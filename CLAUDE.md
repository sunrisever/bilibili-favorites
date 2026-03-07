> This file is for AI coding assistants (Claude Code, Codex, OpenCode, OpenClaw, etc.). It is optional and can be safely deleted.

# bilibili-favorites-classifier

Bilibili favorites AI classifier with 3-stage pipeline: algorithm pre-classification → AI review → manual review, then sync to Bilibili favorites folders.

## Key Commands

```bash
python fetch.py all              # Fetch all favorites video data
python fetch.py resume           # Resume interrupted fetch
python analyze.py                # AI generates classification rules
python classify.py               # Full 3-stage classification
python classify.py algo          # Algorithm pre-classification only
python classify.py ai            # AI review only
python classify.py review        # Manual review only
python sync.py --dry-run         # Preview sync operations
python sync.py                   # Sync to Bilibili (destructive rebuild)
python add_new.py                # Process new favorites (last 7 days)
python recover.py --dry-run      # Preview missing videos
python import_up_map.py          # Import UP mapping from follow-classifier
python generate_info.py          # Generate summaries
```

## Architecture

- `fetch.py`: Async data collection with checkpoint resume (0.3s/video rate limit)
- `analyze.py`: Claude API generates classification rules from data statistics (tag TOP50, zone distribution, UP TOP20)
- `classify.py`: 3-stage pipeline with confidence scoring
  - Stage 1 (Algorithm): manual rules(+1000) > UP mapping(+200) > keywords(weight*count) > tags(weight*1.5) > zone(+50)
  - Stage 2 (AI): Low confidence(<40) all reviewed, medium(40-70) 30% sampled, high(>70) 5% sampled
  - Stage 3 (Manual): Interactive review for confidence < 60
- `sync.py`: Destructive rebuild of all favorites folders, preserving bookmark timestamps
- `import_up_map.py`: Import UP→category mapping from bilibili-follow-classifier (+200 weight)
- `data_example/`: Config and rule templates
- `data/`: Personal data directory (gitignored)

## Important Notes

- `sync.py` **DESTROYS and rebuilds** all favorites folders. Always use `--dry-run` first.
- Cookie expires periodically, update `data/config.json` when API returns 401.
- AI review in `classify.py` consumes Claude API quota (batches of 30 videos per call).
- Works with bilibili-follow-classifier for UP→category cross-referencing.
