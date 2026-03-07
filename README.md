English | [简体中文](README_CN.md)

# Bilibili Favorites Classifier

AI-powered 3-stage classifier for Bilibili favorites (bookmarked videos). Uses Claude API to generate classification rules, then applies algorithm pre-classification → AI review → manual review pipeline, and syncs results to Bilibili favorites folders.

> Companion project: [bilibili-follow-classifier](https://github.com/sunrisever/bilibili-follow-classifier) — classifies followed UP masters. Import its results to boost favorites classification accuracy.

## Features

- **Data Collection**: Async fetch of all favorites with checkpoint resume
- **AI Rule Generation**: Claude API analyzes your data statistics to generate classification rules
- **3-Stage Classification**: Algorithm → AI review (low-confidence items) → Manual review
- **UP Master Mapping**: Import classification from bilibili-follow-classifier as a strong signal (+200 weight)
- **Folder Descriptions**: Auto-set Bilibili favorites folder descriptions
- **Sync to Bilibili**: Rebuild favorites folders from classification results
- **Incremental Updates**: Process only newly bookmarked videos
- **Summary Export**: Generate readable video info and classification documents
- **AI coding assistant support**: includes `CLAUDE.md` and `AGENTS.md` for Claude Code, Codex, OpenCode, and OpenClaw

## Setup

```bash
pip install -r requirements.txt
```

### Configuration

1. Copy example config:
```bash
cp data_example/config.json data/config.json
```

2. Edit `data/config.json`:

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

Get Bilibili cookies: Log in → F12 → Application → Cookies.

## Workflow

### 1. Fetch Data

```bash
python fetch.py all       # Full fetch of all favorites
python fetch.py resume    # Resume after interruption
python fetch.py stats     # View collection statistics
```

### 2. Generate Classification Rules

```bash
python analyze.py          # AI generates rules from data statistics
python analyze.py summary  # View data summary only (no API call)
```

Rules are saved to `data/classify_rules.json`. Fine-tune manually as needed.

### 3. Import UP Master Classification (Optional)

If you've used [bilibili-follow-classifier](https://github.com/sunrisever/bilibili-follow-classifier):

```bash
python import_up_map.py                     # Auto-find sibling project
python import_up_map.py <project_path>      # Specify path
python import_up_map.py --file <result.json> # Specify file directly
```

This creates `data/up_classify_map.json`, giving UP master mapping +200 weight in classification.

### 4. Classify Videos

```bash
python classify.py         # Full 3-stage pipeline
python classify.py algo    # Algorithm only
python classify.py ai      # AI review only
python classify.py review  # Manual review only
```

Manual review controls: `Enter` confirm | `number` reassign | `s` skip | `o` open in browser | `q` quit & save

### 5. Sync to Bilibili

```bash
python sync.py --dry-run   # Preview operations
python sync.py             # Execute (rebuilds all favorites folders)
```

**Warning**: `sync.py` deletes all non-default favorites folders and rebuilds them. Always `--dry-run` first.

### 6. Incremental Updates

```bash
python add_new.py            # Process last 7 days
python add_new.py --days 30  # Process last 30 days
```

### 7. Recovery

```bash
python recover.py --dry-run  # Preview missing videos
python recover.py            # Re-bookmark missing videos
```

## Project Structure

```
├── fetch.py              # Data collection (checkpoint resume)
├── analyze.py            # AI rule generation
├── classify.py           # 3-stage classification
├── sync.py               # Sync to Bilibili favorites (destructive rebuild)
├── recover.py            # Recover missing videos
├── import_up_map.py      # Import UP classification from follow-classifier
├── add_new.py            # Incremental processing
├── generate_info.py      # Generate readable summaries
├── requirements.txt
├── data/                 # Personal data (gitignored)
└── data_example/         # Config templates
```

## Notes

- `data/` contains personal data and is gitignored
- `sync.py` is **destructive** — always preview with `--dry-run`
- Cookies expire periodically; update when API returns errors
- AI review in `classify.py` and `analyze.py` consumes Claude API quota
- Works with [bilibili-follow-classifier](https://github.com/sunrisever/bilibili-follow-classifier): one for follows, one for favorites

## License

MIT
