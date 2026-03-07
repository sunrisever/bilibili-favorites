# -*- coding: utf-8 -*-
"""
AI 分析生成分类体系
使用 Claude API 分析收藏视频数据，自动生成 classify_rules.json

用法:
  python analyze.py          # 分析并生成分类规则
  python analyze.py summary  # 仅输出数据摘要（不调用AI）
"""

import json
import sys
from pathlib import Path
from collections import Counter

import anthropic

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / "data"

# 参考分类（来自关注分类项目，作为AI生成分类时的参考）
REFERENCE_CATEGORIES = [
    "考研", "AI学术/论文", "AI产品/开源/新闻", "AI网课/教程",
    "编程/计算机", "数学/物理", "数码/科技/汽车", "电气/电子/自动化",
    "时政/地缘政治", "财经/金融", "科普/人文", "形象提升/医美",
    "两性情感", "户外探索", "美食/探店", "音乐/乐器",
    "影视/动漫", "医学/健康", "校园生活/校园日常", "美女/颜值", "生活"
]


def load_config():
    with open(DATA_PATH / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_videos():
    path = DATA_PATH / "收藏视频数据.json"
    if not path.exists():
        print("错误: 未找到视频数据文件，请先运行 fetch.py all")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_data_summary(videos):
    """聚合统计：标签Top50、分区分布、UP主Top20、每分区采样标题"""

    # 标签统计
    tag_counter = Counter()
    for v in videos:
        for tag in v.get("tags", []):
            tag_counter[tag] += 1
    top_tags = tag_counter.most_common(50)

    # 分区分布
    zone_counter = Counter()
    zone_samples = {}  # 每个分区采样标题
    for v in videos:
        tname = v.get("tname", "") or "未知"
        zone_counter[tname] += 1
        if tname not in zone_samples:
            zone_samples[tname] = []
        if len(zone_samples[tname]) < 5:
            zone_samples[tname].append(v.get("title", ""))

    # UP主统计
    up_counter = Counter()
    for v in videos:
        name = v.get("owner", {}).get("name", "未知")
        up_counter[name] += 1
    top_ups = up_counter.most_common(20)

    # 收藏夹分布
    folder_counter = Counter()
    for v in videos:
        folder = v.get("source_folder", {}).get("title", "未知")
        folder_counter[folder] += 1

    summary = {
        "total_videos": len(videos),
        "top_tags": top_tags,
        "zone_distribution": zone_counter.most_common(),
        "zone_samples": zone_samples,
        "top_uploaders": top_ups,
        "folder_distribution": folder_counter.most_common(),
    }
    return summary


def format_summary_text(summary):
    """格式化摘要为可读文本"""
    lines = []
    lines.append(f"=== 收藏视频数据摘要 ===\n")
    lines.append(f"总视频数: {summary['total_videos']}\n")

    lines.append("--- 热门标签 Top50 ---")
    for tag, count in summary["top_tags"]:
        lines.append(f"  {tag}: {count}")

    lines.append("\n--- 分区分布 ---")
    for zone, count in summary["zone_distribution"]:
        lines.append(f"  {zone}: {count}")

    lines.append("\n--- 分区视频采样 ---")
    for zone, titles in summary["zone_samples"].items():
        lines.append(f"  [{zone}]")
        for t in titles:
            lines.append(f"    - {t}")

    lines.append("\n--- UP主 Top20 ---")
    for name, count in summary["top_uploaders"]:
        lines.append(f"  {name}: {count}")

    lines.append("\n--- 收藏夹分布 ---")
    for folder, count in summary["folder_distribution"]:
        lines.append(f"  {folder}: {count}")

    return "\n".join(lines)


def call_claude_api(config, summary_text):
    """调用 Claude API 生成分类体系"""
    claude_config = config["claude"]
    client = anthropic.Anthropic(
        api_key=claude_config["api_key"],
        base_url=claude_config.get("base_url", "https://api.anthropic.com"),
    )
    model = claude_config.get("model", "claude-sonnet-4-20250514")

    ref_cats = "、".join(REFERENCE_CATEGORIES)

    prompt = f"""你是一个B站视频分类专家。我需要你根据以下收藏视频数据统计，为我生成一套合适的分类体系。

## 我之前对关注UP主的分类体系（仅供参考，视频分类可能需要调整）
{ref_cats}

## 我的收藏视频数据统计
{summary_text}

## 要求
1. 根据数据实际分布设计 8-20 个分类，分类名简短（2-6字）
2. 可以参考我之前的UP主分类，但应根据视频数据的实际情况调整（增删改）
3. 每个分类需要配套：简短描述、关键词及权重、对应的B站分区
4. 关键词权重范围 5-20，越相关越高
5. 必须有一个"其他"分类作为兜底
6. 确保所有常见视频类型都能被覆盖

## 输出格式
请严格输出JSON格式（不要markdown代码块包裹），结构如下：
{{
  "categories": ["分类1", "分类2", ...],
  "category_descriptions": {{"分类1": "描述", ...}},
  "default_category": "其他",
  "manual": {{}},
  "keyword_rules": {{"分类1": [["关键词", 权重], ...], ...}},
  "zone_mapping": {{"分类1": ["分区1", "分区2"], ...}}
}}"""

    print(f"正在调用 {model} 生成分类体系...")
    response = client.messages.create(
        model=model,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    # 提取响应文本
    text = response.content[0].text.strip()

    # 尝试清理可能的markdown包裹
    if text.startswith("```"):
        lines = text.split("\n")
        # 去掉首尾的```行
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    return text


def main(summary_only=False):
    videos = load_videos()
    print(f"已加载 {len(videos)} 个视频\n")

    summary = build_data_summary(videos)
    summary_text = format_summary_text(summary)

    if summary_only:
        print(summary_text)
        return

    config = load_config()

    # 调用 Claude API
    result_text = call_claude_api(config, summary_text)

    # 解析JSON
    try:
        rules = json.loads(result_text)
    except json.JSONDecodeError as e:
        print(f"AI返回的JSON解析失败: {e}")
        print(f"原始输出:\n{result_text}")
        # 保存原始输出供手动修复
        with open(DATA_PATH / "ai_raw_output.txt", "w", encoding="utf-8") as f:
            f.write(result_text)
        print(f"已保存原始输出到 data/ai_raw_output.txt，请手动修复后保存为 classify_rules.json")
        return

    # 验证必要字段
    required = ["categories", "category_descriptions", "default_category", "keyword_rules", "zone_mapping"]
    for field in required:
        if field not in rules:
            print(f"警告: 缺少字段 '{field}'")

    # 确保有 manual 字段
    rules.setdefault("manual", {})

    # 保存
    rules_path = DATA_PATH / "classify_rules.json"
    with open(rules_path, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)

    print(f"\n分类体系已生成并保存到: {rules_path}")
    print(f"\n分类列表 ({len(rules['categories'])} 个):")
    for cat in rules["categories"]:
        desc = rules.get("category_descriptions", {}).get(cat, "")
        kw_count = len(rules.get("keyword_rules", {}).get(cat, []))
        print(f"  {cat}: {desc} ({kw_count}个关键词)")

    print(f"\n提示: 你可以手动编辑 {rules_path} 来微调分类规则。")


if __name__ == "__main__":
    summary_only = len(sys.argv) > 1 and sys.argv[1] == "summary"
    main(summary_only=summary_only)
