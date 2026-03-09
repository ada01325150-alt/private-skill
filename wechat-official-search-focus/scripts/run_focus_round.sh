#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEYWORDS_CSV="$ROOT_DIR/data/wechat-research/keywords_shortdrama_focus_v1.csv"
PRIVACY_MODE="incognito"
TOP_LINKS_PER_KEYWORD=20
PICK_RANK=1
MIN_SOURCE_SCORE=55
OUT_ROOT="$ROOT_DIR/output/wechat-research"
PWCLI=""
FOCUS_ONLY=1

usage() {
  cat <<USAGE
Usage: bash scripts/run_focus_round.sh [options]

Options:
  --keywords-csv PATH         keyword CSV file
  --privacy-mode MODE         incognito|normal (default: incognito)
  --top-links-per-keyword N   default: 20
  --pick-rank N               default: 1
  --min-source-score N        default: 55
  --out-root PATH             default: ./output/wechat-research
  --pwcli PATH                optional playwright wrapper path
  --focus-only 0|1            default: 1
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keywords-csv) KEYWORDS_CSV="$2"; shift 2 ;;
    --privacy-mode) PRIVACY_MODE="$2"; shift 2 ;;
    --top-links-per-keyword) TOP_LINKS_PER_KEYWORD="$2"; shift 2 ;;
    --pick-rank) PICK_RANK="$2"; shift 2 ;;
    --min-source-score) MIN_SOURCE_SCORE="$2"; shift 2 ;;
    --out-root) OUT_ROOT="$2"; shift 2 ;;
    --pwcli) PWCLI="$2"; shift 2 ;;
    --focus-only) FOCUS_ONLY="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

mkdir -p "$OUT_ROOT" "$ROOT_DIR/data/wechat-research/queue"

echo "[wechat-official-search-focus] version=1.0.0"
echo "[1/3] discovery and queue generation"

BATCH_CMD=(python3 "$ROOT_DIR/scripts/wechat_keyword_standard_batch.py"
  --keywords-csv "$KEYWORDS_CSV"
  --pick-rank "$PICK_RANK"
  --top-links-per-keyword "$TOP_LINKS_PER_KEYWORD"
  --out-root "$OUT_ROOT/keyword-path"
  --batch-out-dir "$OUT_ROOT/keyword-path-batch"
  --queue-dir "$ROOT_DIR/data/wechat-research/queue"
  --privacy-mode "$PRIVACY_MODE")

if [[ -n "$PWCLI" ]]; then
  BATCH_CMD+=(--pwcli "$PWCLI")
fi

"${BATCH_CMD[@]}"

QUEUE_CSV="$(ls -t "$ROOT_DIR"/data/wechat-research/queue/keyword-path-batch-*.csv 2>/dev/null | head -n 1 || true)"
if [[ -z "$QUEUE_CSV" ]]; then
  echo "ERROR: no queue CSV was produced." >&2
  exit 1
fi

ROUND_DIR="$OUT_ROOT/focus-round-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$ROUND_DIR"

echo "[2/3] harvesting queue: $QUEUE_CSV"
HARVEST_CMD=(python3 "$ROOT_DIR/scripts/wechat_harvest_with_pwcli.py"
  --input "$QUEUE_CSV"
  --out-dir "$ROUND_DIR"
  --privacy-mode "$PRIVACY_MODE")

if [[ -n "$PWCLI" ]]; then
  HARVEST_CMD+=(--pwcli "$PWCLI")
fi

"${HARVEST_CMD[@]}"

ARTICLES_JSONL="$ROUND_DIR/articles.jsonl"
if [[ ! -f "$ARTICLES_JSONL" ]]; then
  echo "ERROR: harvest did not produce $ARTICLES_JSONL" >&2
  exit 1
fi

echo "[3/3] building synthesis artifacts"
MATRIX_CMD=(python3 "$ROOT_DIR/scripts/wechat_dialectic_matrix.py"
  --input "$ARTICLES_JSONL"
  --out-dir "$ROUND_DIR"
  --wechat-only
  --min-source-score "$MIN_SOURCE_SCORE")

if [[ "$FOCUS_ONLY" == "1" ]]; then
  MATRIX_CMD+=(--focus-only)
fi

"${MATRIX_CMD[@]}"

echo "DONE: $ROUND_DIR"
