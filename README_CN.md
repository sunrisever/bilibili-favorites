[English](README.md) | 简体中文

# Bilibili 收藏夹分类助手

自动对B站收藏夹中的视频进行分类管理。使用 Claude API 生成分类体系并辅助审核，支持算法预分类 + AI审核 + 人工审核的三阶段分类流程。

> 灵感来源：[bilibili-follow-classifier](https://github.com/sunrisever/bilibili-follow-classifier) — B站关注UP主分类工具。本项目借鉴了其分类体系设计，并支持导入UP主分类结果作为收藏夹分类的辅助信号，提升分类准确率。

## 功能

- **数据采集**：自动获取所有收藏夹的视频信息（含标签），支持断点续传
- **AI分类体系**：基于收藏数据统计，由 Claude 自动生成合适的分类规则
- **三阶段分类**：算法预分类 → AI审核低置信度结果 → 人工审核兜底
- **UP主映射**：支持导入关注分类结果（`up_classify_map.json`），利用UP主已有分类提升准确率
- **收藏夹简介**：创建收藏夹时自动设置描述文字
- **同步到B站**：将分类结果同步为B站收藏夹（清空重建模式）
- **增量处理**：支持仅处理新收藏的视频
- **摘要生成**：输出可读的视频信息汇总和分类结果文档
- **AI 编程助手支持**：内置 `CLAUDE.md` 和 `AGENTS.md`，兼容 Claude Code、Codex、OpenCode、OpenClaw

## 环境准备

```bash
pip install -r requirements.txt
```

## 配置

1. 复制示例配置：
```bash
cp data_example/config.json data/config.json
```

2. 编辑 `data/config.json`，填入你的凭证：

```json
{
  "bilibili": {
    "sessdata": "从浏览器Cookie获取",
    "bili_jct": "从浏览器Cookie获取",
    "buvid3": "从浏览器Cookie获取",
    "dedeuserid": "你的B站UID"
  },
  "claude": {
    "api_key": "你的Claude API Key",
    "model": "claude-sonnet-4-20250514",
    "base_url": "https://api.anthropic.com"
  }
}
```

**获取B站Cookie**：浏览器登录B站 → F12开发者工具 → Application → Cookies → 找到对应字段。

## 使用流程

### 1. 采集数据

```bash
python fetch.py all       # 全量采集所有收藏夹视频
python fetch.py resume    # 断点续传（中断后继续）
python fetch.py stats     # 查看已采集数据统计
```

### 2. 生成分类规则

```bash
python analyze.py          # AI分析数据并生成分类体系
python analyze.py summary  # 仅查看数据摘要（不调用AI）
```

生成的规则保存在 `data/classify_rules.json`，可手动微调。

### 3. 导入UP主分类（可选）

如果你使用过 [bilibili-follow-classifier](https://github.com/sunrisever/bilibili-follow-classifier) 对关注的UP主进行了分类，可以一键导入：

```bash
python import_up_map.py                        # 自动查找同级目录的关注分类项目
python import_up_map.py <关注分类项目路径>     # 指定项目路径
python import_up_map.py --file <分类结果.json> # 直接指定文件
```

导入后生成 `data/up_classify_map.json`，算法预分类时UP主映射会作为强信号（+200分），显著提升该UP主视频的分类准确率。

### 4. 分类视频

```bash
python classify.py         # 完整三阶段分类
python classify.py algo    # 仅算法预分类
python classify.py ai      # 仅AI审核
python classify.py review  # 仅人工审核
```

人工审核时的操作：
- `Enter` - 确认当前分类
- `数字` - 更改为指定分类
- `s` - 跳过
- `o` - 浏览器打开视频
- `q` - 退出并保存

### 5. 编辑收藏夹简介（可选）

编辑 `data/folder_descriptions.json`，为每个分类设置收藏夹简介：

```json
{
  "编程/计算机": "数据结构与算法、操作系统、计算机网络、编程语言教程",
  "音乐/乐器": "钢琴演奏、吉他指弹、声乐教学、翻唱与乐理知识"
}
```

同步时会自动将简介写入B站收藏夹的描述字段。参考模板见 `data_example/folder_descriptions.json`。

### 6. 同步到B站

```bash
python sync.py --dry-run   # 预览将要执行的操作
python sync.py             # 实际同步（会重建收藏夹）
```

**特性**：
- 按收藏时间顺序逐个移动视频，恢复原始时间结构（最近收藏的排在最前）
- 支持自定义收藏夹显示顺序（在 sync.py 的 `folder_order` 函数中调整）
- 同步前会先将旧收藏夹视频归集到默认收藏夹，确保不丢失视频

**注意**：同步操作会删除所有非默认收藏夹并重新创建，请先使用 `--dry-run` 预览。

### 6.1 恢复丢失的视频（可选）

```bash
python recover.py --dry-run   # 预览缺失的视频
python recover.py             # 将缺失视频重新收藏到默认收藏夹
```

### 7. 增量更新

```bash
python add_new.py            # 处理最近7天的新收藏
python add_new.py --days 30  # 处理最近30天的新收藏
```

### 8. 生成摘要

```bash
python generate_info.py    # 生成视频信息汇总和分类结果文档
```

## 项目结构

```
├── fetch.py                  # 数据采集（断点续传）
├── analyze.py                # AI生成分类体系
├── classify.py               # 三阶段分类
├── sync.py                   # 同步到B站收藏夹（按收藏时间排序）
├── recover.py                # 恢复丢失的视频
├── import_up_map.py          # 导入UP主分类（从关注分类项目）
├── add_new.py                # 增量处理
├── generate_info.py          # 生成可读摘要
├── requirements.txt
├── data/                     # 个人数据（gitignored）
│   ├── config.json
│   ├── classify_rules.json
│   ├── folder_descriptions.json
│   ├── up_classify_map.json
│   ├── 收藏视频数据.json
│   ├── fetch_checkpoint.json
│   ├── 分类结果.json
│   ├── 分类结果.md
│   └── 视频信息汇总.txt
└── data_example/             # 示例模板
    ├── config.json
    ├── classify_rules.json
    └── folder_descriptions.json
```

## 注意事项

- `data/` 目录包含个人隐私数据，不会上传
- sync.py 会**删除并重建**所有收藏夹，务必先 `--dry-run`
- Cookie 过期后所有 API 操作失败，需重新获取
- analyze.py 和 classify.py 的 AI 审核会消耗 Claude API 额度
- 与 [bilibili-follow-classifier](https://github.com/sunrisever/bilibili-follow-classifier) 互补：一个管关注UP主分组，一个管收藏视频分类

## 开源协议

MIT
