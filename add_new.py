# -*- coding: utf-8 -*-
"""
增量处理新收藏的视频
获取最近N天的新收藏 → 去重 → 采集信息+标签 → 算法分类 → 追加到数据文件

用法:
  python add_new.py            # 处理最近7天的新收藏
  python add_new.py --days 30  # 处理最近30天的新收藏
"""

import json
import asyncio
import sys
import time
from pathlib import Path

from bilibili_api import favorite_list, video, Credential

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / "data"


def load_config():
    with open(DATA_PATH / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_credential(config):
    bili = config["bilibili"]
    return Credential(
        sessdata=bili["sessdata"],
        bili_jct=bili["bili_jct"],
        buvid3=bili["buvid3"],
        dedeuserid=bili["dedeuserid"],
    )


def load_videos():
    path = DATA_PATH / "收藏视频数据.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_videos(videos):
    with open(DATA_PATH / "收藏视频数据.json", "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)


def load_results():
    path = DATA_PATH / "分类结果.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_results(results):
    with open(DATA_PATH / "分类结果.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def load_rules():
    rules_path = DATA_PATH / "classify_rules.json"
    if not rules_path.exists():
        return None
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def get_all_favorite_folders(credential, uid):
    """获取所有收藏夹列表"""
    result = await favorite_list.get_video_favorite_list(uid=int(uid), credential=credential)
    folders = []
    if result and "list" in result:
        for item in result["list"]:
            folders.append({
                "media_id": item["id"],
                "title": item["title"],
                "media_count": item["media_count"],
            })
    return folders


async def get_recent_videos(credential, media_id, days):
    """获取收藏夹中最近N天的视频"""
    cutoff_time = int(time.time()) - days * 86400
    recent = []
    page = 1

    while True:
        try:
            result = await favorite_list.get_video_favorite_list_content(
                media_id=media_id, page=page, credential=credential
            )
            medias = result.get("medias", None)
            if not medias:
                break

            for media in medias:
                fav_time = media.get("fav_time", 0)
                if fav_time >= cutoff_time:
                    recent.append(media)
                else:
                    # 按收藏时间排序，遇到过早的就停止
                    return recent

            has_more = result.get("has_more", False)
            if not has_more:
                break
            page += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  获取第 {page} 页时出错: {e}")
            break

    return recent


async def get_video_tags(credential, bvid):
    """获取视频标签"""
    try:
        vid = video.Video(bvid=bvid, credential=credential)
        tags = await vid.get_tags()
        return [t.get("tag_name", "") for t in tags if t.get("tag_name")]
    except Exception:
        return []


def extract_video_info(raw, folder_info):
    """从API原始数据中提取视频信息"""
    return {
        "aid": raw.get("id", 0),
        "bvid": raw.get("bvid", ""),
        "title": raw.get("title", ""),
        "desc": raw.get("intro", ""),
        "owner": {
            "mid": raw.get("upper", {}).get("mid", 0),
            "name": raw.get("upper", {}).get("name", ""),
        },
        "tname": raw.get("type_name", "") or "",
        "duration": raw.get("duration", 0),
        "pubdate": raw.get("pubtime", 0),
        "fav_time": raw.get("fav_time", 0),
        "tags": [],
        "source_folder": {
            "media_id": folder_info["media_id"],
            "title": folder_info["title"],
        },
        "cnt_info": {
            "play": raw.get("cnt_info", {}).get("play", 0),
            "danmaku": raw.get("cnt_info", {}).get("danmaku", 0),
        },
    }


def classify_video_algo(video_info, rules):
    """简易算法分类（复用classify.py的逻辑）"""
    import re

    categories = rules["categories"]
    keyword_rules = {k: [(kw, w) for kw, w in v] for k, v in rules.get("keyword_rules", {}).items()}
    zone_mapping = rules.get("zone_mapping", {})
    default_cat = rules.get("default_category", "其他")

    scores = {cat: 0 for cat in categories}

    texts = [video_info.get("title", ""), video_info.get("desc", "") or "",
             video_info.get("owner", {}).get("name", "")]
    combined_text = " ".join(texts).lower()
    tags = video_info.get("tags", [])
    tags_text = " ".join(tags).lower()
    tname = (video_info.get("tname", "") or "").lower()

    for category, keywords in keyword_rules.items():
        if category not in scores:
            continue
        for keyword, weight in keywords:
            kw_lower = keyword.lower()
            count = len(re.findall(re.escape(kw_lower), combined_text))
            if count > 0:
                scores[category] += weight * min(count, 5)
            tag_count = len(re.findall(re.escape(kw_lower), tags_text))
            if tag_count > 0:
                scores[category] += int(weight * 1.5) * min(tag_count, 5)

    if tname:
        for category, zones in zone_mapping.items():
            if category not in scores:
                continue
            for zone_kw in zones:
                if zone_kw.lower() in tname or tname in zone_kw.lower():
                    scores[category] += 50

    max_score = max(scores.values())
    if max_score == 0:
        return default_cat, 0.0

    best = max(scores, key=scores.get)
    sorted_scores = sorted(scores.values(), reverse=True)
    confidence = (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0] * 100 if sorted_scores[0] > 0 else 0
    return best, round(confidence, 1)


async def clean_invalid_videos(credential, folders):
    """清理所有收藏夹中的失效视频"""
    print("清理失效视频...")
    cleaned_total = 0
    for folder in folders:
        try:
            result = await favorite_list.clean_video_favorite_list_content(
                media_id=folder["media_id"], credential=credential
            )
            # API 返回清理结果
            if result:
                cleaned_total += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  清理 {folder['title']} 失败: {e}")
    if cleaned_total > 0:
        print(f"  已对 {cleaned_total} 个收藏夹执行清理")
    else:
        print(f"  所有收藏夹均无失效内容")
    print()


async def add_new(days=7):
    config = load_config()
    credential = get_credential(config)
    uid = config["bilibili"]["dedeuserid"]

    # 加载已有数据
    existing_videos = load_videos()
    existing_bvids = {v["bvid"] for v in existing_videos}
    results = load_results()
    rules = load_rules()

    print(f"已有 {len(existing_videos)} 个视频，检查最近 {days} 天的新收藏...\n")

    # 获取所有收藏夹
    folders = await get_all_favorite_folders(credential, uid)
    print(f"共 {len(folders)} 个收藏夹\n")

    # 清理B站收藏夹中的失效视频（不动本地数据）
    await clean_invalid_videos(credential, folders)

    new_videos = []

    for folder in folders:
        print(f"检查: {folder['title']}...")
        recent = await get_recent_videos(credential, folder["media_id"], days)

        for raw in recent:
            bvid = raw.get("bvid", "")
            if not bvid or bvid in existing_bvids:
                continue
            if raw.get("attr", 0) != 0:
                continue

            info = extract_video_info(raw, folder)

            # 获取标签
            tags = await get_video_tags(credential, bvid)
            info["tags"] = tags
            await asyncio.sleep(0.3)

            new_videos.append(info)
            existing_bvids.add(bvid)
            print(f"  新增: {info['title'][:40]}")

        await asyncio.sleep(0.5)

    if not new_videos:
        print(f"\n没有新的收藏视频")
        return

    print(f"\n共发现 {len(new_videos)} 个新视频")

    # 追加到数据
    existing_videos.extend(new_videos)
    save_videos(existing_videos)
    print(f"视频数据已更新 (总计 {len(existing_videos)} 个)")

    # 算法分类
    if rules:
        print(f"\n使用现有规则进行分类...")
        for v in new_videos:
            category, confidence = classify_video_algo(v, rules)
            results[v["bvid"]] = {
                "bvid": v["bvid"],
                "title": v["title"],
                "category": category,
                "confidence": confidence,
                "reason": "增量自动分类",
                "stage": "algo",
            }
            print(f"  {v['title'][:30]} → {category} ({confidence}%)")

        save_results(results)
        print(f"\n分类结果已更新 (总计 {len(results)} 个)")
    else:
        print("\n提示: 未找到分类规则，新视频暂未分类。请先运行 analyze.py 生成规则。")


def main():
    days = 7
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--days" and i + 1 < len(args):
            days = int(args[i + 1])
            i += 2
        else:
            i += 1

    asyncio.run(add_new(days=days))


if __name__ == "__main__":
    main()
