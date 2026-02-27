#!/usr/bin/env bash
# CURSOR_DROPLET_BIG_BOARD_EDGE_DISCOVERY.sh
#
# PURPOSE:
#   Brutally search for repeatable profitability using REAL droplet data.
#   Replay signals, test entry/exit/direction/sizing combinations,
#   enforce sample-size sanity, and produce a BOARD-GRADE verdict with
#   MULTI-MODEL ADVERSARIAL REVIEW (prosecutor / defender / sre / board).
#
# NON-NEGOTIABLES:
# - DROPLET ONLY (/root/stock-bot)
# - REAL DATA ONLY (truth_30d.json)
# - NO SUPPRESSION (learn from everything)
# - ITERATE HARD (hundreds of scenarios)
# - RANK BY MONEY ONLY
# - MULTI-MODEL ADVERSARIAL: prosecutor (adversarial), defender (pushback), sre, board (synthesis)
#
# THIS BLOCK:
# - Runs massive signal replay + edge discovery
# - Enforces MIN_TRADES so fake winners die
# - Aggregates results correctly
# - Runs multi-model adversarial review on the TOP-RANKED policy (by PnL)
# - Forces a big-board review with explicit questions and required exhibits
# - Never fails the run if one component flakes

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: Must run on droplet"; exit 1; }

RUN_TAG="big_board_edge_discovery_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/big_board_edge_discovery/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

# Controls (override via env)
TRUTH="${TRUTH:-reports/massive_profit_reviews/massive_30d_profit_review_20260225T011830Z/truth_30d.json}"
ITERATIONS="${ITERATIONS:-600}"
PARALLELISM="${PARALLELISM:-10}"
MIN_TRADES="${MIN_TRADES:-300}"

EDGE_SCRIPT="${EDGE_SCRIPT:-scripts/CURSOR_MASSIVE_SIGNAL_REPLAY_AND_EDGE_DISCOVERY.sh}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"
log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== BIG BOARD EDGE DISCOVERY START ==="
log "TRUTH=${TRUTH}"
log "ITERATIONS=${ITERATIONS} PARALLELISM=${PARALLELISM} MIN_TRADES=${MIN_TRADES}"
log "EDGE_SCRIPT=${EDGE_SCRIPT}"
log "OUT_DIR=${OUT_DIR}"

if [ ! -f "${TRUTH}" ]; then
  log "ERROR: truth file missing: ${TRUTH}"
  exit 1
fi
if [ ! -f "${EDGE_SCRIPT}" ]; then
  log "ERROR: edge discovery script missing: ${EDGE_SCRIPT}"
  exit 1
fi

# ------------------------------------------------------------
# 1) Run massive signal replay + edge discovery
#    Edge script expects TRUTH_30D_PATH (not TRUTH).
# ------------------------------------------------------------
log "Running massive signal replay + edge discovery"
TRUTH_30D_PATH="${TRUTH}" ITERATIONS="${ITERATIONS}" PARALLELISM="${PARALLELISM}" \
bash "${EDGE_SCRIPT}" | tee -a "${LOG}" || true

# Find latest edge discovery output
LATEST_EDGE_DIR="$(ls -1dt reports/edge_discovery/signal_replay_edge_discovery_* 2>/dev/null | head -n 1 || true)"
if [ -z "${LATEST_EDGE_DIR}" ]; then
  log "ERROR: Could not find edge discovery output directory"
  exit 1
fi
log "Detected edge discovery output: ${LATEST_EDGE_DIR}"

# Copy artifacts for board cohesion
mkdir -p "${OUT_DIR}/artifacts"
cp -a "${LATEST_EDGE_DIR}/." "${OUT_DIR}/artifacts/" || true

# ------------------------------------------------------------
# 2) Re-aggregate with MIN_TRADES enforced (kills fake winners)
# ------------------------------------------------------------
log "Re-aggregating with MIN_TRADES=${MIN_TRADES}"
python3 scripts/learning/aggregate_profitability_campaign.py \
  --campaign_dir "${OUT_DIR}/artifacts" \
  --rank_by TOTAL_PNL_AFTER_COSTS \
  --min_trades "${MIN_TRADES}" \
  --emit_top_n 10 \
  --emit_promotion_payloads \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 3) Write BIG BOARD REVIEW PACKET (explicit questions)
# ------------------------------------------------------------
log "Writing board review packet"
cat > "${OUT_DIR}/BOARD_REVIEW_PACKET.md" <<'MD'
# Big Board Review — Edge Discovery (Droplet Truth)

## Prime Directive
Maximize realized PnL after costs. Nothing else matters.

## Data Provenance
- 30-day droplet truth (trades, exits, 1m bars)
- No suppression of symbols, times, or directions
- Sample-size enforced (MIN_TRADES)

## Required Exhibits
- truth_30d.json
- labeled_moves.json
- signal_leading_stats.json
- candidate_policies.json
- iterations/*/iteration_result.json
- iterations/*/why_packet.json (if present)
- aggregate_result.json
- promotion_payloads/

