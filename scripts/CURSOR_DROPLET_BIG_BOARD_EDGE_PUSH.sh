#!/usr/bin/env bash
# CURSOR_DROPLET_BIG_BOARD_EDGE_PUSH.sh
#
# Non-negotiables:
# - DROPLET ONLY (/root/stock-bot)
# - REAL DATA ONLY (truth_30d.json from droplet run)
# - NO SUPPRESSION (learn from everything)
# - RESUMABLE + LONG-RUN FRIENDLY
# - BOARD-GRADE REVIEW (multi-persona, adversarial, decision-focused)
#
# What it does:
# 1) Runs EDGE DISCOVERY (massive signal replay: entry+exit+direction+sizing)
# 2) Enforces MIN_TRADES so 0-trade / tiny-sample policies cannot "win"
# 3) Produces WHY packets per iteration + aggregate ranking
# 4) Generates a Board Review Packet (questions + required exhibits)
# 5) Runs multi-persona board review (best-effort; never blocks aggregation)

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="big_board_edge_push_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/big_board_edge_push/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

# Tune knobs (override via env)
TRUTH="${TRUTH:-reports/massive_profit_reviews/massive_30d_profit_review_20260225T011830Z/truth_30d.json}"
ITERATIONS="${ITERATIONS:-480}"          # "as much as we can get"
PARALLELISM="${PARALLELISM:-10}"
MIN_TRADES="${MIN_TRADES:-200}"         # strong sample-size pressure
MAX_HOLD_MIN="${MAX_HOLD_MIN:-240}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"
log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== BIG BOARD EDGE PUSH START ==="
log "TRUTH=${TRUTH}"
log "ITERATIONS=${ITERATIONS} PARALLELISM=${PARALLELISM} MIN_TRADES=${MIN_TRADES} MAX_HOLD_MIN=${MAX_HOLD_MIN}"
log "OUT_DIR=${OUT_DIR}"

if [ ! -f "${TRUTH}" ]; then
  log "ERROR: truth file missing: ${TRUTH}"
  exit 1
fi

# ------------------------------------------------------------
# 0) Preconditions: ensure edge discovery script exists
#    Default: CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh
# ------------------------------------------------------------
EDGE_V2_SCRIPT="${EDGE_V2_SCRIPT:-scripts/CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh}"
if [ ! -f "${EDGE_V2_SCRIPT}" ]; then
  log "ERROR: Missing ${EDGE_V2_SCRIPT}."
  log "This run requires the edge discovery script to exist in-repo."
  exit 1
fi

# ------------------------------------------------------------
# 1) Run EDGE DISCOVERY (expanded levers + why packets)
#    Pass TRUTH via TRUTH_30D_PATH for the massive script.
# ------------------------------------------------------------
log "Running EDGE DISCOVERY (massive signal replay + min-trades enforced at aggregate)"
TRUTH_30D_PATH="${TRUTH}" ITERATIONS="${ITERATIONS}" PARALLELISM="${PARALLELISM}" \
bash "${EDGE_V2_SCRIPT}" | tee -a "${LOG}" || true

# Capture the most recent edge_discovery output (signal_replay_edge_discovery_*)
LATEST_V2_DIR="$(ls -1dt reports/edge_discovery/signal_replay_edge_discovery_* 2>/dev/null | head -n 1 || true)"
if [ -z "${LATEST_V2_DIR}" ]; then
  log "ERROR: Could not find reports/edge_discovery/signal_replay_edge_discovery_* output."
  exit 1
fi
log "Detected latest EDGE DISCOVERY output: ${LATEST_V2_DIR}"

# Copy key artifacts into this run's OUT_DIR for board packet cohesion
mkdir -p "${OUT_DIR}/artifacts"
cp -a "${LATEST_V2_DIR}/." "${OUT_DIR}/artifacts/" || true

# Re-aggregate with MIN_TRADES so 0-trade / tiny-sample policies cannot win
log "Re-aggregating with MIN_TRADES=${MIN_TRADES}"
python3 scripts/learning/aggregate_profitability_campaign.py \
  --campaign_dir "${OUT_DIR}/artifacts" \
  --rank_by TOTAL_PNL_AFTER_COSTS \
  --emit_top_n 10 \
  --emit_promotion_payloads \
  --min_trades "${MIN_TRADES}" \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 2) Build Board Review Packet (questions + required exhibits)
# ------------------------------------------------------------
log "Writing board review packet (questions + exhibits)"
cat > "${OUT_DIR}/BOARD_REVIEW_PACKET.md" <<'MD'
# Big board review packet — profitability edge discovery (droplet truth)

## Prime directive
Maximize realized PnL after costs. Nothing else matters.

## Non-negotiables
- Droplet truth only
- No suppression (learn from all symbols/times/directions)
- Sample-size sanity (no 0-trade winners; no tiny-sample "miracles")

