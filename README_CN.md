[English](README.md) | 简体中文

# B站收藏夹分类器

> AI-assisted Bilibili favorites classifier and folder sync | AI 辅助的 B站收藏夹分类与同步工具

这个项目用来把凌乱的 B 站收藏夹重组为一个可维护的分类系统。它把数据采集、规则生成、算法预分类、AI 审核、人工复核和最终同步串成一条完整流程，适合长期维护大量收藏视频。

> 配套项目：[bilibili-follow-classifier](https://github.com/sunrisever/bilibili-follow-classifier)。你可以把关注 UP 主的分类结果导入进来，作为收藏视频分类的重要先验信号。

## 这个项目解决什么问题

收藏视频一多，默认收藏夹通常会出现这些问题：

- 新视频不断堆到不合适的位置
- 分类体系随着兴趣变化逐渐失真
- 手工整理成本越来越高

这个仓库的目标，就是把整理收藏夹变成一条可重复执行的流程：采集数据、生成规则、处理低置信度样本、最后再同步回 B 站。

## 核心特点

- 支持全量采集收藏数据，并可断点续传
- 基于你自己的数据统计生成分类规则
- 三阶段分类：算法预分类 -> AI 审核 -> 人工审核
- 可选导入 `bilibili-follow-classifier` 的 UP 主分类结果
- 支持只处理新收藏的视频
- 提供缺失视频恢复流程
- 内置 `SKILL.md`、`AGENTS.md`、`CLAUDE.md`，适合 Claude Code、Codex、OpenCode、OpenClaw 等 AI 编程助手

## 快速入口

- [SKILL.md](SKILL.md)
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)

## 使用流程总览

1. 复制示例配置到本地 `data/`
2. 填好 B 站 Cookie 和模型 API 凭证
3. 用 `python fetch.py all` 采集收藏数据
4. 用 `python analyze.py` 生成分类规则
5. 用 `python classify.py` 跑完整分类流程
6. 复核低置信度样本
7. 用 `python sync.py --dry-run` 预览同步
8. 确认无误后再执行 `python sync.py`

## 安装

```bash
pip install -r requirements.txt
```

## 配置

先从示例配置生成本地配置：

```bash
cp data_example/config.json data/config.json
```

然后编辑 `data/config.json`：

```json
{
  "bilibili": {
    "sessdata": "你的SESSDATA",
    "bili_jct": "你的bili_jct",
    "buvid3": "你的buvid3",
    "dedeuserid": "你的UID"
  },
  "claude": {
    "api_key": "你的Claude API Key",
    "model": "claude-sonnet-4-20250514",
    "base_url": "https://api.anthropic.com"
  }
}
```

## 主流程

### 1. 采集收藏数据

```bash
python fetch.py all
python fetch.py resume
python fetch.py stats
```

### 2. 生成分类规则

```bash
python analyze.py
python analyze.py summary
```

生成后的规则文件保存在 `data/classify_rules.json`。

### 3. 导入 UP 主分类

```bash
python import_up_map.py
python import_up_map.py <project_path>
python import_up_map.py --file <result.json>
```

这样可以把“某个 UP 主通常属于哪个方向”的先验引入收藏分类中。

### 4. 运行三阶段分类

```bash
python classify.py
python classify.py algo
python classify.py ai
python classify.py review
```

人工审核快捷键：

- `Enter`：接受当前分类
- `数字`：改成对应分类
- `s`：跳过
- `o`：浏览器打开视频
- `q`：退出并保存

### 5. 预览并同步到 B 站

```bash
python sync.py --dry-run
python sync.py
```

## 增量与恢复工具

### 处理新收藏

```bash
python add_new.py
python add_new.py --days 30
```

### 恢复缺失视频

```bash
python recover.py --dry-run
python recover.py
```

### 生成可读摘要

```bash
python generate_info.py
```

## 项目结构

```text
├── fetch.py
├── analyze.py
├── classify.py
├── sync.py
├── add_new.py
├── recover.py
├── import_up_map.py
├── generate_info.py
├── SKILL.md
├── AGENTS.md
├── CLAUDE.md
├── RELEASE_CHECKLIST.md
├── data_example/
└── data/
```

## 隐私与安全

- `data/` 中包含 Cookie、采集数据和分类结果，应保持本地存放
- 仓库已按隐私型规则配置，避免提交本地敏感数据
- 所有破坏性同步操作都应先 `--dry-run`

## 风险提醒

- `sync.py` 会重建非默认收藏夹
- AI 审核和规则生成会消耗模型额度
- Cookie 会过期，需要定期更新
- 最安全的用法是把“同步”当最后一步，而不是最开始就执行

## 相关项目

- [bilibili-follow-classifier](https://github.com/sunrisever/bilibili-follow-classifier)：用于整理关注 UP 主，并把结果复用到这里

## 开源协议

MIT