## Multi-Model Adversarial Review (mandatory for verdict)
The board verdict MUST consider the adversarial outputs in board_review/:
- **prosecutor_output.md** — adversarial view: failure modes, chokes, no edge
- **defender_output.md** — pushback: alternative causes, validity of run
- **sre_output.md** — evidence and operational view
- **board_verdict.md** — synthesis and decision
Consensus: answer board questions using evidence; cite prosecutor/defender where they disagree.

## Board Questions (Answer with Evidence)
### 1) Where is the loss coming from?
- Costs vs direction vs exit timing vs sizing
- Concentration by symbol, time-of-day, volatility

### 2) Entry signals
- Which signals precede profitable moves?
- Which are anti-signals?
- What entry_min range improves expectancy without killing volume?

### 3) Direction logic
- When should we prefer long vs short?
- Are there signals that flip meaning by direction?

### 4) Exit logic
- Which exit families reduce loss on the same trades?
- Are winners cut early or losers held too long?

### 5) Sizing
- Which sizing styles reduce drawdown and improve PnL?
- Does sizing amplify noise or edge?

### 6) Repeatability
- Which candidates survive higher MIN_TRADES?
- Which patterns repeat across many iterations?

## Required Output
- Verdict (2–3 sentences)
- Top 3 concrete changes to test next
- Top 10 candidate table (iter_id, trades, pnl, win_rate, key params)
- Next iteration plan (what to freeze, what to vary)
MD

# ------------------------------------------------------------
# 4) Multi-model adversarial review (best-effort; never blocks)
#    Run on the TOP-RANKED policy (by PnL after min_trades) so the board
#    sees adversarial critique of the best candidate.
#    multi_model_runner expects backtest_dir to contain baseline/.
# ------------------------------------------------------------
if [ -f scripts/multi_model_runner.py ]; then
  log "Running multi-model adversarial review (prosecutor, defender, sre, board)"
  mkdir -p "${OUT_DIR}/board_review"
  TOP_POLICY_DIR=""
  if [ -f "${OUT_DIR}/artifacts/aggregate_result.json" ]; then
    FIRST_ITER_ID="$(python3 -c 'import json; d=json.load(open("'"${OUT_DIR}"'/artifacts/aggregate_result.json")); t=d.get("top_n") or []; print(t[0].get("iter_id","") if t else "")' 2>/dev/null || true)"
    if [ -n "${FIRST_ITER_ID}" ] && [ -d "${OUT_DIR}/artifacts/iterations/${FIRST_ITER_ID}" ] && [ -d "${OUT_DIR}/artifacts/iterations/${FIRST_ITER_ID}/baseline" ]; then
      TOP_POLICY_DIR="${OUT_DIR}/artifacts/iterations/${FIRST_ITER_ID}"
      log "Adversarial review target: top-ranked policy ${FIRST_ITER_ID}"
    fi
  fi
  if [ -z "${TOP_POLICY_DIR}" ]; then
    for d in "${OUT_DIR}/artifacts"/iterations/policy_*; do
      [ -d "$d" ] && [ -d "${d}/baseline" ] && { TOP_POLICY_DIR="$d"; log "Adversarial review target: fallback $d"; break; }
    done
  fi
  if [ -n "${TOP_POLICY_DIR}" ]; then
    (python3 scripts/multi_model_runner.py \
      --backtest_dir "${TOP_POLICY_DIR}" \
      --out "${OUT_DIR}/board_review" \
      --roles "prosecutor,defender,sre,board" \
      > "${OUT_DIR}/board_review/stdout.txt" 2> "${OUT_DIR}/board_review/stderr.txt") || true
    log "Multi-model adversarial outputs: board_review/prosecutor_output.md, defender_output.md, sre_output.md, board_verdict.md"
  else
    log "No policy iteration with baseline/ found; manual board review required"
  fi
else
  log "multi_model_runner.py not found; manual board review required"
fi

# ------------------------------------------------------------
# 5) Final summary
# ------------------------------------------------------------
log "Writing final summary"
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
BIG BOARD EDGE DISCOVERY COMPLETE

TRUTH:
- ${TRUTH}

EDGE DISCOVERY:
- Source: ${LATEST_EDGE_DIR}
- Iterations: ${ITERATIONS}
- Parallelism: ${PARALLELISM}
- MIN_TRADES enforced: ${MIN_TRADES}

ARTIFACTS:
- ${OUT_DIR}/artifacts/
- ${OUT_DIR}/BOARD_REVIEW_PACKET.md
- ${OUT_DIR}/board_review/ (multi-model adversarial: prosecutor_output.md, defender_output.md, sre_output.md, board_verdict.md)

DECISION CONTRACT:
- Profitability only
- No suppression
- No fake winners
- Evidence over intuition
- Verdict must consider multi-model adversarial review (prosecutor vs defender, board synthesis)

LOG:
- ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
log "=== COMPLETE ==="
