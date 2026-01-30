#!/usr/bin/env bash
# Stock-Bot Signal Contribution & Intelligence Gap Audit on droplet.
# Run on droplet at /root/stock-bot.
# Produces reports/STOCK_SIGNAL_CONTRIBUTION_AND_GAPS_<DATE>.md
set -euo pipefail

REPO_DIR="${REPO_DIR:-/root/stock-bot}"
cd "$REPO_DIR" || exit 1

DATE="${1:-$(date -u +%Y-%m-%d)}"

echo "Signal contribution audit: REPO_DIR=$REPO_DIR DATE=$DATE"

git fetch origin
git pull --rebase --autostash origin main || true

python3 scripts/signal_contribution_and_gaps_audit.py --date "$DATE" --base-dir "$REPO_DIR"

REPORT="reports/STOCK_SIGNAL_CONTRIBUTION_AND_GAPS_${DATE}.md"
if [ ! -f "$REPORT" ]; then
  echo "ERROR: Report not created: $REPORT"
  exit 1
fi
if [ ! -s "$REPORT" ]; then
  echo "ERROR: Report is empty: $REPORT"
  exit 1
fi
echo "Report exists and non-empty: $REPORT"

if [ "${AUTO_COMMIT_PUSH:-1}" = "1" ]; then
  git add "$REPORT" scripts/signal_contribution_and_gaps_audit.py scripts/run_signal_contribution_audit_on_droplet.sh || true
  git status --short
  git commit -m "Stock-bot: signal contribution & intelligence gap audit ${DATE}" || true
  git push origin main || true
  echo "Committed and pushed."
else
  echo "AUTO_COMMIT_PUSH=0; skip commit/push."
fi

echo "Done — signal contribution audit ${DATE}."
