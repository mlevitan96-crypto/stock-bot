#!/usr/bin/env bash
# CURSOR_DROPLET_WEEK_TO_DATE_DEEP_REVIEW.sh
#
# PURPOSE:
#   Perform a WEEK-TO-DATE (WTD) review using all existing intelligence:
#   - Percent-move signal correlation
#   - Contextual entry/exit behavior
#   - Policy performance
#
#   Designed to answer:
#   - Are signals behaving differently this week?
#   - Are exits failing in a new regime?
#   - Is this drawdown structural or temporary?
#
# CONTRACT:
# - DROPLET ONLY
# - REAL DATA ONLY
# - NO SUPPRESSION
# - NO FORWARD BIAS

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="week_to_date_review_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/week_to_date_review/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

# Inputs
FULL_TRUTH="${FULL_TRUTH:-reports/massive_profit_reviews/massive_30d_profit_review_20260225T011830Z/truth_30d.json}"
INTEL_30D="${INTEL_30D:-reports/percent_move_intelligence/percent_move_intelligence_20260225T035926Z/entry_exit_intelligence.json}"

# WTD definition: Monday 00:00 UTC → now
WTD_START_UTC="$(date -u -d 'last monday' +%Y-%m-%dT00:00:00Z)"

MOVE_PCTS="${MOVE_PCTS:-0.5,1.0,1.5,2.0}"
LOOKBACK_MINUTES="${LOOKBACK_MINUTES:-5,15,30,60}"
LOOKAHEAD_MINUTES="${LOOKAHEAD_MINUTES:-5,15,30,60}"

ITERATIONS="${ITERATIONS:-200}"
PARALLELISM="${PARALLELISM:-8}"
MIN_TRADES="${MIN_TRADES:-50}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"
log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== WEEK-TO-DATE DEEP REVIEW START ==="
log "FULL_TRUTH=${FULL_TRUTH}"
log "WTD_START_UTC=${WTD_START_UTC}"
log "OUT_DIR=${OUT_DIR}"

[ -f "${FULL_TRUTH}" ] || { log "ERROR: truth missing"; exit 1; }

# ------------------------------------------------------------
# 1) Slice truth to WEEK-TO-DATE
# ------------------------------------------------------------
log "Slicing truth to week-to-date window"
python3 scripts/analysis/slice_truth_by_time.py \
  --truth "${FULL_TRUTH}" \
  --start_utc "${WTD_START_UTC}" \
  --out "${OUT_DIR}/truth_wtd.json" \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 2) Percent-move intelligence on WTD only
# ------------------------------------------------------------
log "Running percent-move intelligence on WTD data"
python3 scripts/analysis/label_large_moves.py \
  --truth "${OUT_DIR}/truth_wtd.json" \
  --move_pcts "${MOVE_PCTS}" \
  --lookahead_minutes "${LOOKAHEAD_MINUTES}" \
  --out "${OUT_DIR}/labeled_moves_wtd.json" \
  | tee -a "${LOG}" || true

python3 scripts/analysis/correlate_signals_before_moves.py \
  --truth "${OUT_DIR}/truth_wtd.json" \
  --labeled_moves "${OUT_DIR}/labeled_moves_wtd.json" \
  --lookback_minutes "${LOOKBACK_MINUTES}" \
  --out "${OUT_DIR}/signal_pre_move_wtd.json" \
  --no_suppression \
  | tee -a "${LOG}" || true

python3 scripts/analysis/correlate_signals_after_moves.py \
  --truth "${OUT_DIR}/truth_wtd.json" \
  --labeled_moves "${OUT_DIR}/labeled_moves_wtd.json" \
  --lookahead_minutes "${LOOKAHEAD_MINUTES}" \
  --out "${OUT_DIR}/signal_post_move_wtd.json" \
  --no_suppression \
  | tee -a "${LOG}" || true

python3 scripts/analysis/build_entry_exit_intelligence.py \
  --pre "${OUT_DIR}/signal_pre_move_wtd.json" \
  --post "${OUT_DIR}/signal_post_move_wtd.json" \
  --out "${OUT_DIR}/entry_exit_intelligence_wtd.json" \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 3) Contextual policy simulation on WTD
# ------------------------------------------------------------
log "Running contextual policy simulation on WTD"
python3 scripts/learning/generate_contextual_policies.py \
  --truth "${OUT_DIR}/truth_wtd.json" \
  --intelligence "${OUT_DIR}/entry_exit_intelligence_wtd.json" \
  --max_candidates "${ITERATIONS}" \
  --out "${OUT_DIR}/candidate_policies_wtd.json" \
  --no_suppression \
  | tee -a "${LOG}" || true

python3 scripts/learning/run_policy_simulations.py \
  --truth "${OUT_DIR}/truth_wtd.json" \
  --policies "${OUT_DIR}/candidate_policies_wtd.json" \
  --out "${OUT_DIR}/iterations" \
  --parallelism "${PARALLELISM}" \
  --objective MAX_PNL_AFTER_COSTS \
  --no_suppression \
  | tee -a "${LOG}" || true

python3 scripts/learning/aggregate_profitability_campaign.py \
  --campaign_dir "${OUT_DIR}" \
  --rank_by TOTAL_PNL_AFTER_COSTS \
  --min_trades "${MIN_TRADES}" \
  --emit_top_n 10 \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 4) Board review packet
# ------------------------------------------------------------
cat > "${OUT_DIR}/BOARD_REVIEW_PACKET.md" <<'MD'
# Week-To-Date Deep Review

## Objective
Determine whether the last 3 losing days represent:
- A temporary drawdown
- A regime shift
- A signal failure
- An exit failure

## Questions
1. Are entry signals weaker WTD vs 30D?
2. Are continuation rates lower?
3. Are exhaustion signals appearing earlier?
4. Is direction asymmetry stronger?
5. Should exits tighten or entries pause?

## Exhibits
- truth_wtd.json
- entry_exit_intelligence_wtd.json
- aggregate_result.json
- candidate_policies_wtd.json
MD

# ------------------------------------------------------------
# 5) Final summary
# ------------------------------------------------------------
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
WEEK-TO-DATE REVIEW COMPLETE

WINDOW:
- From ${WTD_START_UTC} to now

OUTPUTS:
- truth_wtd.json
- entry_exit_intelligence_wtd.json
- aggregate_result.json
- BOARD_REVIEW_PACKET.md

NEXT STEP:
- Compare WTD intelligence vs 30D
- Decide whether to pause, tighten, or invert signals

LOG:
- ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
log "=== COMPLETE ==="
