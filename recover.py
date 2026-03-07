# -*- coding: utf-8 -*-
"""
恢复丢失的收藏视频

根据本地分类结果，找出线上收藏夹中缺失的视频，重新收藏到对应的分类收藏夹中。

用法:
  python recover.py --dry-run   # 预览缺失情况
  python recover.py             # 执行恢复
"""

import json
import asyncio
import sys
from pathlib import Path

from bilibili_api import favorite_list, video, Credential

sys.stdout.reconfigure(errors="replace")

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


def load_classify_results():
    with open(DATA_PATH / "分类结果.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_videos():
    with open(DATA_PATH / "收藏视频数据.json", "r", encoding="utf-8") as f:
        return json.load(f)


async def get_all_online_aids(credential, uid):
    """获取线上所有收藏夹中的有效 aid 集合"""
    result = await favorite_list.get_video_favorite_list(uid=int(uid), credential=credential)
    all_aids = set()
    if not result or "list" not in result:
        return all_aids

    for folder in result["list"]:
        media_id = folder["id"]
        page = 1
        while True:
            try:
                r = await favorite_list.get_video_favorite_list_content(
                    media_id=media_id, page=page, credential=credential
                )
                medias = r.get("medias", None)
                if not medias:
                    break
                for m in medias:
                    all_aids.add(m.get("id", 0))
                if not r.get("has_more", False):
                    break
                page += 1
                await asyncio.sleep(0.3)
            except Exception:
                break
    return all_aids


async def get_existing_folders(credential, uid):
    """获取所有收藏夹 {title: media_id}"""
    result = await favorite_list.get_video_favorite_list(uid=int(uid), credential=credential)
    folders = {}
    default_media_id = None
    if result and "list" in result:
        for i, item in enumerate(result["list"]):
            folders[item["title"]] = item["id"]
            if i == 0:
                default_media_id = item["id"]
    return folders, default_media_id


async def recover(dry_run=False):
    config = load_config()
    credential = get_credential(config)
    uid = config["bilibili"]["dedeuserid"]

    # 加载本地数据
    results = load_classify_results()
    videos = load_videos()
    videos_dict = {v["bvid"]: v for v in videos}

    print("=== 恢复丢失的收藏视频 ===\n")
    print(f"本地分类记录: {len(results)} 个")
    if dry_run:
        print("【预览模式】不会实际执行\n")

    # 获取线上已有的aid
    print("扫描线上收藏夹...")
    online_aids = await get_all_online_aids(credential, uid)
    print(f"线上有效视频: {len(online_aids)} 个\n")

    # 找出缺失的视频
    missing = []  # [(bvid, aid, title, category)]
    for bvid, r in results.items():
        v = videos_dict.get(bvid, {})
        aid = v.get("aid", 0)
        if aid and aid not in online_aids:
            missing.append({
                "bvid": bvid,
                "aid": aid,
                "title": r.get("title", ""),
                "category": r.get("category", "未分类"),
            })

    if not missing:
        print("没有缺失的视频，无需恢复。")
        return

    # 按分类分组
    by_category = {}
    for m in missing:
        cat = m["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(m)

    print(f"缺失视频: {len(missing)} 个，分布在 {len(by_category)} 个分类中：")
    for cat, items in sorted(by_category.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(items)} 个")
    print()

    if dry_run:
        for cat, items in sorted(by_category.items(), key=lambda x: -len(x[1])):
            print(f"[{cat}] ({len(items)}个)")
            for item in items[:3]:
                print(f"  {item['title'][:50]}")
            if len(items) > 3:
                print(f"  ...等{len(items)}个")
        print("\n预览完毕。去掉 --dry-run 执行恢复。")
        return

    # 统一收藏到默认收藏夹，后续由 sync.py 按分类整理
    _, default_media_id = await get_existing_folders(credential, uid)
    if default_media_id is None:
        print("错误: 未找到默认收藏夹")
        return

    print(f"将 {len(missing)} 个视频收藏到默认收藏夹...\n")
    success_count = 0
    fail_count = 0

    for i, item in enumerate(missing):
        try:
            vid = video.Video(aid=item["aid"], credential=credential)
            await vid.set_favorite(add_media_ids=[default_media_id])
            success_count += 1
            if success_count % 10 == 0:
                print(f"  进度: {success_count}/{len(missing)}")
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(2)
        except Exception as e:
            err_msg = str(e)
            if "412" in err_msg:
                print(f"  触发风控(412)，暂停60秒后继续...")
                await asyncio.sleep(60)
                # 重试一次
                try:
                    await vid.set_favorite(add_media_ids=[default_media_id])
                    success_count += 1
                    continue
                except Exception:
                    pass
            fail_count += 1
            print(f"  [FAIL] {item['title'][:30]}: {err_msg[:80]}")

    print(f"\n=== 恢复完成 ===")
    print(f"成功: {success_count}")
    if fail_count > 0:
        print(f"失败: {fail_count} (可能是视频已被UP主删除)")
    print(f"\n下一步: 运行 python sync.py 将所有视频按分类整理到收藏夹")


def main():
    dry_run = "--dry-run" in sys.argv
    asyncio.run(recover(dry_run=dry_run))


if __name__ == "__main__":
    main()
