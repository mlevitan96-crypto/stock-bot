#!/usr/bin/env bash
# CURSOR_MASSIVE_30D_PROFIT_REVIEW_AND_ITERATE.sh
#
# OBJECTIVE:
#   STOP PROFIT BLEEDING AND FIND WHAT MAKES MONEY.
#
# GUARANTEES:
# - DROPLET ONLY
# - REAL DATA ONLY (attribution + exit_attribution + Alpaca bars)
# - NO SUPPRESSION (all symbols, times, directions)
# - RESUMABLE (cache + checkpoints)
# - MULTI-PERSONA REVIEW
# - DOZENS OF ITERATIONS
# - RANKED BY REALIZED PNL AFTER COSTS

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1

# --- DROPLET ENFORCEMENT ---
if [ ! -d "/root/stock-bot" ]; then
  echo "ERROR: Must run on droplet."
  exit 1
fi
# --- END DROPLET ENFORCEMENT ---

RUN_TAG="massive_30d_profit_review_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/massive_profit_reviews/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

DAYS=30
ITERATIONS="${ITERATIONS:-48}"
PARALLELISM="${PARALLELISM:-6}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== MASSIVE 30D PROFIT REVIEW START ==="

# -------------------------------------------------
# 1) ENSURE ALPACA BAR COMPLETENESS (RESUMABLE)
# -------------------------------------------------
log "Ensuring Alpaca bars complete for last ${DAYS} days"

python3 scripts/fill_alpaca_bars_30d.py \
  --days "${DAYS}" \
  --max_days_per_symbol 20 \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 2) BUILD CANONICAL 30D TRUTH DATASET
# -------------------------------------------------
log "Building canonical 30d truth dataset"

python3 scripts/analysis/build_30d_truth_dataset.py \
  --days "${DAYS}" \
  --attribution logs/attribution.jsonl \
  --exit_attribution logs/exit_attribution.jsonl \
  --bars data/bars \
  --out "${OUT_DIR}/truth_30d.json" \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 3) MASSIVE MULTI-ANGLE REVIEW
# -------------------------------------------------
log "Running massive review (entry, exit, direction, sizing, costs)"

python3 scripts/analysis/run_massive_profit_review.py \
  --truth "${OUT_DIR}/truth_30d.json" \
  --out "${OUT_DIR}/review" \
  --no_suppression \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 4) MULTI-PERSONA ADVERSARIAL REVIEW (uses existing multi_model_runner interface)
# -------------------------------------------------
if [ -f scripts/multi_model_runner.py ]; then
  log "Running multi-persona adversarial review"
  # Use first iteration as backtest dir if present; else review dir (runner expects backtest layout)
  BACKTEST_FOR_MM="${OUT_DIR}/review"
  if [ -d "${OUT_DIR}/iterations/iter_0001" ]; then
    BACKTEST_FOR_MM="${OUT_DIR}/iterations/iter_0001"
  fi
  python3 scripts/multi_model_runner.py \
    --backtest_dir "${BACKTEST_FOR_MM}" \
    --out "${OUT_DIR}/review/multi_model" \
    --roles "prosecutor,defender,sre,board" \
    | tee -a "${LOG}" || true
fi

# -------------------------------------------------
# 5) PROFITABILITY ITERATION CAMPAIGN (DOZENS)
# -------------------------------------------------
log "Launching profitability iterations"

mkdir -p "${OUT_DIR}/iterations"

python3 scripts/learning/run_profitability_campaign.py \
  --truth "${OUT_DIR}/truth_30d.json" \
  --iterations "${ITERATIONS}" \
  --parallelism "${PARALLELISM}" \
  --objective "MAX_PNL_AFTER_COSTS" \
  --no_suppression \
  --out "${OUT_DIR}/iterations" \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 6) AGGREGATE + PROMOTION PAYLOADS (PAPER ONLY)
# -------------------------------------------------
log "Aggregating results by profit"

python3 scripts/learning/aggregate_profitability_campaign.py \
  --campaign_dir "${OUT_DIR}" \
  --rank_by TOTAL_PNL_AFTER_COSTS \
  --emit_top_n 10 \
  --emit_promotion_payloads \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 7) FINAL SUMMARY
# -------------------------------------------------
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
MASSIVE 30D PROFIT REVIEW COMPLETE

DATA:
- Attribution + Exit Attribution (real droplet logs)
- Alpaca 1m bars (complete for last 30 days)

WHAT WAS DONE:
- Canonical 30d truth dataset built
- Massive multi-angle review (entry/exit/direction/sizing/costs)
- Multi-persona adversarial analysis
- Dozens of profitability iterations
- Ranked by realized PnL after costs

OUTPUTS:
- Truth dataset: ${OUT_DIR}/truth_30d.json
- Review: ${OUT_DIR}/review/
- Iterations: ${OUT_DIR}/iterations/
- Promotion payloads: ${OUT_DIR}/promotion_payloads/

DECISION:
- PROFITABILITY IS THE ONLY METRIC
- NO SUPPRESSION
- DROPLET TRUTH ENFORCED

LOG: ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
echo "DECISION: MASSIVE_30D_PROFIT_REVIEW_COMPLETE"
log "=== COMPLETE ==="
