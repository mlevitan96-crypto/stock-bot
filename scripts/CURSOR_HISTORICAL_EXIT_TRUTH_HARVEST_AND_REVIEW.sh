#!/usr/bin/env bash
# CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh
# Massive historical exit review using legacy data.
# Evidence-only. No CTR dependency. No behavior changes.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="historical_exit_review_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/historical_${RUN_TAG}"
LOG="/tmp/cursor_historical_exit_review.log"

START_DATE="${START_DATE:-2025-10-01}"
END_DATE="${END_DATE:-2026-02-23}"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }
fail(){ log "ERROR: $*"; exit 1; }

cd "${REPO}" || fail "Repo not found"

log "=== START HISTORICAL EXIT REVIEW ${RUN_TAG} ==="
log "Window: ${START_DATE} → ${END_DATE}"

# -------------------------------------------------
# 1) Discover historical exit-relevant sources
# -------------------------------------------------
log "Discovering historical exit data sources"

python3 scripts/analysis/discover_exit_data_sources.py \
  --repo "${REPO}" \
  --out "${RUN_DIR}/exit_data_sources.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 2) Harvest historical exit truth
# -------------------------------------------------
log "Harvesting historical exit truth from legacy sources"

python3 scripts/analysis/harvest_historical_exit_truth.py \
  --sources "${RUN_DIR}/exit_data_sources.json" \
  --start "${START_DATE}" \
  --end "${END_DATE}" \
  --out "${RUN_DIR}/historical_exit_truth.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 3) Normalize + annotate provenance
# -------------------------------------------------
log "Normalizing exit truth and annotating provenance"

python3 scripts/analysis/normalize_exit_truth_with_provenance.py \
  --in "${RUN_DIR}/historical_exit_truth.json" \
  --out "${RUN_DIR}/normalized_exit_truth.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 4) Replay exits against candidate exit signals
# -------------------------------------------------
log "Replaying exits against candidate exit signals"

REPLAY_EXTRA=""
if [ -n "${EXIT_SIGNAL_CONFIG:-}" ] && [ -f "${EXIT_SIGNAL_CONFIG}" ]; then
  REPLAY_EXTRA="--config ${EXIT_SIGNAL_CONFIG}"
fi

python3 scripts/analysis/replay_exits_with_candidate_signals.py \
  --historical "${RUN_DIR}/normalized_exit_truth.json" \
  --out "${RUN_DIR}/exit_replay_results.json" \
  ${REPLAY_EXTRA} \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 5) Compute edge metrics
# -------------------------------------------------
log "Computing exit edge metrics"

python3 scripts/analysis/compute_exit_edge_metrics.py \
  --replay "${RUN_DIR}/exit_replay_results.json" \
  --out_json "${RUN_DIR}/exit_edge_metrics.json" \
  --out_md "${RUN_DIR}/exit_edge_metrics.md" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 6) Regime-conditional analysis
# -------------------------------------------------
log "Running regime-conditional analysis"

python3 scripts/analysis/exit_edge_by_regime.py \
  --edge "${RUN_DIR}/exit_edge_metrics.json" \
  --out "${RUN_DIR}/exit_edge_by_regime.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 7) Multi-model adversarial board review
# -------------------------------------------------
log "Running multi-persona board review"

python3 scripts/analysis/exit_edge_board_review.py \
  --evidence "${RUN_DIR}" \
  --out "${RUN_DIR}/board_review" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 8) Final board decision
# -------------------------------------------------
log "Synthesizing board decision"

python3 scripts/analysis/synthesize_exit_edge_decision.py \
  --edge "${RUN_DIR}/exit_edge_metrics.json" \
  --regime "${RUN_DIR}/exit_edge_by_regime.json" \
  --board "${RUN_DIR}/board_review" \
  --out "${RUN_DIR}/BOARD_DECISION.json" \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 9) Summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
RUN_TAG: ${RUN_TAG}
WINDOW: ${START_DATE} → ${END_DATE}

DATA:
- exit_data_sources.json (discovered legacy truth)
- historical_exit_truth.json (raw harvest)
- normalized_exit_truth.json (review corpus)

ANALYSIS:
- exit_replay_results.json
- exit_edge_metrics.{json,md}
- exit_edge_by_regime.json

GOVERNANCE:
- board_review/
- BOARD_DECISION.json

NEXT:
- If PROMOTE → implement exit pressure logic using CTR going forward
- If TUNE → adjust candidate signals and re-run
- If HOLD → no behavior change

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: HISTORICAL_EXIT_REVIEW_COMPLETE"

log "=== COMPLETE HISTORICAL EXIT REVIEW ==="
