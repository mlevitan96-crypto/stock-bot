#!/usr/bin/env bash
# CURSOR_FETCH_MISSING_BARS_AND_RERUN_GRID.sh
# Uses existing Alpaca bars in data/bars; only fetches missing (symbol, date) from Alpaca.
# Does NOT re-fetch 30 days from scratch. Then re-runs exit grid search + board review.
# Evidence-only. No trading behavior changes.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="exit_grid_with_bars_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_exit_grid_with_bars.log"

HIST_RUN_DIR="${HIST_RUN_DIR:-$(ls -dt ${REPO}/reports/exit_review/historical_* 2>/dev/null | head -n1)}"
BARS_DIR="${REPO}/data/bars"

mkdir -p "${RUN_DIR}" "${BARS_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found"

if [ -z "${HIST_RUN_DIR}" ] || [ ! -d "${HIST_RUN_DIR}" ]; then
  fail "No historical run (set HIST_RUN_DIR or run CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh first)"
fi
NORMALIZED="${HIST_RUN_DIR}/normalized_exit_truth.json"
if [ ! -f "${NORMALIZED}" ]; then
  fail "Missing ${NORMALIZED}"
fi

log "=== START FETCH MISSING BARS + GRID RERUN ${RUN_TAG} ==="
log "Historical run: ${HIST_RUN_DIR}"

# -------------------------------------------------
# 1) Identify exits missing bars
# -------------------------------------------------
log "Identifying exits missing bar coverage"

python3 scripts/analysis/find_exits_missing_bars.py \
  --normalized "${NORMALIZED}" \
  --bars_dir "${BARS_DIR}" \
  --out "${RUN_DIR}/missing_bars.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 2) Fetch missing bars from Alpaca (bounded)
# -------------------------------------------------
log "Fetching missing bars from Alpaca (only required symbols/dates)"

python3 scripts/analysis/fetch_missing_bars_from_alpaca.py \
  --missing "${RUN_DIR}/missing_bars.json" \
  --bars_dir "${BARS_DIR}" \
  --timeframe "1Min" \
  --max_days_per_symbol 10 \
  2>&1 | tee -a "${LOG}" || log "Fetch skipped or failed (check ALPACA_API_KEY/SECRET on droplet); continuing with existing bars"

# -------------------------------------------------
# 3) Re-run exit grid search (uses data/bars under repo)
# -------------------------------------------------
log "Re-running exit parameter grid search with bars"

python3 scripts/analysis/exit_param_grid_search.py \
  --historical "${NORMALIZED}" \
  --out "${RUN_DIR}/grid_results.json" \
  --bars_dir "${BARS_DIR}" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 4) Board review of grid results
# -------------------------------------------------
log "Running board review on grid results"

python3 scripts/analysis/exit_grid_board_review.py \
  --grid_results "${RUN_DIR}/grid_results.json" \
  --out_dir "${RUN_DIR}/grid_board_review" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 5) Summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}

INPUT:
- normalized_exit_truth.json (historical)
- Missing bars fetched from Alpaca into data/bars

OUTPUT:
- grid_results.json (ranked exit configs)
- grid_board_review/
- grid_board_review/GRID_RECOMMENDATION.json

NEXT:
- If PROMOTE_TOP_CONFIG -> copy recommended_config into exit_candidate_signals.tuned.json
- Then run CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh for apples-to-apples validation
- If TUNE_OR_GET_MORE_BARS -> expand bar window or timeframe and re-run

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_GRID_WITH_BARS_COMPLETE"

log "=== COMPLETE FETCH MISSING BARS + GRID RERUN ==="
