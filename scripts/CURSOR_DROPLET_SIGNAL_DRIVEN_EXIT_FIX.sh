#!/usr/bin/env bash
# CURSOR_DROPLET_SIGNAL_DRIVEN_EXIT_FIX.sh
#
# PURPOSE:
#   Replace time-based exits with SIGNAL-DRIVEN exits using
#   entry_exit_intelligence.json. Iterate on massive entry+exit combinations
#   to find data-driven profitable signal combinations.
#
#   This block:
#   - Derives continuation vs exhaustion thresholds from intelligence
#   - Generates contextual policies with signal-driven hold windows
#   - Simulates and aggregates with MIN_TRADES
#   - Keeps governance intact; goal = overall winning combinations
#
# CONTRACT:
# - DROPLET ONLY
# - REAL DATA ONLY
# - NO SUPPRESSION
# - EXIT BY INFORMATION, NOT TIME

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="signal_exit_fix_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/signal_exit_fix/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

TRUTH_30D_PATH="${TRUTH_30D_PATH:-reports/massive_profit_reviews/massive_30d_profit_review_20260225T011830Z/truth_30d.json}"
INTEL_PATH="${INTEL_PATH:-reports/percent_move_intelligence/percent_move_intelligence_20260225T035926Z/entry_exit_intelligence.json}"

ITERATIONS="${ITERATIONS:-300}"
PARALLELISM="${PARALLELISM:-10}"
MIN_TRADES="${MIN_TRADES:-200}"
MAX_HOLD_CAP_MIN="${MAX_HOLD_CAP_MIN:-60}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"
log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== SIGNAL-DRIVEN EXIT FIX START ==="
log "TRUTH=${TRUTH_30D_PATH}"
log "INTEL=${INTEL_PATH}"
log "ITERATIONS=${ITERATIONS} PARALLELISM=${PARALLELISM} MIN_TRADES=${MIN_TRADES}"
log "MAX_HOLD_CAP_MIN=${MAX_HOLD_CAP_MIN}"
log "OUT_DIR=${OUT_DIR}"

[ -f "${TRUTH_30D_PATH}" ] || { log "ERROR: truth missing"; exit 1; }
[ -f "${INTEL_PATH}" ] || { log "ERROR: intelligence missing"; exit 1; }

cp "${INTEL_PATH}" "${OUT_DIR}/entry_exit_intelligence.json" || true

# ------------------------------------------------------------
# 1) Derive exit thresholds from intelligence
# ------------------------------------------------------------
log "Deriving signal-driven exit thresholds from intelligence"
python3 scripts/learning/derive_signal_exit_thresholds.py \
  --intelligence "${INTEL_PATH}" \
  --out "${OUT_DIR}/exit_thresholds.json" \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 2) Generate contextual policies with signal-driven exits
# ------------------------------------------------------------
log "Generating contextual policies with signal-driven exits"
python3 scripts/learning/generate_contextual_policies.py \
  --truth "${TRUTH_30D_PATH}" \
  --intelligence "${INTEL_PATH}" \
  --exit_thresholds "${OUT_DIR}/exit_thresholds.json" \
  --max_hold_cap_min "${MAX_HOLD_CAP_MIN}" \
  --out "${OUT_DIR}/candidate_policies.json" \
  --max_candidates "${ITERATIONS}" \
  --no_suppression \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 3) Simulate policies (hold_min = signal-driven exit window)
# ------------------------------------------------------------
log "Simulating policies with signal-driven exits"
python3 scripts/learning/run_policy_simulations.py \
  --truth "${TRUTH_30D_PATH}" \
  --policies "${OUT_DIR}/candidate_policies.json" \
  --out "${OUT_DIR}/iterations" \
  --parallelism "${PARALLELISM}" \
  --objective MAX_PNL_AFTER_COSTS \
  --no_suppression \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 4) Aggregate with MIN_TRADES enforced
# ------------------------------------------------------------
log "Aggregating results with MIN_TRADES=${MIN_TRADES}"
python3 scripts/learning/aggregate_profitability_campaign.py \
  --campaign_dir "${OUT_DIR}" \
  --rank_by TOTAL_PNL_AFTER_COSTS \
  --min_trades "${MIN_TRADES}" \
  --emit_top_n 10 \
  --emit_promotion_payloads \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 5) Board review packet
# ------------------------------------------------------------
log "Writing board review packet"
cat > "${OUT_DIR}/BOARD_REVIEW_PACKET.md" <<'MD'
# Board Review — Signal-Driven Exit Fix

## Objective
Validate that replacing time-based exits with
signal-driven exhaustion/continuation exits
improves expectancy. Find overall winning entry+exit combinations.

## Questions
1. Did average win size increase?
2. Did average loss size decrease?
3. Did trade duration align with continuation?
4. Which exit thresholds worked best?
5. Is the edge now scalable?

## Exhibits
- entry_exit_intelligence.json
- exit_thresholds.json
- candidate_policies.json
- iterations/*/iteration_result.json
- aggregate_result.json
MD

# ------------------------------------------------------------
# 6) Final summary
# ------------------------------------------------------------
log "Writing final summary"
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
SIGNAL-DRIVEN EXIT FIX COMPLETE

TRUTH:
- ${TRUTH_30D_PATH}

INTELLIGENCE:
- ${INTEL_PATH}

EXIT MODEL:
- Signal-driven exhaustion/continuation
- Max hold cap: ${MAX_HOLD_CAP_MIN} min

OUTPUTS:
- exit_thresholds.json
- candidate_policies.json
- iterations/
- aggregate_result.json
- promotion_payloads/
- BOARD_REVIEW_PACKET.md

NEXT STEP:
- Compare PnL vs fixed-hold baseline
- Freeze best exit thresholds
- Re-run with higher MIN_TRADES

LOG:
- ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
log "=== COMPLETE ==="
