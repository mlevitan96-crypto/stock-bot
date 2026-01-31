#!/usr/bin/env bash
# Snapshot→Outcome attribution on droplet. NO-APPLY. No orders placed.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/root/stock-bot}"
cd "$REPO_DIR" || exit 1

DATE="${1:-$(date -u +%Y-%m-%d)}"

echo "Snapshot outcome attribution: REPO_DIR=$REPO_DIR DATE=$DATE"

git fetch origin
git pull --rebase --autostash origin main || true

# 1) Intel producers
REPO_DIR="$REPO_DIR" bash scripts/run_intel_producers_on_droplet.sh || true

# 2) UW no-live audit
python3 scripts/audit_no_live_uw_calls_in_scoring.py || exit 1

# 3) Run harness if not already run today
HARNESS_LOG="logs/signal_snapshots_harness_${DATE}.jsonl"
if [ ! -s "$HARNESS_LOG" ]; then
  python3 scripts/run_snapshot_harness.py --date "$DATE" --symbols "AAPL" --max-events 25
fi

# 4) Generate shadow snapshots from harness
python3 scripts/generate_shadow_snapshots.py --date "$DATE" --source harness --max-records 50

# 5) Generate attribution report (baseline + shadow)
python3 scripts/generate_snapshot_outcome_attribution_report.py --date "$DATE" --snapshots-path "logs/signal_snapshots_harness_${DATE}.jsonl"

# 6) Commit + push (once)
if [ "${AUTO_COMMIT_PUSH:-1}" = "1" ]; then
  git add logs/signal_snapshots_shadow_${DATE}.jsonl \
          reports/SNAPSHOT_OUTCOME_ATTRIBUTION_${DATE}.md \
          scripts/generate_snapshot_outcome_attribution_report.py \
          scripts/generate_shadow_snapshots.py \
          scripts/run_snapshot_outcome_attribution_on_droplet.sh \
          scripts/run_snapshot_outcome_attribution_on_droplet.py \
          config/shadow_snapshot_profiles.yaml \
          telemetry/snapshot_join_keys.py \
          telemetry/snapshot_builder.py 2>/dev/null || true
  git status --short
  git commit -m "Stock-bot: snapshot→outcome attribution + shadow snapshots ${DATE}" || true
  git push origin main || true
  echo "Pushed."
fi

echo "Done — snapshot outcome attribution ${DATE}."
