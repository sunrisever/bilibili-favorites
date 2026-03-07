# -*- coding: utf-8 -*-
"""
将分类结果同步到B站收藏夹
策略：删除所有非默认收藏夹 → 按分类创建新收藏夹 → 批量移动视频

用法:
  python sync.py              # 执行同步
  python sync.py --dry-run    # 预览模式，不实际执行
"""

import json
import asyncio
import sys
from pathlib import Path

from bilibili_api import favorite_list, Credential

# Windows终端GBK编码无法显示emoji等特殊字符，用?替代避免崩溃
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


def load_folder_descriptions():
    """加载收藏夹简介"""
    path = DATA_PATH / "folder_descriptions.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_videos():
    with open(DATA_PATH / "收藏视频数据.json", "r", encoding="utf-8") as f:
        return json.load(f)


async def get_existing_folders(credential, uid):
    """获取当前所有收藏夹，返回 (default_folder, other_folders_dict)"""
    result = await favorite_list.get_video_favorite_list(uid=int(uid), credential=credential)
    default_folder = None
    others = {}
    if result and "list" in result:
        for i, item in enumerate(result["list"]):
            info = {
                "media_id": item["id"],
                "title": item["title"],
                "media_count": item["media_count"],
            }
            if i == 0:
                # B站API返回的第一个收藏夹始终是系统默认收藏夹（不可删除）
                default_folder = info
            else:
                others[item["title"]] = info
    return default_folder, others


async def get_all_valid_aids(credential, folders):
    """遍历所有收藏夹，收集当前有效的 aid 集合"""
    valid_aids = set()
    for folder in folders:
        media_id = folder["media_id"]
        page = 1
        while True:
            try:
                result = await favorite_list.get_video_favorite_list_content(
                    media_id=media_id, page=page, credential=credential
                )
                medias = result.get("medias", None)
                if not medias:
                    break
                for m in medias:
                    # attr == 0 表示有效视频
                    if m.get("attr", 0) == 0:
                        valid_aids.add(m.get("id", 0))
                if not result.get("has_more", False):
                    break
                page += 1
                await asyncio.sleep(0.3)
            except Exception:
                break
    return valid_aids


