#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/bootstrap_venv.sh [/absolute/or/relative/repo/path]
REPO_DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[bootstrap_venv] ERROR: python3 not found" >&2
  exit 1
fi

echo "[bootstrap_venv] Repo: $REPO_DIR"

# Ensure venv tooling exists (Ubuntu/Debian)
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y python3-venv python3-pip
fi

rm -rf venv
python3 -m venv venv

./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "[bootstrap_venv] OK"
