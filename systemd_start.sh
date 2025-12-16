#!/bin/bash
set -euo pipefail

# Run relative to the repo directory (works regardless of install path).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "venv/bin/activate" ]; then
  echo "[systemd_start] ERROR: venv not found at $SCRIPT_DIR/venv" >&2
  exit 1
fi

source "venv/bin/activate"
exec "venv/bin/python" "deploy_supervisor.py"
