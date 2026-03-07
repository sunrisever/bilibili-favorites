# -*- coding: utf-8 -*-
"""
B站收藏夹视频数据采集模块
支持：全量采集 / 断点续传 / 统计信息

用法:
  python fetch.py all       # 全量采集所有收藏夹视频
  python fetch.py resume    # 断点续传
  python fetch.py stats     # 查看已采集数据统计
"""

import json
import asyncio
import sys
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
    """加载已采集的视频数据"""
    path = DATA_PATH / "收藏视频数据.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_videos(videos):
    """保存视频数据"""
    with open(DATA_PATH / "收藏视频数据.json", "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)


def load_checkpoint():
    """加载断点信息"""
    path = DATA_PATH / "fetch_checkpoint.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed_bvids": [], "current_folder_index": 0, "current_page": 1, "done": False}


def save_checkpoint(checkpoint):
    """保存断点信息"""
    with open(DATA_PATH / "fetch_checkpoint.json", "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


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


async def get_folder_videos(credential, media_id):
    """分页获取某个收藏夹的所有视频"""
    all_videos = []
    page = 1
    while True:
        try:
            result = await favorite_list.get_video_favorite_list_content(
                media_id=media_id, page=page, credential=credential
            )
            medias = result.get("medias", None)
            if not medias:
                break
            all_videos.extend(medias)
            # 检查是否还有下一页
            has_more = result.get("has_more", False)
            if not has_more:
                break
            page += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  获取第 {page} 页时出错: {e}")
            break
    return all_videos


async def get_video_tags(credential, bvid):
    """获取单个视频的标签"""
    try:
        vid = video.Video(bvid=bvid, credential=credential)
        tags = await vid.get_tags()
        return [t.get("tag_name", "") for t in tags if t.get("tag_name")]
    except Exception:
        return []


def extract_video_info(raw, folder_info):
    """从API原始数据中提取需要的视频信息"""
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
        "tags": [],  # 后续填充
        "source_folder": {
            "media_id": folder_info["media_id"],
            "title": folder_info["title"],
        },
        "cnt_info": {
            "play": raw.get("cnt_info", {}).get("play", 0),
            "danmaku": raw.get("cnt_info", {}).get("danmaku", 0),
        },
    }


async def fetch_all(resume=False):
    """全量采集所有收藏夹视频数据"""
    config = load_config()
    credential = get_credential(config)
    uid = config["bilibili"]["dedeuserid"]

    # 加载断点
    if resume:
        checkpoint = load_checkpoint()
        if checkpoint.get("done"):
            print("上次采集已完成，无需续传。如需重新采集请使用 all 命令。")
            return
        videos = load_videos()
        processed_bvids = set(checkpoint["processed_bvids"])
        start_folder = checkpoint["current_folder_index"]
        print(f"断点续传：已有 {len(videos)} 个视频，从第 {start_folder + 1} 个收藏夹继续...")
    else:
        checkpoint = {"processed_bvids": [], "current_folder_index": 0, "current_page": 1, "done": False}
        videos = []
        processed_bvids = set()
        start_folder = 0

    # 获取收藏夹列表
    print("正在获取收藏夹列表...")
    folders = await get_all_favorite_folders(credential, uid)
    if not folders:
        print("未获取到收藏夹列表")
        return

    total_count = sum(f["media_count"] for f in folders)
    print(f"共 {len(folders)} 个收藏夹，约 {total_count} 个视频\n")

    video_count = 0
    tag_count = 0

    for folder_idx in range(start_folder, len(folders)):
        folder = folders[folder_idx]
        print(f"[{folder_idx + 1}/{len(folders)}] {folder['title']} ({folder['media_count']}个视频)")

        # 获取该收藏夹所有视频
        raw_videos = await get_folder_videos(credential, folder["media_id"])
        print(f"  实际获取 {len(raw_videos)} 个视频")

        for raw in raw_videos:
            bvid = raw.get("bvid", "")
            if not bvid or bvid in processed_bvids:
                continue

            # 跳过失效视频
            if raw.get("attr", 0) != 0:
                print(f"  跳过失效视频: {raw.get('title', '未知')}")
                continue

            info = extract_video_info(raw, folder)

            # 获取标签
            tags = await get_video_tags(credential, bvid)
            info["tags"] = tags
            tag_count += 1
            await asyncio.sleep(0.3)

            videos.append(info)
            processed_bvids.add(bvid)
            video_count += 1

            # 每50个视频暂停并保存
            if video_count % 50 == 0:
                print(f"  已处理 {video_count} 个新视频（共 {len(videos)} 个），暂停2秒...")
                checkpoint["processed_bvids"] = list(processed_bvids)
                checkpoint["current_folder_index"] = folder_idx
                save_videos(videos)
                save_checkpoint(checkpoint)
                await asyncio.sleep(2)
            elif video_count % 10 == 0:
                print(f"  已处理 {video_count} 个新视频...")

        # 每个收藏夹处理完后保存
        checkpoint["processed_bvids"] = list(processed_bvids)
        checkpoint["current_folder_index"] = folder_idx + 1
        save_videos(videos)
        save_checkpoint(checkpoint)
        await asyncio.sleep(0.5)

    # 标记完成
    checkpoint["done"] = True
    save_checkpoint(checkpoint)
    save_videos(videos)

    print(f"\n采集完成！")
    print(f"  总视频数: {len(videos)}")
    print(f"  本次新增: {video_count}")
    print(f"  标签请求: {tag_count}")


