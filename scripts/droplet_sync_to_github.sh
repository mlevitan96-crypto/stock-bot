#!/bin/bash
# EOD report auto-sync to GitHub. Run on droplet.
# Cron: 32 21 * * 1-5 (weekdays 21:32 UTC)
# Use REPO_DIR if set; else detect same root as EOD cron (stock-bot-current, then stock-bot).
# EOD output lives in board/eod/out/YYYY-MM-DD/; must add that folder explicitly.
set -e
if [ -z "${REPO_DIR}" ]; then
  if [ -d /root/stock-bot-current/scripts ] && [ -f /root/stock-bot-current/board/eod/eod_confirmation.py ]; then
    REPO_DIR=/root/stock-bot-current
  else
    REPO_DIR=/root/stock-bot
  fi
fi
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
