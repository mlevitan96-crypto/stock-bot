#!/usr/bin/env bash
# CURSOR_DROPLET_CONTEXTUAL_EDGE_DISCOVERY.sh
#
# PURPOSE:
#   Use percent-move intelligence to CONSTRAIN policy generation.
#   Trade only when:
#     - Price has already moved by X%
#     - Signal state predicts continuation
#   Exit when:
#     - Signal state predicts exhaustion
#
# THIS IS WHERE EDGE TURNS INTO PROFIT.
#
# CONTRACT:
# - DROPLET ONLY
# - REAL DATA ONLY
# - NO SUPPRESSION
# - CONTEXTUAL ENTRIES
# - HIGH MIN_TRADES, BUT ACHIEVABLE

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="contextual_edge_discovery_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/contextual_edge_discovery/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

TRUTH_30D_PATH="${TRUTH_30D_PATH:-reports/massive_profit_reviews/massive_30d_profit_review_20260225T011830Z/truth_30d.json}"
INTEL_PATH="${INTEL_PATH:-reports/percent_move_intelligence/percent_move_intelligence_20260225T035926Z/entry_exit_intelligence.json}"

ITERATIONS="${ITERATIONS:-400}"
PARALLELISM="${PARALLELISM:-10}"
MIN_TRADES="${MIN_TRADES:-200}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"
log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== CONTEXTUAL EDGE DISCOVERY START ==="
log "TRUTH=${TRUTH_30D_PATH}"
log "INTEL=${INTEL_PATH}"
log "ITERATIONS=${ITERATIONS} PARALLELISM=${PARALLELISM} MIN_TRADES=${MIN_TRADES}"
log "OUT_DIR=${OUT_DIR}"

[ -f "${TRUTH_30D_PATH}" ] || { log "ERROR: truth missing"; exit 1; }
[ -f "${INTEL_PATH}" ] || { log "ERROR: entry/exit intelligence missing"; exit 1; }

cp "${INTEL_PATH}" "${OUT_DIR}/entry_exit_intelligence.json" || true

# ------------------------------------------------------------
# 1) Generate CONTEXTUAL candidate policies
# ------------------------------------------------------------
log "Generating contextual candidate policies from percent-move intelligence"
python3 scripts/learning/generate_contextual_policies.py \
  --truth "${TRUTH_30D_PATH}" \
  --intelligence "${INTEL_PATH}" \
  --out "${OUT_DIR}/candidate_policies.json" \
  --max_candidates "${ITERATIONS}" \
  --no_suppression \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 2) Simulate contextual policies
# ------------------------------------------------------------
log "Simulating contextual policies"
python3 scripts/learning/run_policy_simulations.py \
  --truth "${TRUTH_30D_PATH}" \
  --policies "${OUT_DIR}/candidate_policies.json" \
  --out "${OUT_DIR}/iterations" \
  --parallelism "${PARALLELISM}" \
  --objective MAX_PNL_AFTER_COSTS \
  --no_suppression \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 3) Aggregate with MIN_TRADES enforced
# ------------------------------------------------------------
log "Aggregating contextual results with MIN_TRADES=${MIN_TRADES}"
python3 scripts/learning/aggregate_profitability_campaign.py \
  --campaign_dir "${OUT_DIR}" \
  --rank_by TOTAL_PNL_AFTER_COSTS \
  --min_trades "${MIN_TRADES}" \
  --emit_top_n 10 \
  --emit_promotion_payloads \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 4) Board review packet
# ------------------------------------------------------------
log "Writing board review packet"
cat > "${OUT_DIR}/BOARD_REVIEW_PACKET.md" <<'MD'
# Board Review — Contextual Edge Discovery

## Objective
Validate that conditioning entries on price movement
and exits on signal exhaustion produces scalable edge.

## Questions
1. Do contextual entries improve expectancy?
2. Does trade count remain sufficient?
3. Which X% thresholds work best?
4. Which signals drive continuation?
5. Which exits preserve gains?

## Exhibits
- entry_exit_intelligence.json
- candidate_policies.json
- iterations/*/iteration_result.json
- aggregate_result.json
MD

# ------------------------------------------------------------
# 5) Final summary
# ------------------------------------------------------------
log "Writing final summary"
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
CONTEXTUAL EDGE DISCOVERY COMPLETE

TRUTH:
- ${TRUTH_30D_PATH}

INTELLIGENCE:
- ${INTEL_PATH}

OUTPUTS:
- candidate_policies.json
- iterations/
- aggregate_result.json
- promotion_payloads/
- BOARD_REVIEW_PACKET.md

NEXT STEP:
- Freeze the first contextual constraint that reduces loss
- Re-run with higher MIN_TRADES

LOG:
- ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
log "=== COMPLETE ==="
