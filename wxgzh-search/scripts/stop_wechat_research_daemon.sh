#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT_DIR/output/wechat-research/_daemon/daemon.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "daemon not running (no pid file)"
  exit 0
fi

pid="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "$pid" ]]; then
  rm -f "$PID_FILE"
  echo "daemon pid empty, cleaned"
  exit 0
fi

if kill -0 "$pid" 2>/dev/null; then
  kill "$pid"
  echo "stopped daemon pid=$pid"
else
  echo "process not found for pid=$pid"
fi

rm -f "$PID_FILE"

