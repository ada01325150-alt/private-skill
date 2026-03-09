#!/usr/bin/env bash
set -euo pipefail

echo "[browser-automation-ops] version=1.0.0"

if ! command -v agent-browser >/dev/null 2>&1; then
  echo "ERROR: agent-browser is not installed or not on PATH." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required." >&2
  exit 1
fi

echo "agent-browser: $(command -v agent-browser)"
echo "python3: $(command -v python3)"
echo "npx: ${NPX_PATH:-$(command -v npx || true)}"

echo "--- agent-browser help (first lines) ---"
agent-browser --help | sed -n '1,20p'
