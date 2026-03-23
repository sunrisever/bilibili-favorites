English | [简体中文](README_CN.md)

# Bilibili Favorites

> Export your Bilibili favorites, let ChatGPT / Claude / Gemini / Codex or any frontier LLM help with classification, then sync the final folder plan back to Bilibili favorites.

This project is for people whose Bilibili favorites have become too large and too messy to manage by hand. The point is not that the repo must have its own hard-wired AI API. The real workflow is:

- fetch and structure your favorites data
- generate or refine categories locally
- let a stronger general-purpose AI model review edge cases if you want
- sync the final folder structure back to Bilibili

## What this project actually is

It is a favorites-management pipeline, not just a one-shot classifier.

The full idea is:

1. Fetch your favorites and keep local checkpoints.
2. Generate or refine folder rules.
3. Classify videos in stages.
4. Export readable summaries for AI review or human review.
5. Preview the sync.
6. Rebuild your Bilibili favorites folders from the final structured result.

## Do I need an API key?

For the normal beginner workflow: **no**.

The easiest and most practical way is:

- run the local scripts
- export the readable result files
- open them in ChatGPT, Claude, Gemini, Codex, Claude Code, OpenCode, or another frontier LLM tool
- ask the model to review ambiguous items, improve category design, or suggest manual overrides
- update the local rule files and sync back to Bilibili

The repository can support API-based automation for advanced users, but that is optional. A beginner does not need to prepare an LLM API key just to get value from the project.

## Who this is for

This project is helpful if you:

- have a large Bilibili favorites library
- want folders by topic instead of a chaotic flat structure
- want a workflow stronger than Bilibili's built-in manual organization
- want to combine local rules, AI review, and final human control

## Core ideas

- **Rule-first, AI-assisted**: AI helps the difficult cases; your rule files remain the long-term source of truth.
- **Checkpoint-friendly**: large fetches can resume instead of restarting.
- **Review before sync**: destructive sync comes last, not first.
- **Incremental maintenance**: new favorites can be processed later without rebuilding everything.

## Beginner workflow

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Copy the example config

```bash
cp data_example/config.json data/config.json
```

If you are on Windows, you can also copy the file manually.

### 3. Fill in your Bilibili cookies

Edit `data/config.json` and provide:

- `sessdata`
- `bili_jct`
- `buvid3`
- `dedeuserid`

These are required because the project reads your own favorites and later syncs the folder result back.

### 4. Fetch your favorites

```bash
python fetch.py all
python fetch.py resume
python fetch.py stats
```

Main outputs:

- `data/收藏视频数据.json`
- `data/fetch_checkpoint.json`

### 5. Generate the first rule set

```bash
python analyze.py
python analyze.py summary
```

Main output:

- `data/classify_rules.json`

This rule file is yours. You can keep refining it over time.

### 6. Optionally import UP-master priors

If you also use [bilibili-follow](https://github.com/sunrisever/bilibili-follow), you can import follow-group knowledge into favorites classification:

```bash
python import_up_map.py
python import_up_map.py "path/to/bilibili-follow-project"
```

Main output:

- `data/up_classify_map.json`

### 7. Run the classifier

```bash
python classify.py
```

You can also run staged modes if needed:

```bash
python classify.py algo
python classify.py review
```

Main outputs:

- `data/分类结果.json`
- `data/分类结果.md`

## Recommended AI-assisted review loop

This is the part that makes the project much stronger than simple built-in categorization.

After you generate `data/分类结果.md`, you can send it to:

- ChatGPT web/app
- Claude web/app
- Gemini
- Codex
- Claude Code
- OpenCode
- any other strong general-purpose LLM

And ask questions such as:

- which videos seem obviously misclassified?
- which categories are too broad?
- which categories should be split?
- what manual overrides should I add?
- which rules should be simplified?

This gives you the benefits of strong frontier models **without forcing you to hard-code an API provider into the repo**.

## Preview and sync

Always preview first:

```bash
python sync.py --dry-run
```

Then sync:

```bash
python sync.py
```

## Incremental maintenance

### Process newly favorited videos

```bash
python add_new.py
python add_new.py --days 30
```

### Recover missing videos

```bash
python recover.py --dry-run
python recover.py
```

### Generate readable summaries again

```bash
python generate_info.py
```

## Files you should know

| File | Purpose |
| --- | --- |
| `data/config.json` | local cookies and optional advanced runtime config |
| `data/收藏视频数据.json` | fetched favorites data |
| `data/fetch_checkpoint.json` | resume support for large fetches |
| `data/classify_rules.json` | your long-term category rules |
| `data/up_classify_map.json` | optional prior imported from follow groups |
| `data/分类结果.json` | machine-readable result |
| `data/分类结果.md` | AI-friendly and human-friendly review file |
| `sync.py` | preview or apply favorites-folder sync |

## Why this is stronger than basic in-product AI organization

Many products say they have AI categorization, but in practice they often feel weak because:

- context is too shallow
- metadata is too limited
- the model cannot see your whole taxonomy
- the logic is hard to inspect
- the result is hard to improve over time

This project is stronger because it lets you:

- export richer data
- use whichever frontier model you trust most
- keep category rules editable
- combine algorithmic processing, AI review, and human judgment
- reuse the workflow every time your library grows again

## Safety notes

- `sync.py` rebuilds non-default favorites folders, so always use `--dry-run` first.
- Cookies expire and need refresh.
- API-based AI review, if enabled by you, will consume model quota.
- This workflow is safest when sync is treated as the final step.

## Companion project

- [bilibili-follow](https://github.com/sunrisever/bilibili-follow): classify followed UP masters and feed that signal back into favorites organization

## AI coding assistant support

This repo includes:

- `SKILL.md`
- `AGENTS.md`
- `CLAUDE.md`

So it works well with Codex, Claude Code, OpenCode, OpenClaw, and other agent-based workflows.

## License

MIT
