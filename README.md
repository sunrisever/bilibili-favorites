English | [简体中文](README_CN.md)

# Bilibili Favorites

> Export Bilibili favorites, classify them locally, optionally let ChatGPT / Claude / Gemini / Codex review the hard cases, then sync the final folder plan back to Bilibili favorites.

This project is for people whose Bilibili favorites have grown too large to maintain by hand.

Important clarification:

- Bilibili favorites do **not** provide a strong built-in AI classification workflow.
- This repository does **not** require a hard-wired LLM API to be useful.
- The intended workflow is: fetch data locally -> generate rules -> classify -> optionally ask a stronger external model to review -> sync back.

## What this project really is

It is a favorites-management pipeline:

1. Fetch favorites and keep checkpoints.
2. Generate or refine category rules.
3. Classify videos in stages.
4. Export readable summaries for review.
5. Preview sync.
6. Rebuild favorites folders from the final plan.

## Do I need an API key?

No, not for normal usage.

The default path is:

- run the local scripts
- generate the readable files
- ask ChatGPT / Claude / Gemini / Codex / Claude Code / OpenCode to review edge cases
- update local rules
- sync back

API-based automation is optional advanced mode only.

## Beginner quick start

### Step 1. Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2. Prepare config

Copy `data_example/config.json` to `data/config.json`.

### Step 3. Fill in cookies

Provide:

- `sessdata`
- `bili_jct`
- `buvid3`
- `dedeuserid`

### Step 4. Fetch favorites

```bash
python fetch.py all
```

You should see:

- `data/收藏视频数据.json`
- `data/fetch_checkpoint.json`

### Step 5. Generate rules and classify

```bash
python analyze.py
python classify.py
```

You should then see:

- `data/classify_rules.json`
- `data/分类结果.json`
- `data/分类结果.md`

### Step 6. Review and sync

1. Open `data/分类结果.md`
2. Give it to your preferred model
3. Ask for suspicious items, overly broad categories, or suggested manual overrides
4. Update your local rules
5. Preview:

```bash
python sync.py --dry-run
```

6. Sync:

```bash
python sync.py
```

## Screenshot-style beginner walkthrough

### What you touch first

Files:

- `data/config.json`
- `data/classify_rules.json`

### What you run first

```bash
python fetch.py all
```

Think of the first “result screen” as:

- your raw favorites are now stored locally
- the script has not changed your online Bilibili folders yet

### What you run second

```bash
python analyze.py
python classify.py
```

Now you should get:

- a rules file
- a machine-readable classification file
- a Markdown review file

### What you give to AI

Give the AI:

- `data/分类结果.md`

Do **not** start with API integration unless you really want scripting later.

Good questions:

- Which videos are obviously misclassified?
- Which categories should be merged or split?
- Which manual overrides should I add?
- Which rules are too weak?

### What finally changes Bilibili

Only after you dry-run and confirm:

```bash
python sync.py --dry-run
python sync.py
```

## Incremental maintenance

### New favorites

```bash
python add_new.py
python add_new.py --days 30
```

### Recover missing videos

```bash
python recover.py --dry-run
python recover.py
```

### Regenerate readable summaries

```bash
python generate_info.py
```

## Files that matter

| File | Purpose |
| --- | --- |
| `data/config.json` | local cookies and runtime config |
| `data/收藏视频数据.json` | fetched favorites data |
| `data/fetch_checkpoint.json` | resume support |
| `data/classify_rules.json` | long-term rule file |
| `data/up_classify_map.json` | optional prior imported from follow groups |
| `data/分类结果.json` | machine-readable result |
| `data/分类结果.md` | AI-friendly review file |
| `sync.py` | preview or apply sync |

## Common misunderstandings

### “Does Bilibili already have good AI classification here?”

No. This project exists because favorites organization is still weak and manual.

### “Is this repo built around an LLM provider?”

No. It is built around local data, local rules, and optional AI review.

### “Do I need an API to get value?”

No. Subscription tools are the default path.

## License

MIT
