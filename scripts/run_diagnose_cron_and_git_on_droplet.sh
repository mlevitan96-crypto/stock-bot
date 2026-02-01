#!/usr/bin/env bash
# Run cron + git diagnostic on droplet.
# Path-agnostic: cd to repo root (script's parent's parent)
set -euo pipefail
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR" || exit 1
echo "Running diagnose_cron_and_git from $REPO_DIR"
python3 scripts/diagnose_cron_and_git.py
