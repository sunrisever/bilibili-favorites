# -*- coding: utf-8 -*-
"""
从 bilibili-follow-classifier 项目导入UP主分类结果

将关注分类的结果转换为 up_classify_map.json，供收藏夹分类算法使用。
UP主映射在算法预分类时作为强信号（+200分），提升分类准确率。

用法:
  python import_up_map.py                           # 自动查找同级目录
  python import_up_map.py <关注分类项目路径>        # 指定路径
  python import_up_map.py --file <分类结果.json>    # 直接指定文件
"""

import json
import sys
from pathlib import Path

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / "data"

# 分类名映射：关注分类项目 → 收藏夹分类项目
# 两个项目的分类名基本一致，如有差异在此添加映射
CATEGORY_MAPPING = {
    "两性情感": "两性认知",
    "数学/物理": "数学/物理/化学",
    "美食/探店": "生活",
}


def find_source_file(arg=None):
    """查找关注分类项目的分类结果文件"""
    # 1. 命令行指定文件
    if arg and Path(arg).is_file():
        return Path(arg)

    # 2. 命令行指定目录
    if arg and Path(arg).is_dir():
        candidate = Path(arg) / "data" / "分类结果.json"
        if candidate.exists():
            return candidate

    # 3. 自动查找同级目录
    search_names = ["bilibili关注分类", "bilibili-follow-classifier"]
    for name in search_names:
        candidate = BASE_PATH.parent / name / "data" / "分类结果.json"
        if candidate.exists():
            return candidate

    return None


def load_follow_results(source_path):
    """加载关注分类结果"""
    with open(source_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "categories" not in data:
        print(f"错误: 文件格式不正确，缺少 categories 字段")
        sys.exit(1)

    return data["categories"]


def load_current_rules():
    """加载当前收藏夹分类的分类体系"""
    rules_path = DATA_PATH / "classify_rules.json"
    if rules_path.exists():
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = json.load(f)
        return set(rules.get("categories", []))
    return set()


def convert_to_map(categories, valid_categories):
    """将关注分类结果转换为扁平的 UP主→分类 映射"""
    up_map = {}
    skipped_cats = set()

    for cat_name, up_list in categories.items():
        # 应用分类名映射
        mapped_name = CATEGORY_MAPPING.get(cat_name, cat_name)

        # 检查分类是否存在于收藏夹分类体系中
        if valid_categories and mapped_name not in valid_categories:
            skipped_cats.add(cat_name)
            continue

        for up in up_list:
            name = up.get("name", "")
            if name:
                up_map[name] = mapped_name

    return up_map, skipped_cats


def main():
    # 解析参数
    source_arg = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--file" and len(sys.argv) > 2:
            source_arg = sys.argv[2]
        else:
            source_arg = sys.argv[1]

    # 查找源文件
    source_path = find_source_file(source_arg)
    if source_path is None:
        print("错误: 未找到关注分类结果文件")
        print()
        print("用法:")
        print("  python import_up_map.py                        # 自动查找同级目录")
        print("  python import_up_map.py <关注分类项目路径>     # 指定项目路径")
        print("  python import_up_map.py --file <分类结果.json> # 指定文件路径")
        print()
        print("自动搜索路径:")
        for name in ["bilibili关注分类", "bilibili-follow-classifier"]:
            print(f"  {BASE_PATH.parent / name / 'data' / '分类结果.json'}")
        sys.exit(1)

    print(f"源文件: {source_path}")

    # 加载数据
    categories = load_follow_results(source_path)
    valid_categories = load_current_rules()

    if valid_categories:
        print(f"当前分类体系: {len(valid_categories)} 个分类")
    else:
        print("提示: 未找到 classify_rules.json，将导入所有分类")

    # 转换
    up_map, skipped_cats = convert_to_map(categories, valid_categories)

    # 检查是否已有映射
    output_path = DATA_PATH / "up_classify_map.json"
    existing_count = 0
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing_count = len(existing)

    # 保存
    DATA_PATH.mkdir(exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(up_map, f, ensure_ascii=False, indent=2)

    # 统计
    print(f"\n导入完成:")
    if existing_count > 0:
        print(f"  覆盖: {existing_count} -> {len(up_map)} 个UP主映射")
    else:
        print(f"  导入: {len(up_map)} 个UP主映射")

    # 按分类统计
    cat_count = {}
    for cat in up_map.values():
        cat_count[cat] = cat_count.get(cat, 0) + 1

    print(f"\n分类分布:")
    for cat, count in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    if skipped_cats:
        print(f"\n跳过的分类（不在当前分类体系中）:")
        for cat in sorted(skipped_cats):
            count = len(categories[cat])
            print(f"  {cat}: {count} 个UP主")
        print("如需导入，请在脚本顶部的 CATEGORY_MAPPING 中添加映射")

    print(f"\n输出: {output_path}")


if __name__ == "__main__":
    main()
