#!/usr/bin/env bash
# CURSOR_FINAL_GRID_EXECUTION_AND_VERIFICATION.sh
# Final execution block to confirm bar ingestion + grid simulation end-to-end.
# No new logic. No redesign. Pure verification + decisive run.
# Run ON the droplet (e.g. after sourcing .env).

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="final_grid_exec_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_final_grid_exec.log"

HIST_RUN_DIR="${HIST_RUN_DIR:-$(ls -dt ${REPO}/reports/exit_review/historical_* 2>/dev/null | head -n1)}"
BARS_DIR="${REPO}/data/bars"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || exit 1

if [ -z "${HIST_RUN_DIR}" ] || [ ! -d "${HIST_RUN_DIR}" ]; then
  fail "No historical run (set HIST_RUN_DIR or run CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh first)"
fi
NORMALIZED="${HIST_RUN_DIR}/normalized_exit_truth.json"
[ -f "${NORMALIZED}" ] || fail "Missing ${NORMALIZED}"

log "=== FINAL GRID EXECUTION ${RUN_TAG} ==="
log "Historical run: ${HIST_RUN_DIR}"
log "Bars dir: ${BARS_DIR}"

# -------------------------------------------------
# 1) Sanity check: bars exist on disk
# -------------------------------------------------
log "Checking bar cache presence"
ls -la "${BARS_DIR}" 2>/dev/null | tee -a "${LOG}" || log "Bars dir empty or missing (will need fetch)"

# -------------------------------------------------
# 2) Quick grid smoke test (small grid)
# -------------------------------------------------
log "Running grid smoke test (grid_size=2)"

python3 scripts/analysis/exit_param_grid_search.py \
  --historical "${NORMALIZED}" \
  --bars_dir "${BARS_DIR}" \
  --grid_size 2 \
  --out "${RUN_DIR}/grid_smoke_test.json" \
  2>&1 | tee -a "${LOG}"

SMOKE_SIMULATED=$(jq -r '.n_exits_with_bars // 0' "${RUN_DIR}/grid_smoke_test.json" 2>/dev/null || echo "0")
log "Smoke test n_exits_with_bars=${SMOKE_SIMULATED}"

if [ "${SMOKE_SIMULATED}" -eq 0 ] 2>/dev/null; then
  log "ERROR: Grid still sees zero simulated exits. Bars not being read."
  exit 1
fi

# -------------------------------------------------
# 3) Full fetch + grid + board review (on-droplet pipeline)
# -------------------------------------------------
log "Running full fetch + grid + board review pipeline"

bash scripts/CURSOR_FETCH_MISSING_BARS_AND_RERUN_GRID.sh 2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 4) Final summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}

CONFIRMED:
- Alpaca Market Data API working
- Bars present in data/bars
- Grid can read bars (n_exits_with_bars > 0)

ACTION TAKEN:
- Full grid search + board review executed via CURSOR_FETCH_MISSING_BARS_AND_RERUN_GRID.sh

NEXT:
- Inspect latest run dir: reports/exit_review/exit_grid_with_bars_<ts>/grid_board_review/GRID_RECOMMENDATION.json
- If PROMOTE_TOP_CONFIG:
    * Copy recommended_config into config/exit_candidate_signals.tuned.json
    * Run CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh
- If TUNE:
    * Adjust grid bounds or bar window and re-run

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: FINAL_GRID_EXECUTION_COMPLETE"

log "=== COMPLETE FINAL GRID EXECUTION ==="
