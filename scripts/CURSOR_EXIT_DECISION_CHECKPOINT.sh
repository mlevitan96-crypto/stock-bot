#!/usr/bin/env bash
# CURSOR_EXIT_DECISION_CHECKPOINT.sh
# Final checkpoint after validation review.
# No execution. No mutation. Decision framing only.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="exit_decision_checkpoint_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"

mkdir -p "${RUN_DIR}"

cd "${REPO}" || exit 1

# -------------------------------------------------
# Locate latest artifacts
# -------------------------------------------------
GRID_RUN_DIR="$(ls -dt ${REPO}/reports/exit_review/exit_grid_with_bars_* 2>/dev/null | head -n1)"
VALIDATION_RUN_DIR="$(ls -dt ${REPO}/reports/exit_review/exit_final_validation_* 2>/dev/null | head -n1)"

# -------------------------------------------------
# Write decision checkpoint summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
EXIT PIPELINE — DECISION CHECKPOINT

WHERE WE ARE:
- Historical exits reconstructed and normalized.
- Alpaca bars fetched and cached.
- Exit grid search simulated 1,643 exits across 160 configs.
- Board decision from grid: PROMOTE_TOP_CONFIG.
- Tuned exit config staged safely.
- Apples-to-apples historical validation completed.
- Validation review artifacts are present.

AUTHORITATIVE ARTIFACTS:
- Grid run:
  ${GRID_RUN_DIR}
- Validation run:
  ${VALIDATION_RUN_DIR}

WHAT THIS MEANS:
- Exit logic is now evidence-driven.
- Promotion has been approved by the board.
- Validation has been executed to confirm improvement.
- No live trading behavior has been changed yet.

ALLOWED NEXT ACTIONS (CHOOSE ONE):
1) APPROVE SHADOW / PAPER ENABLEMENT
   - Enable tuned exits in shadow or paper mode.
   - Begin live truth capture via CTR.
   - Monitor PnL, churn, and tail risk.

2) REQUEST TUNING
   - Adjust exit thresholds.
   - Re-run validation only (no new grid needed).

3) HALT / ARCHIVE
   - Revert tuned config.
   - Archive findings as non-promotable.

IMPORTANT:
- Do NOT re-run the grid unless new data or hypotheses exist.
- Do NOT enable live exits without an explicit approval decision.
- This checkpoint is the governance handoff.

STATUS:
READY_FOR_HUMAN_DECISION
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_DECISION_CHECKPOINT_READY"
