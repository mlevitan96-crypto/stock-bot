#!/usr/bin/env bash
# Molt workflow on droplet. Post-market. NO-APPLY.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/root/stock-bot}"
DATE="${1:-$(date -u +%Y-%m-%d)}"
cd "$REPO_DIR" || exit 1

echo "Molt workflow: REPO_DIR=$REPO_DIR DATE=$DATE"

git fetch origin
git pull --rebase --autostash origin main || true

# Run learning pipeline first if not already done
REPO_DIR="$REPO_DIR" bash scripts/run_exit_join_and_blocked_attribution_on_droplet.sh "$DATE" 2>/dev/null || true
REPO_DIR="$REPO_DIR" bash scripts/run_snapshot_outcome_attribution_on_droplet.sh "$DATE" 2>/dev/null || true

# Molt workflow
python3 scripts/run_molt_workflow.py --date "$DATE" --base-dir "$REPO_DIR" || exit 1

# Commit Molt artifacts
git add reports/LEARNING_STATUS_${DATE}.md \
        reports/ENGINEERING_HEALTH_${DATE}.md \
        reports/PROMOTION_DISCIPLINE_${DATE}.md \
        reports/MEMORY_BANK_CHANGE_PROPOSAL_${DATE}.md 2>/dev/null || true
git add reports/PROMOTION_PROPOSAL_${DATE}.md reports/REJECTION_WITH_REASON_${DATE}.md 2>/dev/null || true
if git diff --staged --quiet 2>/dev/null; then
  echo "No new Molt artifacts to commit"
else
  git commit -m "Stock-bot: Molt workflow $DATE" || true
  git push origin main || true
fi

echo "Molt workflow done."
