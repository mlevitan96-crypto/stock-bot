#!/usr/bin/env bash
# Snapshot harness verification on droplet. NO ORDERS PLACED.
# Steps: pull → intel producers → harness → SIGNAL_MAP → commit + push (once).
set -euo pipefail

REPO_DIR="${REPO_DIR:-/root/stock-bot}"
cd "$REPO_DIR" || exit 1

DATE="${1:-$(date -u +%Y-%m-%d)}"

echo "Snapshot harness: REPO_DIR=$REPO_DIR DATE=$DATE"

git fetch origin
git pull --rebase --autostash origin main || true

# 1) Intel producers prewarm artifacts
REPO_DIR="$REPO_DIR" bash scripts/run_intel_producers_on_droplet.sh || true

# 2) Audit: no live UW in scoring (fail if violated)
python3 scripts/audit_no_live_uw_calls_in_scoring.py || exit 1

# 3) Harness
python3 scripts/run_snapshot_harness.py --date "$DATE" --symbols "AAPL" --max-events 25

# 4) SIGNAL_MAP from harness file
python3 scripts/generate_daily_signal_map_report.py --date "$DATE" --symbols "AAPL" --snapshots-path "logs/signal_snapshots_harness_${DATE}.jsonl" --base-dir "$REPO_DIR"

# 5) Verify artifacts
HARNESS_LOG="logs/signal_snapshots_harness_${DATE}.jsonl"
VERIFY_REPORT="reports/SNAPSHOT_HARNESS_VERIFICATION_${DATE}.md"
SIGNAL_MAP="reports/SIGNAL_MAP_${DATE}.md"

if [ ! -f "$HARNESS_LOG" ] || [ ! -s "$HARNESS_LOG" ]; then
  echo "ERROR: $HARNESS_LOG missing or empty"
  exit 1
fi
if [ ! -f "$VERIFY_REPORT" ]; then
  echo "ERROR: $VERIFY_REPORT missing"
  exit 1
fi
if [ ! -f "$SIGNAL_MAP" ]; then
  echo "ERROR: $SIGNAL_MAP missing"
  exit 1
fi
echo "Artifacts OK: $HARNESS_LOG, $VERIFY_REPORT, $SIGNAL_MAP"

# 6) Commit + push (exactly once)
if [ "${AUTO_COMMIT_PUSH:-1}" = "1" ]; then
  git add "$HARNESS_LOG" "$VERIFY_REPORT" "$SIGNAL_MAP" scripts/run_snapshot_harness.py scripts/run_snapshot_harness_on_droplet.sh scripts/audit_no_live_uw_calls_in_scoring.py 2>/dev/null || true
  git add scripts/generate_daily_signal_map_report.py 2>/dev/null || true
  git status --short
  git commit -m "Stock-bot: snapshot harness verification ${DATE}" || true
  git push origin main || true
  echo "Pushed."
fi

echo "Done — snapshot harness ${DATE}."