async def sync(dry_run=False):
    config = load_config()
    credential = get_credential(config)
    uid = config["bilibili"]["dedeuserid"]

    # 加载分类结果和收藏夹简介
    results = load_classify_results()
    videos = load_videos()
    descriptions = load_folder_descriptions()
    videos_dict = {v["bvid"]: v for v in videos}

    # 按分类组织视频
    category_videos = {}  # {分类名: [aid, ...]}
    for bvid, r in results.items():
        cat = r["category"]
        v = videos_dict.get(bvid, {})
        aid = v.get("aid", 0)
        if aid:
            if cat not in category_videos:
                category_videos[cat] = []
            fav_time = v.get("fav_time", 0)
            category_videos[cat].append({"aid": aid, "bvid": bvid, "title": r.get("title", ""), "fav_time": fav_time})

    total_videos = sum(len(v) for v in category_videos.values())
    print("=== B站收藏夹同步 ===")
    print(f"共 {len(category_videos)} 个分类，{total_videos} 个视频")
    if dry_run:
        print("【预览模式】不会实际执行任何操作")
    print()

    # 1. 获取已有收藏夹
    print("第1步：获取已有收藏夹...")
    default_folder, other_folders = await get_existing_folders(credential, uid)
    if default_folder:
        print(f"  默认收藏夹: {default_folder['title']} ({default_folder['media_count']}个视频)")
    print(f"  其他收藏夹: {len(other_folders)} 个")
    for name, info in other_folders.items():
        print(f"    {name} ({info['media_count']}个视频)")
    print()

    if default_folder is None:
        print("错误: 未找到默认收藏夹，中止操作")
        return

    source_media_id = default_folder["media_id"]

    print(f"将同步全部 {total_videos} 个视频\n")

    # 2. 把所有非默认收藏夹的视频移回默认收藏夹
    to_delete = other_folders
    if to_delete:
        print(f"第2步：归集视频到默认收藏夹，然后删除旧收藏夹...")
        batch_size = 20
        for name, info in to_delete.items():
            if info["media_count"] == 0:
                continue
            # 获取该收藏夹所有有效视频的aid
            folder_aids = []
            page = 1
            while True:
                try:
                    result = await favorite_list.get_video_favorite_list_content(
                        media_id=info["media_id"], page=page, credential=credential
                    )
                    medias = result.get("medias", None)
                    if not medias:
                        break
                    for m in medias:
                        if m.get("attr", 0) == 0:
                            folder_aids.append(m.get("id", 0))
                    if not result.get("has_more", False):
                        break
                    page += 1
                    await asyncio.sleep(0.3)
                except Exception:
                    break

            if folder_aids:
                if not dry_run:
                    # 分批移动到默认收藏夹
                    for i in range(0, len(folder_aids), batch_size):
                        batch = folder_aids[i:i + batch_size]
                        try:
                            await favorite_list.move_video_favorite_list_content(
                                media_id_from=info["media_id"],
                                media_id_to=source_media_id,
                                aids=batch,
                                credential=credential,
                            )
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f"  [FAIL] {name} 归集失败: {e}")
                    print(f"  [OK] {name}: {len(folder_aids)}个视频 → 默认收藏夹")
                else:
                    print(f"  [预览] {name}: {len(folder_aids)}个视频 → 默认收藏夹")

        # 删除已清空的非默认收藏夹
        if not dry_run:
            await asyncio.sleep(1)
            media_ids = [info["media_id"] for info in to_delete.values()]
            try:
                await favorite_list.delete_video_favorite_list(media_ids, credential)
                print(f"  [OK] 已删除 {len(to_delete)} 个旧收藏夹")
            except Exception as e:
                print(f"  批量删除失败: {e}")
                for del_name, del_info in to_delete.items():
                    try:
                        await favorite_list.delete_video_favorite_list([del_info["media_id"]], credential)
                        await asyncio.sleep(0.5)
                    except Exception as e2:
                        print(f"  [FAIL] 删除 {del_name}: {e2}")
        else:
            print(f"  [预览] 归集完成后将删除 {len(to_delete)} 个旧收藏夹")
    else:
        print("第2步：没有需要处理的旧收藏夹")
    print()

    # 3. 创建新收藏夹（B站显示顺序：后创建的在前）
    #    目标显示：AI新闻、数学、编程、考研、AI网课 在前，其余按数量，音乐最后
    #    创建顺序需反过来
    def folder_order(c):
        # 返回值越小越先创建（显示越靠后）
        if c == "音乐/乐器":
            return (0, 0)  # 最先创建 -> 显示最后
        elif c == "AI产品/开源/新闻":
            return (5, 0)  # 最后创建 -> 显示最前
        elif c == "数学/物理/化学":
            return (4, 0)  # 显示第二
        elif c == "编程/计算机":
            return (3, 0)  # 显示第三
        elif c == "考研":
            return (2, 1)  # 显示第四
        elif c == "AI网课/教程":
            return (2, 0)  # 显示第五
        else:
            return (1, len(category_videos[c]))  # 按数量从少到多
    sorted_cats = sorted(category_videos.keys(), key=folder_order)
    print(f"第3步：创建 {len(category_videos)} 个分类收藏夹...")
    folder_map = {}  # {分类名: media_id}

    if not dry_run:
        for cat_name in sorted_cats:
            try:
                result = await favorite_list.create_video_favorite_list(
                    title=cat_name,
                    introduction=descriptions.get(cat_name, ""),
                    credential=credential,
                )
                media_id = result.get("id")
                if media_id:
                    folder_map[cat_name] = media_id
                    print(f"  [OK] 创建: {cat_name} (media_id={media_id})")
                else:
                    print(f"  [FAIL] 创建失败: {cat_name} - 未返回id: {result}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  [FAIL] 创建失败: {cat_name} - {e}")
    else:
        for cat_name in sorted_cats:
            print(f"  [预览] 将创建: {cat_name} ({len(category_videos[cat_name])}个视频)")
            folder_map[cat_name] = -1
    print()

    # 4. 按收藏时间顺序逐个移动视频到对应收藏夹
    #    fav_time升序移动：最早收藏的先移，最近收藏的后移
    #    这样B站收藏夹中最新收藏的排在最前，恢复原始时间顺序
    print("第4步：按收藏时间顺序移动视频到对应收藏夹...\n")
    success_count = 0
    fail_count = 0

    # 汇总所有视频并按fav_time升序排列
    all_moves = []
    for cat_name, video_list in category_videos.items():
        target_media_id = folder_map.get(cat_name)
        if target_media_id is None:
            print(f"跳过 {cat_name}: 收藏夹不存在")
            continue
        print(f"[{cat_name}] {len(video_list)} 个视频 → media_id={target_media_id}")
        for v in video_list:
            all_moves.append({**v, "cat": cat_name, "target": target_media_id})

    all_moves.sort(key=lambda x: x["fav_time"])
    print(f"\n共 {len(all_moves)} 个视频，按收藏时间顺序逐个移动...\n")

    if dry_run:
        from datetime import datetime
        print(f"  最早: {datetime.fromtimestamp(all_moves[0]['fav_time']).strftime('%Y-%m-%d')} {all_moves[0]['title'][:20]}")
        print(f"  最晚: {datetime.fromtimestamp(all_moves[-1]['fav_time']).strftime('%Y-%m-%d')} {all_moves[-1]['title'][:20]}")
    else:
        for i, item in enumerate(all_moves):
            try:
                await favorite_list.move_video_favorite_list_content(
                    media_id_from=source_media_id,
                    media_id_to=item["target"],
                    aids=[item["aid"]],
                    credential=credential,
                )
                success_count += 1
                if success_count % 50 == 0:
                    print(f"  进度: {success_count}/{len(all_moves)}")
                    await asyncio.sleep(3)
                else:
                    await asyncio.sleep(1)
            except Exception as e:
                fail_count += 1
                err = str(e)
                if "412" in err:
                    print(f"  触发风控(412)，暂停60秒... ({success_count}/{len(all_moves)})")
                    await asyncio.sleep(60)
                    try:
                        await favorite_list.move_video_favorite_list_content(
                            media_id_from=source_media_id,
                            media_id_to=item["target"],
                            aids=[item["aid"]],
                            credential=credential,
                        )
                        success_count += 1
                        fail_count -= 1
                    except Exception:
                        print(f"  [FAIL] {item['title'][:30]}: 重试失败")
                else:
                    print(f"  [FAIL] {item['title'][:30]}: {err[:60]}")

    # 5. 总结
    print(f"\n=== 同步完成 ===")
    if not dry_run:
        print(f"成功: {success_count} 个视频")
        if fail_count > 0:
            print(f"失败: {fail_count} 个视频")
    else:
        print("预览完毕，未执行任何实际操作")
        print("去掉 --dry-run 参数以实际执行")


def main():
    dry_run = "--dry-run" in sys.argv
    asyncio.run(sync(dry_run=dry_run))


if __name__ == "__main__":
    main()
