#!/usr/bin/env bash
# CURSOR_DROPLET_PERCENT_MOVE_INTELLIGENCE.sh
#
# PURPOSE:
#   Learn from PRICE MOVEMENT FIRST.
#   Extract entry and exit intelligence by correlating signals
#   BEFORE and AFTER significant percent moves.
#
# X (move thresholds): MOVE_PCTS — we label +X% / -X% moves for each threshold.
#   Goal = profitability: we can ENTER after stock is already up a little when
#   the signal hits and more move is likely (e.g. enter on signal after +0.5%,
#   capture the next +2%). We also learn when to EXIT (exhaustion vs continuation).
#
# THIS BLOCK:
# - Uses real 30d droplet truth
# - Labels +X% / -X% moves (X from MOVE_PCTS)
# - Correlates signals in lookback windows (entry intelligence)
# - Correlates outcomes in lookahead windows (exit vs continuation)
# - Produces board-grade intelligence artifacts
#
# NO POLICY RANKING. NO PROMOTION.
# THIS IS PURE LEARNING.

set -euo pipefail

REPO="/root/stock-bot"
cd "${REPO}" || exit 1
[ -d "/root/stock-bot" ] || { echo "ERROR: droplet only"; exit 1; }

RUN_TAG="percent_move_intelligence_$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="reports/percent_move_intelligence/${RUN_TAG}"
LOG="/tmp/${RUN_TAG}.log"

TRUTH_30D_PATH="${TRUTH_30D_PATH:-reports/massive_profit_reviews/massive_30d_profit_review_20260225T011830Z/truth_30d.json}"

# X = move % thresholds we learn from (e.g. 0.5=small, 2.0=meaningful, 3.0=big)
MOVE_PCTS="${MOVE_PCTS:-0.5,1.0,1.5,2.0,3.0}"
LOOKBACK_MINUTES="${LOOKBACK_MINUTES:-5,15,30,60,120}"
LOOKAHEAD_MINUTES="${LOOKAHEAD_MINUTES:-5,15,30,60,120}"

mkdir -p "${OUT_DIR}"
: > "${LOG}"
log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

log "=== PERCENT MOVE INTELLIGENCE START ==="
log "TRUTH=${TRUTH_30D_PATH}"
log "MOVE_PCTS=${MOVE_PCTS} (X thresholds)"
log "LOOKBACK_MINUTES=${LOOKBACK_MINUTES}"
log "LOOKAHEAD_MINUTES=${LOOKAHEAD_MINUTES}"
log "OUT_DIR=${OUT_DIR}"

[ -f "${TRUTH_30D_PATH}" ] || { log "ERROR: truth missing"; exit 1; }

# ------------------------------------------------------------
# 1) Label significant price moves (+X% / -X% for each X in MOVE_PCTS)
# ------------------------------------------------------------
log "Labeling +X% / -X% moves"
python3 scripts/analysis/label_large_moves.py \
  --truth "${TRUTH_30D_PATH}" \
  --move_pcts "${MOVE_PCTS}" \
  --lookahead_minutes "${LOOKAHEAD_MINUTES}" \
  --out "${OUT_DIR}/labeled_moves.json" \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 2) Correlate signals BEFORE moves (entry intelligence)
# ------------------------------------------------------------
log "Correlating signals before moves (entry intelligence)"
python3 scripts/analysis/correlate_signals_before_moves.py \
  --truth "${TRUTH_30D_PATH}" \
  --labeled_moves "${OUT_DIR}/labeled_moves.json" \
  --lookback_minutes "${LOOKBACK_MINUTES}" \
  --out "${OUT_DIR}/signal_pre_move_intelligence.json" \
  --no_suppression \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 3) Correlate outcomes AFTER moves (exit vs continuation)
# ------------------------------------------------------------
log "Correlating outcomes after moves (exit intelligence)"
python3 scripts/analysis/correlate_signals_after_moves.py \
  --truth "${TRUTH_30D_PATH}" \
  --labeled_moves "${OUT_DIR}/labeled_moves.json" \
  --lookahead_minutes "${LOOKAHEAD_MINUTES}" \
  --out "${OUT_DIR}/signal_post_move_intelligence.json" \
  --no_suppression \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 4) Build entry/exit intelligence tables
# ------------------------------------------------------------
log "Building entry/exit intelligence"
python3 scripts/analysis/build_entry_exit_intelligence.py \
  --pre "${OUT_DIR}/signal_pre_move_intelligence.json" \
  --post "${OUT_DIR}/signal_post_move_intelligence.json" \
  --out "${OUT_DIR}/entry_exit_intelligence.json" \
  | tee -a "${LOG}" || true

# ------------------------------------------------------------
# 5) Board review packet
# ------------------------------------------------------------
log "Writing board review packet"
cat > "${OUT_DIR}/BOARD_REVIEW_PACKET.md" <<'MD'
# Board Review — Percent Move Intelligence

## Objective
Learn how to:
- Enter BEFORE meaningful price moves (or enter after small move when signal says more is coming)
- Exit when moves are exhausted
- Let winners run when continuation is likely

## X (move thresholds)
We label moves at +X% / -X% for X in MOVE_PCTS. Use this to see which signals precede which size move.

## Questions
1. Which signals precede +X% moves?
2. Which signals precede −X% moves?
3. Which signals indicate exhaustion after a move?
4. Which indicate continuation?
5. What entry rules are implied? (Including: enter on signal after +0.5% to capture next leg?)
6. What exit rules are implied?

## Exhibits
- labeled_moves.json
- signal_pre_move_intelligence.json
- signal_post_move_intelligence.json
- entry_exit_intelligence.json
MD

# ------------------------------------------------------------
# 6) Final summary
# ------------------------------------------------------------
log "Writing final summary"
cat > "${OUT_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
PERCENT MOVE INTELLIGENCE COMPLETE

TRUTH:
- ${TRUTH_30D_PATH}

X (move thresholds): ${MOVE_PCTS}
LOOKBACK: ${LOOKBACK_MINUTES} min
LOOKAHEAD: ${LOOKAHEAD_MINUTES} min

OUTPUTS:
- labeled_moves.json
- signal_pre_move_intelligence.json
- signal_post_move_intelligence.json
- entry_exit_intelligence.json
- BOARD_REVIEW_PACKET.md

NEXT STEP:
- Use entry_exit_intelligence.json to CONSTRAIN policy generation
- Then re-run edge discovery with those constraints frozen

LOG:
- ${LOG}
EOF

echo "OUT_DIR: ${OUT_DIR}"
log "=== COMPLETE ==="