## Required exhibits (must be referenced in verdict)
- **Truth dataset:** `truth_30d.json` (window, trades, exits)
- **Labeled moves:** `labeled_moves.json` (up/down move labels)
- **Signal leading stats:** `signal_leading_stats.json`
- **Candidate policies:** `candidate_policies.json`
- **Iteration results:** `iterations/policy_*/iteration_result.json`
- **WHY packets:** `iterations/policy_*/why_packet.json` (if present)
- **Aggregate ranking:** `aggregate_result.json` (min_trades applied)
- **Top promotion payloads (PAPER only):** `promotion_payloads/`

## Board questions (answer all, with evidence)
### A) Where is the bleeding coming from?
- What fraction of loss is explained by **costs/slippage** vs raw move direction?
- Is loss concentrated in certain **symbols**, **times of day**, **volatility regimes**, or **holding times**?

### B) Entry quality
- Which entry signals (or combinations) correlate with **positive forward returns** at 5/15/30/60/120 minutes?
- Which signals correlate with **negative** forward returns (anti-signals)?
- What is the best **entry_min** range that improves expectancy while keeping adequate trade count?

### C) Direction choice (long vs short)
- Under what conditions should we prefer **long** vs **short**?
- Are there signals that flip meaning by direction?
- What direction gating reduces loss the most without collapsing trade count?

### D) Exit logic
- Which exit families improve PnL on the same underlying opportunities?
  - time stop vs fixed brackets vs trailing
- Are winners being cut early or losers held too long?
- What exit parameters are consistently present in the top decile?

### E) Sizing
- Which sizing style reduces drawdown and improves PnL after costs?
  - fixed vs score-scaled vs vol-scaled vs score×vol
- Does sizing amplify noise (more trades, more loss) or amplify edge?

### F) Repeatability and promotion readiness
- Which top candidates remain strong under:
  - stricter min-trades thresholds
  - different move thresholds
  - different holding-time caps
- What are the top 3 PAPER-only promotion candidates and why?

## Required output format
- **Verdict:** 1–3 sentences
- **Top 3 actionable changes:** each with expected impact and risk
- **Top 10 candidate table:** iter_id, trades, pnl_after_costs, win_rate, key params
- **Next run plan:** what to vary next and what to freeze
MD

# ------------------------------------------------------------
# 3) Multi-persona "big board" review (best-effort; never blocks)
#    multi_model_runner.py expects --backtest_dir (with baseline/), --roles, --out
# ------------------------------------------------------------
if [ -f scripts/multi_model_runner.py ]; then
  log "Running multi-persona big board review (best-effort)"
  mkdir -p "${OUT_DIR}/board_review"
  FIRST_POLICY_WITH_BASELINE="$(ls -d "${OUT_DIR}/artifacts"/iterations/policy_* 2>/dev/null | while read -r d; do [ -d "${d}/baseline" ] && echo "$d" && break; done || true)"
  if [ -n "${FIRST_POLICY_WITH_BASELINE}" ]; then
    (python3 scripts/multi_model_runner.py \
      --backtest_dir "${FIRST_POLICY_WITH_BASELINE}" \
      --out "${OUT_DIR}/board_review/multi_model" \
      --roles "prosecutor,defender,sre,board" \
      > "${OUT_DIR}/board_review/multi_model_stdout.txt" 2> "${OUT_DIR}/board_review/multi_model_stderr.txt") || true
  else
    log "No policy iteration with baseline/ found; board review will be manual using BOARD_REVIEW_PACKET.md"
  fi
else
  log "multi_model_runner.py not found; board review will be manual using BOARD_REVIEW_PACKET.md"
fi

# ------------------------------------------------------------
# 4) Final summary
# ------------------------------------------------------------
log "Writing final summary"
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
BIG BOARD EDGE PUSH COMPLETE (DROPLET)

TRUTH: ${TRUTH}
EDGE_DISCOVERY_OUTPUT: ${LATEST_V2_DIR}

RUN CONTROLS:
- ITERATIONS=${ITERATIONS}
- PARALLELISM=${PARALLELISM}
- MIN_TRADES=${MIN_TRADES}
- MAX_HOLD_MIN=${MAX_HOLD_MIN}

BOARD PACKET:
- ${OUT_DIR}/BOARD_REVIEW_PACKET.md

ARTIFACTS (copied for cohesion; aggregate re-run with min_trades):
- ${OUT_DIR}/artifacts/

BOARD REVIEW (best-effort):
- ${OUT_DIR}/board_review/

LOG:
- ${LOG}

DECISION CONTRACT:
- Profitability only
- No suppression
- No 0-trade winners
- Sample-size pressure enforced
EOF

echo "OUT_DIR: ${OUT_DIR}"
log "=== COMPLETE ==="
