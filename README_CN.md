[English](README.md) | 简体中文

# Bilibili Favorites

> 导出 B 站收藏夹，先在本地跑规则与分类，再把疑难项交给 ChatGPT / Claude / Gemini / Codex 等强模型辅助复核，最后把最终文件夹方案同步回 B 站。

这个项目适合收藏夹越来越大、已经不想靠纯手工一点点整理的人。

先把原理说清楚：

- B 站收藏夹本身并没有一套强力、成熟、可持续优化的 AI 分类工作流。
- 这个仓库也不是“必须先配某个 LLM API”才能跑。
- 它真正走的是：本地采集 -> 本地规则生成 -> 本地分类 -> 可选外部强模型复核 -> 再同步回 B 站。

## 这个项目本质上是什么

它是一条收藏夹管理流水线，不是一次性脚本。

完整链路是：

1. 采集收藏数据，并保留断点
2. 生成或调整分类规则
3. 分阶段分类视频
4. 导出可读摘要给人或 AI 复核
5. 预览同步结果
6. 再把最终结构写回 B 站收藏夹

## 要不要 API Key？

默认不需要。

推荐给小白的方式是：

- 跑本地脚本
- 生成结果文件
- 把结果交给 ChatGPT 网页端 / App、Claude 网页端 / App、Gemini、Codex、Claude Code、OpenCode
- 让它帮你指出疑难项、建议补人工覆盖、优化分类设计
- 然后你再改本地规则并同步

也就是说，这个项目默认也是“订阅态工具优先”，不是 API-first。

## 零基础最快上手

### Step 1：安装依赖

```bash
pip install -r requirements.txt
```

### Step 2：准备配置

把 `data_example/config.json` 复制成 `data/config.json`。

### Step 3：填 B 站 Cookie

打开 `data/config.json`，填写：

- `sessdata`
- `bili_jct`
- `buvid3`
- `dedeuserid`

### Step 4：采集收藏夹

```bash
python fetch.py all
```

跑完后你应该看到：

- `data/收藏视频数据.json`
- `data/fetch_checkpoint.json`

### Step 5：生成规则并分类

```bash
python analyze.py
python classify.py
```

跑完后你应该看到：

- `data/classify_rules.json`
- `data/分类结果.json`
- `data/分类结果.md`

### Step 6：复核并同步

1. 打开 `data/分类结果.md`
2. 把它交给你喜欢的强模型
3. 问它哪些视频可能分错、哪些分类需要拆分或合并
4. 回来修改本地规则
5. 先预览：

```bash
python sync.py --dry-run
```

6. 没问题后再同步：

```bash
python sync.py
```

## 像看截图一样的使用流程

这一节就是按“你打开什么、运行什么、会出现什么文件”的方式写。

### 第一步，你先看什么文件

主要是这两个：

- `data/config.json`
- `data/classify_rules.json`

### 第二步，你先跑什么

```bash
python fetch.py all
```

这一步结束后，你可以把它理解成“第一张截图里应该看到的是”：

- 本地已经有收藏数据
- 断点文件也生成了
- 但还没有改动线上收藏夹

### 第三步，你再跑什么

```bash
python analyze.py
python classify.py
```

这时你应该得到：

- 规则文件
- 机器可读分类结果
- 给人和 AI 都方便看的 Markdown 摘要

### 第四步，你到底把什么交给 AI

不是整个仓库，也不是 API。  
真正交出去的是：

- `data/分类结果.md`

建议直接问：

- 哪些视频明显分错了？
- 哪些分类太宽？
- 哪些分类应该拆开？
- 哪些视频需要人工覆盖？
- 哪些规则写得太弱？

### 第五步，什么时候才会真正改 B 站

只有这一步：

```bash
python sync.py --dry-run
python sync.py
```

所以前面的采集、规则生成、分类、AI 复核，全都只是本地和离线工作流。

## 可选的增强步骤

### 导入关注分组先验

如果你同时使用 `bilibili-follow`，可以把它的结果导进来：

```bash
python import_up_map.py
python import_up_map.py "path/to/bilibili-follow-project"
```

### 增量处理新收藏

```bash
python add_new.py
python add_new.py --days 30
```

### 恢复缺失视频

```bash
python recover.py --dry-run
python recover.py
```

## 你真正需要关心的文件

| 文件 | 作用 |
| --- | --- |
| `data/config.json` | 本地 Cookie 和运行配置 |
| `data/收藏视频数据.json` | 采集到的收藏数据 |
| `data/fetch_checkpoint.json` | 断点续跑支持 |
| `data/classify_rules.json` | 长期规则文件 |
| `data/up_classify_map.json` | 从关注分组导入的先验 |
| `data/分类结果.json` | 机器可读结果 |
| `data/分类结果.md` | 给人看、给 AI 看都方便的摘要 |
| `sync.py` | 预览或执行同步 |

## 常见误解

### “B 站收藏夹不是已经有 AI 整理了吗？”

不是这个意思。  
这个项目解决的是“平台整理能力弱、人工维护累、长期不可控”的问题。

### “这个项目是不是强绑定某个模型 API？”

不是。  
它的核心仍然是：

- 本地数据
- 本地规则
- 你自己选的外部强模型做复核

### “不用 API 也能用吗？”

完全可以。  
默认就是按订阅态网页端 / App / agent 工具来设计的。

## 开源协议

MIT
