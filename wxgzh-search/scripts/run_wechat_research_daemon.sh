#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
QUEUE_DIR="$ROOT_DIR/data/wechat-research/queue"
DONE_DIR="$QUEUE_DIR/processed"
FAILED_DIR="$QUEUE_DIR/failed"
OUT_ROOT="$ROOT_DIR/output/wechat-research"
LOG_DIR="$OUT_ROOT/_daemon"
LOG_FILE="$LOG_DIR/daemon.log"
PID_FILE="$LOG_DIR/daemon.pid"
SLEEP_SECONDS="${WECHAT_DAEMON_SLEEP_SECONDS:-45}"

mkdir -p "$QUEUE_DIR" "$DONE_DIR" "$FAILED_DIR" "$OUT_ROOT" "$LOG_DIR"

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "[daemon] already running pid=$old_pid"
    exit 0
  fi
fi

echo "$$" > "$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

echo "[$(date +"%F %T")] daemon started" >> "$LOG_FILE"

run_round() {
  local csv_file="$1"
  local base
  base="$(basename "$csv_file")"
  local round
  round="${base%.csv}"

  local out_dir="$OUT_ROOT/$round"
  local session="wx_${round//[^a-zA-Z0-9_]/_}"

  echo "[$(date +"%F %T")] start $base" >> "$LOG_FILE"

  if python3 "$ROOT_DIR/scripts/wechat_harvest_with_pwcli.py" \
      --input "$csv_file" \
      --out-dir "$out_dir" \
      --session "$session" \
      --privacy-mode incognito \
      --pw-timeout-s 30 >> "$LOG_FILE" 2>&1; then
    python3 "$ROOT_DIR/scripts/wechat_build_index.py" \
      --input "$out_dir/articles.jsonl" \
      --out-db "$out_dir/index/articles.db" \
      --out-stats "$out_dir/index/stats.json" >> "$LOG_FILE" 2>&1

    python3 "$ROOT_DIR/scripts/wechat_extract_process_docs.py" \
      --input "$out_dir/articles.jsonl" \
      --out-dir "$out_dir" >> "$LOG_FILE" 2>&1

    python3 "$ROOT_DIR/scripts/wechat_dialectic_matrix.py" \
      --input "$out_dir/articles.jsonl" \
      --out-dir "$out_dir" \
      --wechat-only \
      --focus-only >> "$LOG_FILE" 2>&1

    mv "$csv_file" "$DONE_DIR/$base"
    echo "[$(date +"%F %T")] done $base -> $out_dir" >> "$LOG_FILE"
  else
    mv "$csv_file" "$FAILED_DIR/$base"
    echo "[$(date +"%F %T")] failed $base" >> "$LOG_FILE"
  fi
}

while true; do
  shopt -s nullglob
  files=("$QUEUE_DIR"/*.csv)
  shopt -u nullglob

  if [[ ${#files[@]} -eq 0 ]]; then
    sleep "$SLEEP_SECONDS"
    continue
  fi

  for file in "${files[@]}"; do
    [[ -f "$file" ]] || continue
    run_round "$file"
  done

  sleep "$SLEEP_SECONDS"
done
