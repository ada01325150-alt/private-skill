# wxgzh-search Workflow

Version: `1.0.0`

## Purpose

Provide a WeChat-first operating model that starts from keywords, discovers public article links, harvests content into structured records, and produces a synthesis artifact without bypassing anti-bot controls.

## Phases

### 1. Discovery

Use a keyword source:

- `data/wechat-research/keywords_shortdrama_focus_v1.csv`
- `data/wechat-research/keywords_novel_to_storyboard_top10.csv`

Run either:

- `python3 scripts/wechat_keyword_standard_path.py --keyword "..." --privacy-mode incognito`
- `python3 scripts/wechat_keyword_standard_batch.py --keywords-csv ... --privacy-mode incognito`

### 2. Queue generation

The batch flow writes `keyword,url` records into `data/wechat-research/queue/`.

### 3. Harvesting

Use:

```bash
python3 scripts/wechat_harvest_with_pwcli.py \
  --input data/wechat-research/queue/<queue-file>.csv \
  --out-dir output/wechat-research/<round> \
  --privacy-mode incognito
```

Expected outputs include:

- `articles.jsonl`
- per-article Markdown files
- `errors.jsonl` when failures occur
- blocked records with explicit block reasons

### 4. Synthesis

Run:

```bash
python3 scripts/wechat_dialectic_matrix.py \
  --input output/wechat-research/<round>/articles.jsonl \
  --out-dir output/wechat-research/<round> \
  --wechat-only \
  --min-source-score 55
```

This converts raw harvest output into thesis / antithesis / boundary / action artifacts.

## Anti-bot handling policy

- Default to `incognito` sessions.
- Preserve blocking evidence.
- Retry only through compliant manual verification.
- Prefer direct article reading when URLs are already known.
- Never pretend a blocked page was harvested successfully.

## Recommended operating modes

- Small topic exploration: `run_focus_round.sh`
- Long queue: `run_wechat_research_daemon.sh`
- Known URLs: `wechat_article_reader.py`
