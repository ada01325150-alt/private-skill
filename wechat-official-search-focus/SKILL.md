---
name: wechat-official-search-focus
description: Use when a task needs WeChat official account article discovery from keywords, compliant harvesting of public article content, focus-account expansion, direct URL fallback reading, and synthesis into a research-ready evidence packet.
version: "1.0.0"
---

# WeChat Official Search Focus

Version: `1.0.0`

## Overview

This skill packages a WeChat-first research workflow in English. It combines local keyword-search and focus-expansion scripts with the local WeChat article reader so the agent can search for public article evidence, harvest content compliantly, preserve block states, and synthesize findings into a focused output set.

## Use this skill when

- You start from keywords rather than article URLs.
- You need to search for public `mp.weixin.qq.com` articles and collect evidence in batches.
- You want a keyword -> queue -> harvest -> synthesis workflow.
- You need a direct-URL fallback for known article links.
- You need anti-bot aware handling with evidence preservation instead of stealth bypass.

## Do not use this skill when

- The task requires bypassing captchas, login walls, or anti-bot systems.
- The source is private, paywalled, or user credentials are required.
- The user did not approve searching public WeChat content.

## Core capabilities

### 1. Keyword discovery

Use the standard-path scripts to turn a keyword list into candidate article links:

- `scripts/wechat_keyword_standard_path.py`
- `scripts/wechat_keyword_standard_batch.py`
- `scripts/generate_wechat_queue_from_keywords.py`

### 2. Batch harvesting

Use the queue-based harvester to open public links, extract content, and mark blocked items explicitly:

- `scripts/wechat_harvest_with_pwcli.py`
- `scripts/run_wechat_research_daemon.sh`
- `scripts/stop_wechat_research_daemon.sh`

### 3. Direct URL fallback

If article URLs are already known, skip search and normalize them directly:

- `scripts/wechat_article_reader.py`
- `scripts/wechat_article_digest.py`

### 4. Focus synthesis

After harvesting, convert the corpus into a sharper evidence packet:

- `scripts/wechat_dialectic_matrix.py`
- `scripts/wechat_progress_report.py`
- `scripts/wechat_build_index.py`

## Quick start

### A. Single known article

```bash
python3 scripts/wechat_article_reader.py \
  --url "https://mp.weixin.qq.com/s/..." \
  --out-dir ./output/wechat-reading
```

### B. Focused keyword round

```bash
bash scripts/run_focus_round.sh \
  --keywords-csv data/wechat-research/keywords_shortdrama_focus_v1.csv \
  --privacy-mode incognito \
  --top-links-per-keyword 20
```

### C. Continuous queue harvesting

```bash
bash scripts/run_wechat_research_daemon.sh
```

## Workflow decision tree

### Direct URLs are already known

- Use `wechat_article_reader.py`.
- Optionally build a digest with `wechat_article_digest.py`.

### Keywords are known, URLs are not

- Use `run_focus_round.sh` for a complete batch.
- Or call `wechat_keyword_standard_batch.py` manually for finer control.

### The session hits blocking or verification

- Keep `privacy_mode=incognito` unless a normal session is required.
- Preserve the blocked record and reason.
- Do not bypass the challenge.
- Retry only after compliant manual verification.

## Guardrails

- Public WeChat articles only.
- No covert captcha solving or login bypass.
- Keep `blocked=true` / `block_reason` evidence when a harvest attempt is stopped.
- Preserve source URL, keyword, title, account name, and publish time when available.
- Clearly separate source facts from synthesized conclusions.

## Resources

- `references/workflow-v1.0.0.md`: operating notes and orchestration map.
- `references/test-cases-v1.0.0.md`: test prompts and quality gates.
- `data/wechat-research/`: starter keywords and focus accounts.
- `scripts/run_focus_round.sh`: one-shot keyword -> harvest -> synthesis wrapper.