def show_stats():
    """显示已采集数据的统计信息"""
    videos = load_videos()
    if not videos:
        print("暂无数据，请先运行 fetch.py all 采集数据。")
        return

    print(f"=== 收藏视频数据统计 ===\n")
    print(f"总视频数: {len(videos)}")

    # 收藏夹分布
    folder_count = {}
    for v in videos:
        folder = v.get("source_folder", {}).get("title", "未知")
        folder_count[folder] = folder_count.get(folder, 0) + 1
    print(f"\n收藏夹分布 ({len(folder_count)} 个收藏夹):")
    for folder, count in sorted(folder_count.items(), key=lambda x: -x[1]):
        print(f"  {folder}: {count}")

    # 分区分布
    zone_count = {}
    for v in videos:
        tname = v.get("tname", "") or "未知"
        zone_count[tname] = zone_count.get(tname, 0) + 1
    print(f"\n分区分布 (Top 20):")
    for zone, count in sorted(zone_count.items(), key=lambda x: -x[1])[:20]:
        print(f"  {zone}: {count}")

    # 标签统计
    tag_count = {}
    for v in videos:
        for tag in v.get("tags", []):
            tag_count[tag] = tag_count.get(tag, 0) + 1
    print(f"\n热门标签 (Top 30):")
    for tag, count in sorted(tag_count.items(), key=lambda x: -x[1])[:30]:
        print(f"  {tag}: {count}")

    # UP主统计
    up_count = {}
    for v in videos:
        name = v.get("owner", {}).get("name", "未知")
        up_count[name] = up_count.get(name, 0) + 1
    print(f"\nUP主统计 (Top 20):")
    for name, count in sorted(up_count.items(), key=lambda x: -x[1])[:20]:
        print(f"  {name}: {count}")

    # 有标签的视频比例
    with_tags = sum(1 for v in videos if v.get("tags"))
    print(f"\n标签覆盖: {with_tags}/{len(videos)} ({with_tags * 100 // len(videos)}%)")

    # 断点状态
    checkpoint = load_checkpoint()
    if checkpoint.get("done"):
        print("\n采集状态: 已完成")
    else:
        print(f"\n采集状态: 未完成 (已处理 {len(checkpoint.get('processed_bvids', []))} 个)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "all":
            asyncio.run(fetch_all(resume=False))
        elif cmd == "resume":
            asyncio.run(fetch_all(resume=True))
        elif cmd == "stats":
            show_stats()
        else:
            print("未知命令:", cmd)
            print("用法: python fetch.py [all|resume|stats]")
    else:
        print("用法:")
        print("  python fetch.py all       # 全量采集所有收藏夹视频")
        print("  python fetch.py resume    # 断点续传")
        print("  python fetch.py stats     # 查看已采集数据统计")
