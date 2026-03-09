# WeChat Official Search Focus Test Cases

Version: `1.0.0`

## Test set

1. Read one known public article URL into Markdown and JSONL.
2. Run a one-keyword standard path with `incognito` mode.
3. Run a small batch and verify a queue CSV is produced.
4. Harvest a queue and confirm blocked pages remain explicit in the evidence.
5. Build a dialectic matrix from a harvested `articles.jsonl` file.

## Success criteria

- The skill supports both keyword-first and URL-first entry points.
- Anti-bot states are recorded rather than hidden.
- Scripts resolve correctly from the skill root.
- The workflow preserves primary source URLs and keyword context.

## Failure criteria

- Search is described without a compliant fallback path.
- A blocked page is silently dropped.
- The skill claims private-account or login-only coverage.
