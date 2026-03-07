# -*- coding: utf-8 -*-
"""
生成可读摘要文件
- 视频信息汇总.txt：完整的视频信息列表
- 分类结果.md：按分类分组的 Markdown 格式结果

用法:
  python generate_info.py
"""

import json
import time
from pathlib import Path

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / "data"


def load_videos():
    with open(DATA_PATH / "收藏视频数据.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_results():
    path = DATA_PATH / "分类结果.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def format_duration(seconds):
    """格式化时长"""
    if not seconds:
        return "未知"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_timestamp(ts):
    """格式化时间戳"""
    if not ts:
        return "未知"
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def format_count(n):
    """格式化播放量"""
    if not n:
        return "0"
    if n >= 10000:
        return f"{n / 10000:.1f}万"
    return str(n)


def generate_txt(videos, results):
    """生成视频信息汇总.txt"""
    lines = []
    lines.append("=" * 60)
    lines.append("B站收藏视频信息汇总")
    lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"总视频数: {len(videos)}")
    lines.append("=" * 60)
    lines.append("")

    for v in videos:
        bvid = v.get("bvid", "")
        r = results.get(bvid, {})
        category = r.get("category", "未分类")
        confidence = r.get("confidence", 0)

        lines.append(f"标题: {v.get('title', '')}")
        lines.append(f"BV号: {bvid}")
        lines.append(f"链接: https://www.bilibili.com/video/{bvid}")
        lines.append(f"UP主: {v.get('owner', {}).get('name', '未知')} (mid: {v.get('owner', {}).get('mid', '')})")
        lines.append(f"分区: {v.get('tname', '未知')}")
        lines.append(f"时长: {format_duration(v.get('duration'))}")
        lines.append(f"发布: {format_timestamp(v.get('pubdate'))}")
        lines.append(f"收藏: {format_timestamp(v.get('fav_time'))}")
        lines.append(f"播放: {format_count(v.get('cnt_info', {}).get('play', 0))} | 弹幕: {format_count(v.get('cnt_info', {}).get('danmaku', 0))}")
        tags = v.get("tags", [])
        if tags:
            lines.append(f"标签: {', '.join(tags)}")
        desc = (v.get("desc", "") or "").strip()
        if desc:
            lines.append(f"简介: {desc[:200]}")
        lines.append(f"来源收藏夹: {v.get('source_folder', {}).get('title', '未知')}")
        lines.append(f"分类: {category} (置信度: {confidence}%)")
        lines.append("-" * 40)
        lines.append("")

    output_path = DATA_PATH / "视频信息汇总.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


def generate_md(videos, results):
    """生成分类结果.md"""
    videos_dict = {v["bvid"]: v for v in videos}

    # 按分类组织
    categories = {}
    for bvid, r in results.items():
        cat = r.get("category", "未分类")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({"bvid": bvid, **r})

    # 按数量排序
    sorted_cats = sorted(categories.items(), key=lambda x: -len(x[1]))

    total = sum(len(v) for v in categories.values())
    lines = []
    lines.append("# B站收藏视频分类结果\n")
    lines.append(f"总计: {total} 个视频，{len(categories)} 个分类\n")
    lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("---\n")

    for cat, items in sorted_cats:
        lines.append(f"## {cat} ({len(items)}个)\n")

        # 按收藏时间排序
        items.sort(key=lambda x: videos_dict.get(x["bvid"], {}).get("fav_time", 0), reverse=True)

        for item in items:
            bvid = item["bvid"]
            title = item.get("title", "未知")
            v = videos_dict.get(bvid, {})
            up_name = v.get("owner", {}).get("name", "")
            duration = format_duration(v.get("duration"))
            play = format_count(v.get("cnt_info", {}).get("play", 0))

            lines.append(f"- [{title}](https://www.bilibili.com/video/{bvid}) - {up_name} | {duration} | {play}播放")

        lines.append("")

    output_path = DATA_PATH / "分类结果.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


def main():
    videos = load_videos()
    results = load_results()
    print(f"已加载 {len(videos)} 个视频, {len(results)} 个分类结果\n")

    txt_path = generate_txt(videos, results)
    print(f"[OK] 视频信息汇总: {txt_path}")

    md_path = generate_md(videos, results)
    print(f"[OK] 分类结果文档: {md_path}")

    # 简要统计
    cat_count = {}
    for r in results.values():
        cat = r.get("category", "未分类")
        cat_count[cat] = cat_count.get(cat, 0) + 1

    print(f"\n分类统计:")
    for cat, count in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
