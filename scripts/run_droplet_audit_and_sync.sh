#!/bin/bash
# Run operational readiness audit on droplet, write to reports/droplet_audit/YYYY-MM-DD/,
# then sync EOD + droplet_audit to GitHub. Run on droplet (cron 21:32 UTC weekdays).
# Path-agnostic: uses REPO_DIR or script's parent directory.
set -e
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$REPO_DIR" || exit 1

DATE=$(date -u +%Y-%m-%d)
AUDIT_DIR="reports/droplet_audit/$DATE"
mkdir -p "$AUDIT_DIR"
PYTHON="${VENV_PYTHON:-/usr/bin/python3}"

# 0) Ensure unified daily intelligence pack exists (so audit MEDIUM passes)
"$PYTHON" scripts/run_stockbot_daily_reports.py --date "$DATE" --base-dir "$REPO_DIR" || true

# 1) Run audit, capture full output and exit code
LOG="$AUDIT_DIR/audit_summary.txt"
"$PYTHON" scripts/audit_stock_bot_readiness.py --date "$DATE" --verbose 2>&1 | tee "$LOG"
AUDIT_EXIT=${PIPESTATUS[0]}

# 2) Write machine-readable result
if [ "$AUDIT_EXIT" -eq 0 ]; then STATUS="pass"; else STATUS="fail"; fi
echo "{\"date\":\"$DATE\",\"exit_code\":$AUDIT_EXIT,\"status\":\"$STATUS\"}" > "$AUDIT_DIR/audit_result.json"

# 3) Pull latest, add EOD outputs and droplet_audit, commit, push
git fetch origin
git pull --rebase --autostash origin main || true
git add board/eod/out/*.md board/eod/out/*.json 2>/dev/null || true
git add "reports/stockbot/${DATE}/" 2>/dev/null || true
git add reports/droplet_audit/ || true
git status --short
if git diff --staged --quiet; then
  echo "Nothing to commit (no EOD or audit changes)."
else
  git commit -m "Droplet audit + EOD sync $DATE $(date -u +%H:%M UTC)"
  git push origin main
fi
