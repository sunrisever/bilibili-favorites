[English](README.md) | 简体中文

# Bilibili Favorites

> 导出 B 站收藏夹，交给 ChatGPT / Claude / Gemini / Codex 等通用大模型辅助分类，再把最终文件夹方案同步回 B 站收藏夹。

这个项目适合收藏夹已经很多、单靠手工整理越来越吃力的人。它的重点不是“仓库里必须绑定某个 AI API 才能用”，而是：

- 先把收藏数据结构化导出来
- 再用你信得过的更强大模型辅助判断
- 规则仍然掌握在你自己手里
- 最后再把最终结构同步回 B 站

## 这个项目本质上是什么

它不是一次性分类脚本，而是一条收藏夹管理流水线：

1. 采集收藏数据并保留断点
2. 生成或调整分类规则
3. 分阶段分类视频
4. 导出可读摘要供 AI 或人工复核
5. 预览同步结果
6. 再把最终文件夹结构写回 B 站

## 要不要 API Key？

对普通小白工作流来说：**不需要**。

最推荐的方式是：

- 先跑本地脚本
- 生成可读结果文件
- 再把这些文件交给 ChatGPT 网页端 / App、Claude 网页端 / App、Gemini、Codex、Claude Code、OpenCode 等工具
- 让 AI 帮你指出模糊项、优化分类体系、建议补人工覆盖
- 最后你再回到本地规则文件里修正并同步

仓库确实可以支持“脚本化接 API 的高级自动化模式”，但那是进阶玩法，不是默认前提。

## 适合谁用

如果你有这些需求，这个项目就很适合：

- 收藏夹视频已经很多
- 想按主题重组，而不是继续扁平堆积
- 希望效果明显强于 B 站默认的手工整理体验
- 想把规则、本地数据、AI 复核和最终结果串成一条长期可维护流程

## 核心思路

- **规则优先，AI 辅助**：AI 用来处理疑难项，规则文件才是长期主线
- **断点友好**：大规模采集支持续跑
- **同步前先预览**：真正破坏性操作永远放最后
- **支持增量维护**：新收藏可以后续补进来，不必每次全部重做

## 小白推荐工作流

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 复制示例配置

```bash
cp data_example/config.json data/config.json
```

如果你在 Windows 上，也可以直接手动复制。

### 3. 填好 B 站 Cookie

编辑 `data/config.json`，填写：

- `sessdata`
- `bili_jct`
- `buvid3`
- `dedeuserid`

这是必须的，因为项目需要读取你的收藏夹，并在最后把结果同步回你的账号。

### 4. 采集收藏数据

```bash
python fetch.py all
python fetch.py resume
python fetch.py stats
```

主要输出：

- `data/收藏视频数据.json`
- `data/fetch_checkpoint.json`

### 5. 生成第一版规则

```bash
python analyze.py
python analyze.py summary
```

主要输出：

- `data/classify_rules.json`

这份规则文件就是你后续长期维护收藏夹分类体系的核心。

### 6. 可选导入 UP 主先验

如果你也在用 [bilibili-follow](https://github.com/sunrisever/bilibili-follow)，可以把关注分组结果导进来，作为收藏分类的重要先验：

```bash
python import_up_map.py
python import_up_map.py "path/to/bilibili-follow-project"
```

主要输出：

- `data/up_classify_map.json`

### 7. 运行分类

```bash
python classify.py
```

如果你想分阶段，也可以：

```bash
python classify.py algo
python classify.py review
```

主要输出：

- `data/分类结果.json`
- `data/分类结果.md`

## 推荐的 AI 复核方式

这一部分正是它比“简单内置 AI 分类”更强的关键。

生成 `data/分类结果.md` 后，你可以直接交给：

- ChatGPT 网页端 / App
- Claude 网页端 / App
- Gemini
- Codex
- Claude Code
- OpenCode
- 其他你认为更强的通用大模型

然后问它：

- 哪些视频明显分错了？
- 哪些分类太宽泛？
- 哪些分类应该拆开？
- 哪些视频应该加入人工覆盖？
- 哪些规则写得太复杂或太弱？

这样你就能享受到强模型的判断力，但**不需要把仓库强绑定到某一个 API 提供商**。

## 预览与同步

一定先预览：

```bash
python sync.py --dry-run
```

确认没问题后再同步：

```bash
python sync.py
```

## 日常增量维护

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

### 重新生成可读摘要

```bash
python generate_info.py
```

## 你真正需要关心的文件

| 文件 | 作用 |
| --- | --- |
| `data/config.json` | 本地 Cookie 和可选的高级运行配置 |
| `data/收藏视频数据.json` | 采集到的收藏数据 |
| `data/fetch_checkpoint.json` | 断点续跑支持 |
| `data/classify_rules.json` | 你的长期分类规则 |
| `data/up_classify_map.json` | 从关注分组导入的先验 |
| `data/分类结果.json` | 机器可读结果 |
| `data/分类结果.md` | 给人看、给 AI 看都很方便的摘要 |
| `sync.py` | 预览或执行收藏夹同步 |

## 为什么它比产品内置的 AI 整理更强

很多产品也会说自己有 AI 分类，但实际往往不够强，原因通常是：

- 可见上下文太浅
- 元数据太少
- 分类逻辑不可解释
- 分类体系很难长期演进
- 分完之后难以持续维护

这个项目的优势在于：

- 你可以导出更丰富的数据
- 你可以自己选择最强的通用大模型
- 你的规则体系始终可编辑
- 你可以把算法处理、AI 复核和人工判断叠在一起
- 以后收藏夹越来越大时，这套工作流还能重复使用

## 风险提醒

- `sync.py` 会重建非默认收藏夹，所以一定先 `--dry-run`
- Cookie 会过期，需要定期更新
- 如果你自己启用了 API 方式的 AI 审核，会消耗模型额度
- 最安全的做法是把同步当成最后一步

## 配套项目

- [bilibili-follow](https://github.com/sunrisever/bilibili-follow)：整理关注 UP 主，并把结果反向喂给收藏夹分类

## AI 编程助手支持

仓库已包含：

- `SKILL.md`
- `AGENTS.md`
- `CLAUDE.md`

所以它天然适合和 Codex、Claude Code、OpenCode、OpenClaw 这类 agent 工作流一起用。

## 开源协议

MIT
