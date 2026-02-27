#!/usr/bin/env bash
# Canonical daily governance entry point. Fail-closed.
# Runs Molt workflow, then artifact completeness validation. Single PASS/FAIL verdict.
# Usage: bash scripts/run_daily_governance.sh [YYYY-MM-DD]
# Env: REPO_DIR (default: script repo root or /root/stock-bot on droplet)

set -u
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
DATE="${1:-$(date -u +%Y-%m-%d)}"
cd "$REPO_DIR" || exit 1

echo "Daily governance: REPO_DIR=$REPO_DIR DATE=$DATE"

# 1. Run Molt workflow (includes governance chair, writes state/molt_last_run.json and reports)
REPO_DIR="$REPO_DIR" bash "$REPO_DIR/scripts/run_molt_on_droplet.sh" "$DATE"
MOLT_RC=$?

# 2. Artifact completeness validation (fail-closed)
python3 "$REPO_DIR/scripts/validate_daily_governance_artifacts.py" --date "$DATE" --base-dir "$REPO_DIR"
VAL_RC=$?

# 3. Single verdict
if [ "$MOLT_RC" -ne 0 ]; then
  echo "Daily governance: FAIL (Molt exited with $MOLT_RC)"
  exit 1
fi
if [ "$VAL_RC" -ne 0 ]; then
  echo "Daily governance: FAIL (artifact validation failed)"
  exit 1
fi
echo "Daily governance: PASS"
exit 0
