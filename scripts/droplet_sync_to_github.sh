#!/bin/bash
# EOD report auto-sync to GitHub. Run on droplet.
# Cron: 32 21 * * 1-5 (weekdays 21:32 UTC)
# Path-agnostic: uses REPO_DIR or script's parent directory
set -e
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR" || exit 1
git fetch origin
git pull --rebase --autostash origin main || true
git add board/eod/out/*.md board/eod/out/*.json || true
git commit -m "EOD report auto-sync $(date -u +"%Y-%m-%d %H:%M UTC")" || true
git push origin main
