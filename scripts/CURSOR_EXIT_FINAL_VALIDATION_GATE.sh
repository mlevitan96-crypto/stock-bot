#!/usr/bin/env bash
# CURSOR_EXIT_FINAL_VALIDATION_GATE.sh
# Final evidence gate before any shadow or paper enablement.
# No live trading changes.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="exit_final_validation_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_exit_final_validation.log"

HIST_RUN_DIR="$(ls -dt ${REPO}/reports/exit_review/historical_* 2>/dev/null | head -n1)"
TUNED_CONFIG="config/exit_candidate_signals.tuned.json"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

cd "${REPO}" || exit 1

log "=== EXIT FINAL VALIDATION GATE ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Preconditions
# -------------------------------------------------
if [ ! -f "${TUNED_CONFIG}" ]; then
  log "ERROR: Tuned exit config not found: ${TUNED_CONFIG}"
  exit 1
fi

if [ -z "${HIST_RUN_DIR}" ] || [ ! -f "${HIST_RUN_DIR}/normalized_exit_truth.json" ]; then
  log "ERROR: No historical exit truth available for validation."
  exit 1
fi

log "Using historical truth: ${HIST_RUN_DIR}"
log "Using tuned config: ${TUNED_CONFIG}"

# -------------------------------------------------
# 2) Run apples-to-apples validation
# -------------------------------------------------
log "Running validation: tuned exits vs baseline"

bash scripts/CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 3) Human-readable summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
EXIT FINAL VALIDATION — WHAT IS HAPPENING

CONTEXT:
- A bar-based exit grid search simulated 1,643 real exits.
- 160 exit parameter sets were evaluated.
- The board approved a PROMOTE_TOP_CONFIG.

WHAT THIS STEP DOES:
- Re-runs the historical exit pipeline using the tuned exit config.
- Compares tuned exits vs the original baseline.
- Produces apples-to-apples metrics (PnL, churn, drawdown).

IMPORTANT:
- No live trading behavior is changed.
- This is the final evidence gate.

WHAT TO REVIEW:
- Validation artifacts under reports/exit_review/
- Look for:
  * Improved total PnL
  * Reduced giveback
  * Acceptable churn
  * No tail-risk regression

NEXT STEPS:
- If validation confirms improvement:
    → Approve shadow or paper enablement using CTR.
- If mixed:
    → Tighten thresholds and re-run validation.
- If regression:
    → Revert config and archive findings.

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_FINAL_VALIDATION_RUNNING"

log "=== COMPLETE EXIT FINAL VALIDATION GATE ==="
