#!/usr/bin/env bash
# CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh
# Iterate many exit-rule variations on historical exits (bar-based simulation).
# Board review recommends top configs for tuning. Run on droplet.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
PREV_RUN_DIR="${PREV_RUN_DIR:-$(ls -dt ${REPO}/reports/exit_review/historical_* 2>/dev/null | head -n1)}"
RUN_TAG="exit_grid_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_exit_grid.log"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found"

if [ -z "${PREV_RUN_DIR}" ] || [ ! -d "${PREV_RUN_DIR}" ]; then
  fail "No previous historical run (set PREV_RUN_DIR or run CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh first)"
fi
NORMALIZED="${PREV_RUN_DIR}/normalized_exit_truth.json"
if [ ! -f "${NORMALIZED}" ]; then
  fail "Missing ${NORMALIZED}"
fi

log "=== START EXIT GRID SEARCH + BOARD REVIEW ${RUN_TAG} ==="
log "Using normalized exits: ${NORMALIZED}"

# -------------------------------------------------
# 1) Grid search over exit params (bar-based sim)
# -------------------------------------------------
log "Running exit parameter grid search"

python3 scripts/analysis/exit_param_grid_search.py \
  --historical "${NORMALIZED}" \
  --out "${RUN_DIR}/grid_results.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 2) Board review of grid results
# -------------------------------------------------
log "Running board review of grid results"

python3 scripts/analysis/exit_grid_board_review.py \
  --grid_results "${RUN_DIR}/grid_results.json" \
  --out_dir "${RUN_DIR}/grid_board_review" \
  --top_n 5 \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 3) Summary
# -------------------------------------------------
REC=$(cat "${RUN_DIR}/grid_board_review/GRID_RECOMMENDATION.json" 2>/dev/null || echo "{}")
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}
NORMALIZED_SOURCE: ${NORMALIZED}

ARTIFACTS:
- grid_results.json (all param sets, ranked by simulated PnL)
- grid_board_review/ (prosecutor, defender, quant, sre, board)
- grid_board_review/GRID_RECOMMENDATION.json

NEXT:
- Apply recommended_config to config/exit_candidate_signals.tuned.json
- Run CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh for apples-to-apples validation
- If bar coverage was low, fetch more bars (data/bars or parquet) and re-run grid

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_GRID_SEARCH_COMPLETE"
log "=== COMPLETE EXIT GRID SEARCH + REVIEW ==="
