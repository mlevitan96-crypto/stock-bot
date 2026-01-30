#!/usr/bin/env bash
# Generate daily SIGNAL_MAP report on droplet.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/root/stock-bot}"
cd "$REPO_DIR" || exit 1

DATE="${1:-$(date -u +%Y-%m-%d)}"

echo "SIGNAL_MAP: REPO_DIR=$REPO_DIR DATE=$DATE"

git pull origin main || true

# Ensure log exists and is appendable
mkdir -p logs
touch logs/signal_snapshots.jsonl

python3 scripts/generate_daily_signal_map_report.py --date "$DATE" --base-dir "$REPO_DIR"

REPORT="reports/SIGNAL_MAP_${DATE}.md"
if [ ! -f "$REPORT" ]; then
  echo "Report not created: $REPORT"
  exit 1
fi

if [ "${AUTO_COMMIT_PUSH:-1}" = "1" ]; then
  git add "$REPORT" scripts/generate_daily_signal_map_report.py scripts/run_daily_signal_map_on_droplet.sh 2>/dev/null || true
  git commit -m "Stock-bot: SIGNAL_MAP ${DATE}" || true
  git push origin main || true
fi

echo "Done — SIGNAL_MAP ${DATE}."
