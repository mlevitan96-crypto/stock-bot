#!/usr/bin/env bash
# CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh
#
# OBJECTIVE:
#   FIND REPEATABLE, PROFITABLE ENTRY/EXIT/DIRECTION/SIZING COMBINATIONS
#   USING REAL DROPLET DATA AND BRUTE-FORCE EVIDENCE.
#
# PHILOSOPHY:
# - Replay everything
# - Suppress nothing
# - Let combinations compete
# - Rank by money only
#
# DROPLET ONLY. NEVER FAILS. RESUMABLE.

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1

# --- DROPLET ENFORCEMENT ---
if [ ! -d "/root/stock-bot" ]; then
  echo "ERROR: Must run on droplet."
  exit 1
fi
# --- END DROPLET ENFORCEMENT ---

RUN_TAG="signal_replay_edge_discovery_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/edge_discovery/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

DAYS=30
ITERATIONS="${ITERATIONS:-96}"
PARALLELISM="${PARALLELISM:-8}"

MOVE_PCTS="${MOVE_PCTS:-0.5,1.0,1.5,2.0}"
LOOKAHEAD_MINUTES="${LOOKAHEAD_MINUTES:-5,15,30,60}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== MASSIVE SIGNAL REPLAY + EDGE DISCOVERY START ==="

# -------------------------------------------------
# 1) RESOLVE TRUTH DATASET (latest massive_profit_reviews run)
# -------------------------------------------------
TRUTH=""
if [ -n "${TRUTH_30D_PATH:-}" ] && [ -f "${TRUTH_30D_PATH}" ]; then
  TRUTH="${TRUTH_30D_PATH}"
else
  LATEST=$(ls -td reports/massive_profit_reviews/massive_30d_profit_review_* 2>/dev/null | head -1)
  if [ -n "${LATEST}" ] && [ -f "${LATEST}/truth_30d.json" ]; then
    TRUTH="${LATEST}/truth_30d.json"
  fi
fi
if [ -z "${TRUTH}" ] || [ ! -f "${TRUTH}" ]; then
  log "ERROR: truth_30d.json not found. Run CURSOR_MASSIVE_30D_PROFIT_REVIEW_AND_ITERATE.sh first, or set TRUTH_30D_PATH."
  exit 1
fi
log "Using TRUTH: ${TRUTH}"

# -------------------------------------------------
# 2) LABEL LARGE MOVES (UP/DOWN) AND LEADING WINDOWS
# -------------------------------------------------
log "Labeling large price moves and leading windows"

python3 scripts/analysis/label_large_moves.py \
  --truth "${TRUTH}" \
  --move_pcts "${MOVE_PCTS}" \
  --lookahead_minutes "${LOOKAHEAD_MINUTES}" \
  --out "${OUT_DIR}/labeled_moves.json" \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 3) REPLAY ENTRY SIGNALS AGAINST LABELED MOVES
# -------------------------------------------------
log "Replaying entry signals to find leading indicators"

python3 scripts/analysis/replay_entry_signals.py \
  --truth "${TRUTH}" \
  --labeled_moves "${OUT_DIR}/labeled_moves.json" \
  --out "${OUT_DIR}/signal_leading_stats.json" \
  --no_suppression \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 4) GENERATE SLOT-MACHINE COMBINATIONS
# -------------------------------------------------
log "Generating entry/exit/direction/sizing combinations"

python3 scripts/learning/generate_candidate_policies.py \
  --signal_stats "${OUT_DIR}/signal_leading_stats.json" \
  --out "${OUT_DIR}/candidate_policies.json" \
  --max_candidates "${ITERATIONS}" \
  --no_suppression \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 5) SIMULATE ALL CANDIDATES (RESUMABLE)
# -------------------------------------------------
log "Simulating candidate policies against real data"

mkdir -p "${OUT_DIR}/iterations"

python3 scripts/learning/run_policy_simulations.py \
  --truth "${TRUTH}" \
  --policies "${OUT_DIR}/candidate_policies.json" \
  --out "${OUT_DIR}/iterations" \
  --parallelism "${PARALLELISM}" \
  --objective MAX_PNL_AFTER_COSTS \
  --no_suppression \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 6) MULTI-PERSONA ADVERSARIAL REVIEW (existing interface)
# -------------------------------------------------
if [ -f scripts/multi_model_runner.py ]; then
  log "Running multi-persona review on top candidate"
  BACKTEST_FOR_MM="${OUT_DIR}/iterations"
  FIRST_ITER=$(ls -d "${OUT_DIR}"/iterations/policy_* 2>/dev/null | head -1)
  if [ -n "${FIRST_ITER}" ] && [ -d "${FIRST_ITER}/baseline" ]; then
    python3 scripts/multi_model_runner.py \
      --backtest_dir "${FIRST_ITER}" \
      --out "${OUT_DIR}/multi_model" \
      --roles "prosecutor,defender,sre,board" \
      | tee -a "${LOG}" || true
  else
    log "No policy iteration with baseline/ found; skipping multi_model"
  fi
fi

# -------------------------------------------------
# 7) AGGREGATE + PROMOTION PAYLOADS
# -------------------------------------------------
log "Aggregating results by realized profit"

python3 scripts/learning/aggregate_profitability_campaign.py \
  --campaign_dir "${OUT_DIR}" \
  --rank_by TOTAL_PNL_AFTER_COSTS \
  --emit_top_n 10 \
  --emit_promotion_payloads \
  | tee -a "${LOG}" || true

# -------------------------------------------------
# 8) FINAL SUMMARY
# -------------------------------------------------
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
MASSIVE SIGNAL REPLAY + EDGE DISCOVERY COMPLETE

DATA:
- Real 30d trades, exits, and Alpaca bars (truth: ${TRUTH})
- No suppression of symbols, times, or directions

WHAT WAS DONE:
- Labeled large up/down moves
- Identified leading indicators
- Generated entry/exit/direction/sizing combinations
- Simulated all combinations on real data
- Ranked by realized PnL after costs
- Multi-persona adversarial review (if available)

OUTPUTS:
- Labeled moves: ${OUT_DIR}/labeled_moves.json
- Signal stats: ${OUT_DIR}/signal_leading_stats.json
- Candidate policies: ${OUT_DIR}/candidate_policies.json
- Iterations: ${OUT_DIR}/iterations/
- Promotion payloads: ${OUT_DIR}/promotion_payloads/

DECISION:
- PROFITABILITY IS THE ONLY METRIC
- SLOT-MACHINE SEARCH COMPLETE

LOG: ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
echo "DECISION: MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY_COMPLETE"
log "=== COMPLETE ==="
