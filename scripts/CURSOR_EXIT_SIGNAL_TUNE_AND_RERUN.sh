#!/usr/bin/env bash
# CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh
# Config-only tuning based on prior BOARD_DECISION=TUNE.
# Re-runs the same historical exit review for apples-to-apples comparison.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
PREV_RUN_DIR="${PREV_RUN_DIR:-$(ls -dt ${REPO}/reports/exit_review/historical_* 2>/dev/null | head -n1)}"
RUN_TAG="exit_tune_rerun_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/tuned_${RUN_TAG}"
LOG="/tmp/cursor_exit_tune_rerun.log"

START_DATE="${START_DATE:-2025-10-01}"
END_DATE="${END_DATE:-2026-02-23}"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found"

[ -n "${PREV_RUN_DIR}" ] && [ -d "${PREV_RUN_DIR}" ] || fail "No previous historical run found (PREV_RUN_DIR=${PREV_RUN_DIR})"

log "=== START EXIT SIGNAL TUNE + RERUN ${RUN_TAG} ==="
log "Previous run: ${PREV_RUN_DIR}"
log "Window: ${START_DATE} -> ${END_DATE}"

# -------------------------------------------------
# 1) Extract tuning directives from prior review
# -------------------------------------------------
log "Extracting tuning directives from prior board review"

python3 scripts/analysis/extract_exit_tuning_directives.py \
  --prev_run "${PREV_RUN_DIR}" \
  --out "${RUN_DIR}/tuning_directives.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 2) Apply config-only tuning to candidate exit signals
# -------------------------------------------------
log "Applying config-only tuning to candidate exit signals"

python3 scripts/analysis/apply_exit_signal_tuning.py \
  --tuning "${RUN_DIR}/tuning_directives.json" \
  --out_config "config/exit_candidate_signals.tuned.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 3) Re-run historical exit review with tuned config
# -------------------------------------------------
log "Re-running historical exit review with tuned signals"

START_DATE="${START_DATE}" END_DATE="${END_DATE}" REPO="${REPO}" \
EXIT_SIGNAL_CONFIG="config/exit_candidate_signals.tuned.json" \
bash scripts/CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 4) Compare tuned vs baseline metrics
# -------------------------------------------------
TUNED_RUN_DIR=$(ls -dt ${REPO}/reports/exit_review/historical_* 2>/dev/null | head -n1)
log "Comparing tuned vs baseline edge metrics (baseline=${PREV_RUN_DIR}, tuned=${TUNED_RUN_DIR})"

python3 scripts/analysis/compare_exit_edge_runs.py \
  --baseline "${PREV_RUN_DIR}/exit_edge_metrics.json" \
  --tuned "${TUNED_RUN_DIR}/exit_edge_metrics.json" \
  --out "${RUN_DIR}/edge_comparison.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 5) Final summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}
BASELINE_RUN: ${PREV_RUN_DIR}
TUNED_RUN: ${TUNED_RUN_DIR}

ARTIFACTS:
- tuning_directives.json
- config/exit_candidate_signals.tuned.json
- edge_comparison.json

WHAT CHANGED:
- Config-only tuning of candidate exit signals
- No logic changes
- No trading behavior changes

NEXT:
- If BOARD_DECISION flips to PROMOTE -> prepare shadow/paper enablement using CTR.
- If still TUNE -> iterate config and re-run this block.
- If HOLD -> archive findings.

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_SIGNAL_TUNE_RERUN_COMPLETE"

log "=== COMPLETE EXIT SIGNAL TUNE + RERUN ==="
