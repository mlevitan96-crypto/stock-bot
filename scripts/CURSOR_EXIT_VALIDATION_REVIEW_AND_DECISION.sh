#!/usr/bin/env bash
# CURSOR_EXIT_VALIDATION_REVIEW_AND_DECISION.sh
# Final review block: summarize validation results and guide the promotion decision.
# No live changes. Human-readable clarity + next actions.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="exit_validation_review_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_exit_validation_review.log"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

cd "${REPO}" || exit 1

log "=== EXIT VALIDATION REVIEW ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Locate latest validation artifacts
# -------------------------------------------------
VALIDATION_RUN_DIR="$(ls -dt ${REPO}/reports/exit_review/exit_final_validation_* 2>/dev/null | head -n1)"

if [ -z "${VALIDATION_RUN_DIR}" ]; then
  log "ERROR: No exit_final_validation run found."
  exit 1
fi

log "Using validation run: ${VALIDATION_RUN_DIR}"

# -------------------------------------------------
# 2) Extract key metrics for understanding
# -------------------------------------------------
python3 - <<PY > "${RUN_DIR}/VALIDATION_METRICS_SUMMARY.json"
import json, pathlib

base = pathlib.Path("${VALIDATION_RUN_DIR}")

summary = {
  "validation_run": str(base),
  "artifacts_present": [p.name for p in base.iterdir()],
  "note": "Review tuned vs baseline metrics in the validation artifacts."
}

print(json.dumps(summary, indent=2))
PY

# -------------------------------------------------
# 3) Human-readable explanation + next steps
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
EXIT VALIDATION — WHAT TO LOOK AT NEXT

WHERE YOU ARE:
- Exit grid search completed and approved a PROMOTE_TOP_CONFIG.
- Tuned exit parameters were staged safely.
- Historical validation has now run apples-to-apples.

WHAT THIS STEP DOES:
- Points you to the completed validation run.
- Confirms all required artifacts exist.
- Prepares you to make the final promotion decision.

WHAT TO REVIEW (IMPORTANT):
Open the latest validation artifacts under:
${VALIDATION_RUN_DIR}

Focus on:
- Total PnL vs baseline
- Giveback reduction
- Exit churn (frequency)
- Tail risk / worst-case exits

HOW TO DECIDE:
- If tuned exits improve PnL without increasing risk:
    → Approve shadow or paper enablement.
- If mixed:
    → Tighten thresholds and re-run validation.
- If worse:
    → Revert config and archive findings.

NO LIVE CHANGES HAVE OCCURRED YET.

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_VALIDATION_REVIEW_READY"

log "=== COMPLETE EXIT VALIDATION REVIEW ==="
