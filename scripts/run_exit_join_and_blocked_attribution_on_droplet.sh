#!/usr/bin/env bash
# Exit join canonicalization + blocked trade attribution.
# Run on droplet. NO-APPLY. Observability only.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/root/stock-bot}"
DATE="${1:-$(date -u +%Y-%m-%d)}"
cd "$REPO_DIR" || exit 1

echo "Exit join + blocked attribution: REPO_DIR=$REPO_DIR DATE=$DATE"

git fetch origin
git pull --rebase --autostash origin main || true

# 1) Intel producers
REPO_DIR="$REPO_DIR" bash scripts/run_intel_producers_on_droplet.sh || true

# 2) UW no-live audit
python3 scripts/audit_no_live_uw_calls_in_scoring.py || exit 1

# 3) Run harness if needed (for exit/entry snapshots)
HARNESS_LOG="logs/signal_snapshots_harness_${DATE}.jsonl"
if [ ! -s "$HARNESS_LOG" ]; then
  python3 scripts/run_snapshot_harness.py --date "$DATE" --symbols "AAPL" --max-events 25 || true
fi

# 5) Generate exit join health report
python3 scripts/generate_exit_join_health_report.py --date "$DATE" --base-dir "$REPO_DIR" --snapshots-path "logs/signal_snapshots_harness_${DATE}.jsonl" 2>/dev/null || \
python3 scripts/generate_exit_join_health_report.py --date "$DATE" --base-dir "$REPO_DIR" || true

# 6) Generate blocked trade intel report (also runs linker → logs/blocked_trade_snapshots.jsonl)
python3 scripts/generate_blocked_trade_intel_report.py --date "$DATE" --base-dir "$REPO_DIR" || true

# 7) Commit + push
git add logs/blocked_trade_snapshots.jsonl \
        reports/EXIT_JOIN_HEALTH_${DATE}.md \
        reports/BLOCKED_TRADE_INTEL_${DATE}.md 2>/dev/null || true
if git diff --staged --quiet 2>/dev/null; then
  echo "No new artifacts to commit"
else
  git commit -m "Stock-bot: exit join canonicalization + blocked trade attribution $DATE" || true
  git push origin main || true
fi

echo "Done - exit join + blocked attribution $DATE"
