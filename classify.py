# -*- coding: utf-8 -*-
"""
三阶段视频分类：算法预分类 → Claude AI 审核 → 用户交互审核

用法:
  python classify.py             # 完整三阶段分类
  python classify.py algo        # 仅运行算法预分类
  python classify.py ai          # 仅运行AI审核（需先完成算法预分类）
  python classify.py review      # 仅运行人工审核（需先完成AI审核）
"""

import json
import re
import sys
import random
import webbrowser
from pathlib import Path

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / "data"


# ========== 工具函数 ==========

def load_config():
    with open(DATA_PATH / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_videos():
    with open(DATA_PATH / "收藏视频数据.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_rules():
    rules_path = DATA_PATH / "classify_rules.json"
    if not rules_path.exists():
        print(f"错误: 未找到分类规则文件 {rules_path}")
        print("请先运行 analyze.py 生成分类规则，或从 data_example/ 复制模板。")
        sys.exit(1)
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_results():
    """加载已有的分类结果"""
    path = DATA_PATH / "分类结果.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_up_classify_map():
    """加载UP主分类映射"""
    path = DATA_PATH / "up_classify_map.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_results(results):
    with open(DATA_PATH / "分类结果.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


# ========== Stage 1: 算法预分类 ==========

def calculate_scores(video_info, rules, up_map=None):
    """计算每个分类的得分"""
    categories = rules["categories"]
    keyword_rules = {k: [(kw, w) for kw, w in v] for k, v in rules.get("keyword_rules", {}).items()}
    zone_mapping = rules.get("zone_mapping", {})
    manual = rules.get("manual", {})
    if up_map is None:
        up_map = {}

    scores = {cat: 0 for cat in categories}

    # 手动规则优先（按bvid或标题匹配）
    bvid = video_info.get("bvid", "")
    title = video_info.get("title", "")
    if bvid in manual:
        return {cat: (1000 if cat == manual[bvid] else 0) for cat in categories}, "手动指定"
    if title in manual:
        return {cat: (1000 if cat == manual[title] else 0) for cat in categories}, "手动指定"

    # UP主分类映射加分（强信号 +200）
    up_name = video_info.get("owner", {}).get("name", "")
    # 优先检查 manual 中的UP主名（已在上面处理bvid/title），再检查 up_map
    if up_name in manual:
        matched_cat = manual[up_name]
        if matched_cat in scores:
            scores[matched_cat] += 200
    elif up_name in up_map:
        matched_cat = up_map[up_name]
        if matched_cat in scores:
            scores[matched_cat] += 200

    # 收集所有文本用于关键词匹配
    texts = []
    texts.append(title)
    texts.append(video_info.get("desc", "") or "")
    texts.append(up_name)
    combined_text = " ".join(texts).lower()

    # 标签文本（权重更高，单独处理）
    tags = video_info.get("tags", [])
    tags_text = " ".join(tags).lower()

    # 分区
    tname = (video_info.get("tname", "") or "").lower()

    # 关键词评分
    for category, keywords in keyword_rules.items():
        if category not in scores:
            continue
        for keyword, weight in keywords:
            kw_lower = keyword.lower()
            # 标题+描述中的出现次数
            count = len(re.findall(re.escape(kw_lower), combined_text))
            if count > 0:
                scores[category] += weight * min(count, 5)
            # 标签中的匹配（1.5倍权重）
            tag_count = len(re.findall(re.escape(kw_lower), tags_text))
            if tag_count > 0:
                scores[category] += int(weight * 1.5) * min(tag_count, 5)

    # 分区映射加分（tname为空时跳过）
    if tname:
        for category, zones in zone_mapping.items():
            if category not in scores:
                continue
            for zone_kw in zones:
                if zone_kw.lower() in tname or tname in zone_kw.lower():
                    scores[category] += 50

    return scores, None


def classify_video_algo(video_info, rules, up_map=None):
    """算法分类单个视频，返回 (分类, 置信度, 理由)"""
    default_cat = rules.get("default_category", "其他")
    scores, manual_reason = calculate_scores(video_info, rules, up_map)

    if manual_reason:
        best = max(scores, key=scores.get)
        return best, 100.0, manual_reason

    max_score = max(scores.values())
    if max_score == 0:
        return default_cat, 0.0, "无明确特征"

    best_category = max(scores, key=scores.get)

    # 计算置信度 = (最高分 - 次高分) / 最高分 × 100
    sorted_scores = sorted(scores.values(), reverse=True)
    if sorted_scores[0] > 0:
        confidence = (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0] * 100
    else:
        confidence = 0.0

    # 生成理由
    reason_parts = []
    tags = video_info.get("tags", [])[:5]
    if tags:
        reason_parts.append(f"标签: {', '.join(tags)}")
    tname = video_info.get("tname", "")
    if tname:
        reason_parts.append(f"分区: {tname}")
    # 列出得分前3
    top3 = sorted(scores.items(), key=lambda x: -x[1])[:3]
    score_str = ", ".join(f"{k}:{v}" for k, v in top3 if v > 0)
    if score_str:
        reason_parts.append(f"得分: {score_str}")
    reason = "；".join(reason_parts) if reason_parts else "综合评分"

    return best_category, round(confidence, 1), reason


def stage1_algo(videos, rules):
    """Stage 1: 对所有视频进行算法预分类"""
    print("=" * 50)
    print("Stage 1: 算法预分类")
    print("=" * 50)

    up_map = load_up_classify_map()
    if up_map:
        print(f"已加载UP主分类映射: {len(up_map)} 个UP主")

    results = {}
    for v in videos:
        bvid = v["bvid"]
        category, confidence, reason = classify_video_algo(v, rules, up_map)
        results[bvid] = {
            "bvid": bvid,
            "title": v.get("title", ""),
            "category": category,
            "confidence": confidence,
            "reason": reason,
            "stage": "algo",
        }

    # 统计
    cat_count = {}
    conf_high, conf_mid, conf_low = 0, 0, 0
    for r in results.values():
        cat_count[r["category"]] = cat_count.get(r["category"], 0) + 1
        if r["confidence"] > 70:
            conf_high += 1
        elif r["confidence"] >= 40:
            conf_mid += 1
        else:
            conf_low += 1

    print(f"\n分类统计 ({len(results)} 个视频):")
    for cat, count in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    print(f"\n置信度分布:")
    print(f"  高 (>70): {conf_high}")
    print(f"  中 (40-70): {conf_mid}")
    print(f"  低 (<40): {conf_low}")

    return results


# ========== Stage 2: Claude AI 审核 ==========

def select_for_ai_review(results):
    """根据置信度选择需要AI审核的视频"""
    to_review = []
    high_pool = []

    for bvid, r in results.items():
        conf = r["confidence"]
        if conf < 40:
            # 低置信度：全部审核
            to_review.append(bvid)
        elif conf <= 70:
            # 中置信度：审核30%
            if random.random() < 0.3:
                to_review.append(bvid)
        else:
            # 高置信度：抽查5%
            high_pool.append(bvid)

    # 高置信度抽样
    sample_count = max(1, int(len(high_pool) * 0.05))
    if high_pool:
        to_review.extend(random.sample(high_pool, min(sample_count, len(high_pool))))

    return to_review


def build_ai_review_batch(videos_dict, results, bvids, rules):
    """构建AI审核的批次数据"""
    categories = rules["categories"]
    items = []
    for bvid in bvids:
        r = results[bvid]
        v = videos_dict.get(bvid, {})
        items.append({
            "bvid": bvid,
            "title": r["title"],
            "tags": v.get("tags", []),
            "tname": v.get("tname", ""),
            "desc": (v.get("desc", "") or "")[:100],
            "uploader": v.get("owner", {}).get("name", ""),
            "current_category": r["category"],
            "confidence": r["confidence"],
        })
    return items


def call_claude_review(config, items, categories):
    """调用 Claude API 进行批量审核"""
    claude_config = config["claude"]
    client = anthropic.Anthropic(
        api_key=claude_config["api_key"],
        base_url=claude_config.get("base_url", "https://api.anthropic.com"),
    )
    model = claude_config.get("model", "claude-sonnet-4-20250514")

    cats_str = "、".join(categories)
    videos_json = json.dumps(items, ensure_ascii=False, indent=2)

    prompt = f"""你是B站视频分类审核专家。请审核以下视频的分类是否正确。

可用分类: {cats_str}

待审核视频:
{videos_json}

请对每个视频返回JSON数组，每个元素格式：
{{"bvid": "xxx", "category": "最终分类", "changed": true/false, "reason": "简短理由"}}

规则：
1. 如果当前分类合理，设 changed=false，保持原分类
2. 如果分类不合理，设 changed=true，给出正确分类
3. reason 简短说明判断依据
4. 严格输出JSON数组（不要markdown代码块包裹）"""

    response = client.messages.create(
        model=model,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    return json.loads(text)


def stage2_ai_review(videos, results, rules, config):
    """Stage 2: Claude AI 审核"""
    print("\n" + "=" * 50)
    print("Stage 2: Claude AI 审核")
    print("=" * 50)

    # 选择需要审核的视频
    to_review = select_for_ai_review(results)
    print(f"选出 {len(to_review)} 个视频进行AI审核")

    if not to_review:
        print("无需AI审核")
        return results

    # 构建视频字典
    videos_dict = {v["bvid"]: v for v in videos}

    # 分批审核（每批30个）
    batch_size = 30
    changed_count = 0

    for i in range(0, len(to_review), batch_size):
        batch_bvids = to_review[i:i + batch_size]
        batch_items = build_ai_review_batch(videos_dict, results, batch_bvids, rules)

        print(f"\n审核批次 {i // batch_size + 1} ({len(batch_items)} 个视频)...")
        try:
            reviews = call_claude_review(config, batch_items, rules["categories"])
            for review in reviews:
                bvid = review.get("bvid", "")
                if bvid in results and review.get("changed", False):
                    old_cat = results[bvid]["category"]
                    new_cat = review["category"]
                    if new_cat in rules["categories"]:
                        results[bvid]["category"] = new_cat
                        results[bvid]["reason"] = review.get("reason", "AI修正")
                        results[bvid]["stage"] = "ai_review"
                        changed_count += 1
                        print(f"  修改: {results[bvid]['title'][:30]} | {old_cat} → {new_cat}")
        except Exception as e:
            print(f"  审核失败: {e}")
            continue

    print(f"\nAI审核完成，修改了 {changed_count} 个视频的分类")
    return results


# ========== Stage 3: 用户交互审核 ==========

def stage3_manual_review(videos, results, rules):
    """Stage 3: 用户交互审核低置信度视频"""
    print("\n" + "=" * 50)
    print("Stage 3: 用户交互审核")
    print("=" * 50)

    # 筛选置信度<60的视频
    to_review = []
    for bvid, r in results.items():
        if r["confidence"] < 60 and r.get("stage") != "manual":
            to_review.append(bvid)

    if not to_review:
        print("没有需要人工审核的视频")
        return results

    # 按置信度排序（最低的先审核）
    to_review.sort(key=lambda bvid: results[bvid]["confidence"])

    videos_dict = {v["bvid"]: v for v in videos}
    categories = rules["categories"]
    reviewed = 0

    print(f"共 {len(to_review)} 个视频需要审核")
    print("操作: [Enter]确认 / [数字]更改分类 / [s]跳过 / [o]浏览器打开 / [q]退出保存\n")

    for bvid in to_review:
        r = results[bvid]
        v = videos_dict.get(bvid, {})

        print(f"--- [{reviewed + 1}/{len(to_review)}] ---")
        print(f"标题: {r['title']}")
        print(f"UP主: {v.get('owner', {}).get('name', '未知')}")
        print(f"分区: {v.get('tname', '未知')}")
        tags = v.get("tags", [])
        if tags:
            print(f"标签: {', '.join(tags[:8])}")
        desc = (v.get("desc", "") or "")[:100]
        if desc:
            print(f"简介: {desc}")
        print(f"当前分类: {r['category']} (置信度: {r['confidence']}%)")
        print(f"理由: {r['reason']}")

        # 显示分类选项
        print(f"\n可选分类:")
        for idx, cat in enumerate(categories):
            marker = " ←" if cat == r["category"] else ""
            print(f"  [{idx}] {cat}{marker}")

        while True:
            choice = input("\n操作> ").strip()

            if choice == "" or choice.lower() == "y":
                # 确认当前分类
                results[bvid]["stage"] = "manual"
                break
            elif choice.lower() == "s":
                # 跳过
                break
            elif choice.lower() == "o":
                # 浏览器打开
                webbrowser.open(f"https://www.bilibili.com/video/{bvid}")
                continue
            elif choice.lower() == "q":
                # 退出保存
                save_results(results)
                print(f"\n已保存。已审核 {reviewed} 个视频。")
                return results
            elif choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(categories):
                    old = results[bvid]["category"]
                    results[bvid]["category"] = categories[idx]
                    results[bvid]["reason"] = "人工指定"
                    results[bvid]["stage"] = "manual"
                    print(f"  已修改: {old} → {categories[idx]}")
                    break
                else:
                    print("  无效编号，请重试")
            else:
                print("  无效输入")

        reviewed += 1
        print()

    print(f"\n人工审核完成，已审核 {reviewed} 个视频")
    return results


# ========== 主流程 ==========

def run_full(stages=None):
    """运行分类流程"""
    rules = load_rules()
    videos = load_videos()
    config = load_config()

    print(f"已加载: {len(videos)} 个视频, {len(rules['categories'])} 个分类\n")

    if stages is None:
        stages = ["algo", "ai", "review"]

    results = load_results()

    if "algo" in stages:
        results = stage1_algo(videos, rules)
        save_results(results)

    if "ai" in stages:
        if not results:
            results = load_results()
        if not results:
            print("错误: 无预分类结果，请先运行 algo 阶段")
            return
        results = stage2_ai_review(videos, results, rules, config)
        save_results(results)

    if "review" in stages:
        if not results:
            results = load_results()
        if not results:
            print("错误: 无分类结果，请先运行 algo 或 ai 阶段")
            return
        results = stage3_manual_review(videos, results, rules)
        save_results(results)

    # 最终统计
    print("\n" + "=" * 50)
    print("最终分类统计")
    print("=" * 50)
    cat_count = {}
    for r in results.values():
        cat_count[r["category"]] = cat_count.get(r["category"], 0) + 1
    for cat, count in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    print(f"  总计: {len(results)}")

    save_results(results)
    print(f"\n分类结果已保存到: data/分类结果.json")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "algo":
            run_full(stages=["algo"])
        elif cmd == "ai":
            run_full(stages=["ai"])
        elif cmd == "review":
            run_full(stages=["review"])
        else:
            print(f"未知命令: {cmd}")
            print("用法: python classify.py [algo|ai|review]")
    else:
        run_full()
