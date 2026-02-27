#!/usr/bin/env bash
# CURSOR_DROPLET_WIN_FINDING.sh
#
# PURPOSE:
#   Find the winning signal combination on real data.
#   Stocks move up or down; we need to capture that ahead of time and exit before we lose.
#   MIN_TRADES=2000 so we only accept policies with enough sample size.
#
# CONTRACT:
# - DROPLET ONLY
# - REAL DATA ONLY
# - NO SUPPRESSION
# - MIN_TRADES=2000

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="win_finding_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/win_finding/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

TRUTH_30D_PATH="${TRUTH_30D_PATH:-reports/massive_profit_reviews/massive_30d_profit_review_20260225T011830Z/truth_30d.json}"
INTEL_PATH="${INTEL_PATH:-reports/percent_move_intelligence/percent_move_intelligence_20260225T035926Z/entry_exit_intelligence.json}"

ITERATIONS="${ITERATIONS:-600}"
PARALLELISM="${PARALLELISM:-10}"
MIN_TRADES="${MIN_TRADES:-2000}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"
log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== WIN FINDING START (MIN_TRADES=${MIN_TRADES}) ==="
log "TRUTH=${TRUTH_30D_PATH}"
log "INTEL=${INTEL_PATH}"
log "OUT_DIR=${OUT_DIR}"

[ -f "${TRUTH_30D_PATH}" ] || { log "ERROR: truth missing"; exit 1; }

cp "${INTEL_PATH}" "${OUT_DIR}/entry_exit_intelligence.json" 2>/dev/null || true

# ------------------------------------------------------------
# 1) Generate win-finding policy grid (permissive + intel-driven)
# ------------------------------------------------------------
log "Generating win-finding policies (wide grid + intel)"
python3 scripts/learning/generate_win_finding_policies.py \
  --truth "${TRUTH_30D_PATH}" \
  --intelligence "${INTEL_PATH}" \
  --out "${OUT_DIR}/candidate_policies.json" \
  --max_candidates "${ITERATIONS}" \
  --no_suppression \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 2) Simulate all policies
# ------------------------------------------------------------
log "Simulating policies"
python3 scripts/learning/run_policy_simulations.py \
  --truth "${TRUTH_30D_PATH}" \
  --policies "${OUT_DIR}/candidate_policies.json" \
  --out "${OUT_DIR}/iterations" \
  --parallelism "${PARALLELISM}" \
  --objective MAX_PNL_AFTER_COSTS \
  --no_suppression \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 3) Aggregate with MIN_TRADES=2000
# ------------------------------------------------------------
log "Aggregating with MIN_TRADES=${MIN_TRADES}"
python3 scripts/learning/aggregate_profitability_campaign.py \
  --campaign_dir "${OUT_DIR}" \
  --rank_by TOTAL_PNL_AFTER_COSTS \
  --min_trades "${MIN_TRADES}" \
  --emit_top_n 15 \
  --emit_promotion_payloads \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 4) Summary
# ------------------------------------------------------------
log "Writing summary"
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
WIN FINDING COMPLETE

TRUTH: ${TRUTH_30D_PATH}
MIN_TRADES: ${MIN_TRADES}

OUTPUTS:
- candidate_policies.json
- iterations/
- aggregate_result.json
- promotion_payloads/

Check aggregate_result.json for top_n: winning combination = highest rank_key with trades_count >= ${MIN_TRADES}.

LOG: ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
log "=== COMPLETE ==="
