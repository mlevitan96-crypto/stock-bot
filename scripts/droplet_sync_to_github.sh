#!/bin/bash
# EOD report auto-sync to GitHub. Run on droplet.
# Cron: 32 21 * * 1-5 (weekdays 21:32 UTC)
# Path-agnostic: uses REPO_DIR or script's parent directory
# EOD output lives in board/eod/out/YYYY-MM-DD/; must add that folder explicitly.
set -e
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR" || exit 1
DATE=$(date -u +%Y-%m-%d)
git fetch origin
git pull --rebase --autostash origin main || true
git add board/eod/out/*.md board/eod/out/*.json 2>/dev/null || true
git add "board/eod/out/${DATE}/" 2>/dev/null || true
git add "reports/stockbot/${DATE}/" 2>/dev/null || true
if git diff --staged --quiet 2>/dev/null; then
  echo "Nothing to commit (no EOD or report changes)."
else
  git commit -m "EOD report auto-sync $DATE $(date -u +%H:%M UTC)"
  git push origin main
fi
