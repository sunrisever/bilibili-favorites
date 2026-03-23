English | [简体中文](README_CN.md)

# Bilibili Favorites

> AI-assisted Bilibili favorites organizer and folder sync

This project helps you rebuild a messy Bilibili favorites library into a maintainable folder system. It combines data collection, AI-assisted rule generation, algorithm pre-classification, AI review, manual review, and final sync back to Bilibili favorites folders.

> Companion project: [bilibili-follow](https://github.com/sunrisever/bilibili-follow). Import followed UP master categories as a strong signal to improve favorites classification.

## Why this project

Once you have accumulated a large number of favorites, the default Bilibili folder structure becomes hard to maintain:

- new videos keep piling into the wrong places
- folders drift away from your actual interests
- manual cleanup becomes too slow

This repo turns that into a repeatable workflow: collect data, generate rules, review uncertain items, and rebuild folders from a structured result.

## Highlights

- Full favorites fetch with checkpoint resume
- AI-assisted rule generation from your own data statistics
- 3-stage pipeline: algorithm -> AI review -> manual review
- Optional UP master mapping imported from `bilibili-follow`
- Incremental processing for new favorites only
- Recovery flow for missing favorites
- AI coding assistant support via `SKILL.md`, `AGENTS.md`, and `CLAUDE.md`

## Quick Links

- [SKILL.md](SKILL.md)
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)

## Workflow at a glance

1. Copy example config into your local `data/`
2. Fill in Bilibili cookies and LLM credentials
3. Fetch all favorites with `python fetch.py all`
4. Generate rules with `python analyze.py`
5. Run `python classify.py`
6. Review low-confidence cases
7. Preview sync with `python sync.py --dry-run`
8. Rebuild Bilibili favorites folders with `python sync.py`

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create your local config from the example:

```bash
cp data_example/config.json data/config.json
```

Then edit `data/config.json`:

```json
{
  "bilibili": {
    "sessdata": "YOUR_SESSDATA",
    "bili_jct": "YOUR_bili_jct",
    "buvid3": "YOUR_buvid3",
    "dedeuserid": "YOUR_UID"
  },
  "claude": {
    "api_key": "YOUR_CLAUDE_API_KEY",
    "model": "claude-sonnet-4-20250514",
    "base_url": "https://api.anthropic.com"
  }
}
```

## Main pipeline

### 1. Fetch favorites data

```bash
python fetch.py all
python fetch.py resume
python fetch.py stats
```

### 2. Generate classification rules

```bash
python analyze.py
python analyze.py summary
```

The generated rule file is saved to `data/classify_rules.json`.

### 3. Import UP master categories

```bash
python import_up_map.py
python import_up_map.py <project_path>
python import_up_map.py --file <result.json>
```

This adds a strong prior from your follow classifier.

### 4. Run the 3-stage classifier

```bash
python classify.py
python classify.py algo
python classify.py ai
python classify.py review
```

Manual review controls:

- `Enter`: accept current category
- `number`: reassign
- `s`: skip
- `o`: open video in browser
- `q`: quit and save

### 5. Preview and sync to Bilibili

```bash
python sync.py --dry-run
python sync.py
```

## Incremental and recovery tools

### Process new favorites

```bash
python add_new.py
python add_new.py --days 30
```

### Recover missing videos

```bash
python recover.py --dry-run
python recover.py
```

### Generate readable summaries

```bash
python generate_info.py
```

## Project structure

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

## Privacy and safety

- `data/` contains cookies, fetched metadata, and personal classification results and should remain local
- The repo is configured to avoid committing local/private data
- Always preview destructive sync operations with `--dry-run`

## Important cautions

- `sync.py` rebuilds non-default Bilibili favorites folders
- AI review and rule generation consume model quota
- Cookies expire and need periodic refresh
- This workflow is safest when you treat sync as the last step, not the first

## Related projects

- [bilibili-follow](https://github.com/sunrisever/bilibili-follow): classify followed UP masters and reuse the result here

## License

MIT
