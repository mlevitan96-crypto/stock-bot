#!/usr/bin/env bash
# CURSOR_EXIT_EDGE_DISCOVERY_REVIEW.sh
# Evidence-only. No behavior changes. No flags flipped.
# Requires CTR live with fresh data.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
CTR_ROOT="${STOCKBOT_TRUTH_ROOT:-/var/lib/stock-bot/truth}"
RUN_TAG="exit_edge_review_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/edge_${RUN_TAG}"
LOG="/tmp/cursor_exit_edge_review.log"

START_DATE="${START_DATE:-2025-12-01}"
END_DATE="${END_DATE:-2026-02-23}"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found"

log "=== START EXIT EDGE DISCOVERY ${RUN_TAG} ==="
log "Window: ${START_DATE} → ${END_DATE}"
log "CTR_ROOT: ${CTR_ROOT}"

# -------------------------------------------------
# 1) Preconditions — CTR truth must be fresh
# -------------------------------------------------
for f in \
  "${CTR_ROOT}/exits/exit_truth.jsonl" \
  "${CTR_ROOT}/gates/expectancy.jsonl" \
  "${CTR_ROOT}/health/signal_health.jsonl"
do
  [ -f "${f}" ] || fail "Missing CTR stream: ${f}"
done

# -------------------------------------------------
# 2) Rebuild historical exits (authoritative)
# -------------------------------------------------
log "Rebuilding historical exits from CTR"

python3 scripts/analysis/rebuild_exit_history_from_ctr.py \
  --ctr_root "${CTR_ROOT}" \
  --start "${START_DATE}" \
  --end "${END_DATE}" \
  --out "${RUN_DIR}/historical_exits.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 3) Replay exits against candidate exit signals
# -------------------------------------------------
log "Replaying exits against candidate exit signals"

python3 scripts/analysis/replay_exits_with_candidate_signals.py \
  --historical "${RUN_DIR}/historical_exits.json" \
  --ctr_root "${CTR_ROOT}" \
  --out "${RUN_DIR}/exit_replay_results.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 4) Compute edge metrics (baseline vs candidates)
# -------------------------------------------------
log "Computing edge metrics"

python3 scripts/analysis/compute_exit_edge_metrics.py \
  --replay "${RUN_DIR}/exit_replay_results.json" \
  --out_json "${RUN_DIR}/exit_edge_metrics.json" \
  --out_md "${RUN_DIR}/exit_edge_metrics.md" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 5) Regime-conditional analysis
# -------------------------------------------------
log "Running regime-conditional exit analysis"

python3 scripts/analysis/exit_edge_by_regime.py \
  --edge "${RUN_DIR}/exit_edge_metrics.json" \
  --out "${RUN_DIR}/exit_edge_by_regime.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 6) Board synthesis (multi-persona)
# -------------------------------------------------
log "Running multi-persona board synthesis"

python3 scripts/analysis/exit_edge_board_review.py \
  --roles prosecutor,defender,quant,sre,board \
  --evidence "${RUN_DIR}" \
  --out "${RUN_DIR}/board_review" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 7) Final board decision
# -------------------------------------------------
log "Synthesizing board decision"

python3 scripts/analysis/synthesize_exit_edge_decision.py \
  --edge "${RUN_DIR}/exit_edge_metrics.json" \
  --regime "${RUN_DIR}/exit_edge_by_regime.json" \
  --board "${RUN_DIR}/board_review" \
  --out "${RUN_DIR}/BOARD_DECISION.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 8) Copy/paste summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}
WINDOW: ${START_DATE} → ${END_DATE}

ARTIFACTS:
- historical_exits.json
- exit_replay_results.json
- exit_edge_metrics.{json,md}
- exit_edge_by_regime.json
- board_review/
- BOARD_DECISION.json

WHAT THIS ANSWERS:
- Which exit signals would have reduced giveback?
- Which would have saved losses earlier?
- Which increase tail risk?
- Which only work in specific regimes?

NEXT ACTIONS:
- If BOARD_DECISION = PROMOTE → enable EXIT_PRESSURE_ENABLED=1 in test env.
- If TUNE → apply config-only patch and re-run this block.
- If HOLD → no behavior change; data retained.

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_EDGE_REVIEW_COMPLETE"
echo "PR_BRANCH: NONE"

log "=== COMPLETE EXIT EDGE DISCOVERY ==="
