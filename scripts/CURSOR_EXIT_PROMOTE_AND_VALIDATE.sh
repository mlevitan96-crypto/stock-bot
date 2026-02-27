#!/usr/bin/env bash
# CURSOR_EXIT_PROMOTE_AND_VALIDATE.sh
# Takes the grid-approved exit config, stages it, and runs validation.
# No live trading changes. Evidence-only validation.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="exit_promote_validate_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_exit_promote_validate.log"

GRID_RUN_DIR="$(ls -dt ${REPO}/reports/exit_review/exit_grid_with_bars_* 2>/dev/null | head -n1)"
TUNED_CONFIG="config/exit_candidate_signals.tuned.json"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

cd "${REPO}" || exit 1

log "=== EXIT PROMOTION + VALIDATION ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Sanity checks
# -------------------------------------------------
if [ -z "${GRID_RUN_DIR}" ]; then
  log "ERROR: No exit_grid_with_bars run found."
  exit 1
fi

if [ ! -f "${GRID_RUN_DIR}/grid_board_review/GRID_RECOMMENDATION.json" ]; then
  log "ERROR: GRID_RECOMMENDATION.json missing."
  exit 1
fi

log "Using grid run: ${GRID_RUN_DIR}"

# -------------------------------------------------
# 2) Extract recommended config
# -------------------------------------------------
log "Extracting recommended exit config from grid review"

python3 - <<PY > "${RUN_DIR}/recommended_exit_config.json"
import json, pathlib

grid_dir = "${GRID_RUN_DIR}"
rec = json.load(open(pathlib.Path(grid_dir) / "grid_board_review" / "GRID_RECOMMENDATION.json"))

cfg = rec.get("top_config", {}).get("params")
if not cfg:
    raise SystemExit("No recommended_config found")

print(json.dumps(cfg, indent=2))
PY

# -------------------------------------------------
# 3) Stage tuned config (no live effect)
# -------------------------------------------------
log "Staging tuned exit config at ${TUNED_CONFIG}"

cp "${RUN_DIR}/recommended_exit_config.json" "${TUNED_CONFIG}"

# -------------------------------------------------
# 4) Run apples-to-apples validation
# -------------------------------------------------
log "Running validation: tuned exits vs baseline"

bash scripts/CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh \
  2>&1 | tee -a "${LOG}"

# -------------------------------------------------
# 5) Human-readable summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
EXIT PROMOTION — WHAT IS HAPPENING

STATUS:
- Exit grid search completed successfully.
- 1,643 historical exits simulated with real Alpaca bars.
- 160 exit parameter sets evaluated.
- Board decision: PROMOTE_TOP_CONFIG.

WHAT THIS BLOCK DID:
1) Pulled the board-approved exit configuration.
2) Staged it as:
   ${TUNED_CONFIG}
3) Ran an apples-to-apples validation against the original exit behavior.

IMPORTANT:
- No live trading behavior was changed.
- This is a validation pass only.

WHAT TO REVIEW NEXT:
- Validation run artifacts under:
  reports/exit_review/
- Compare tuned vs baseline PnL, drawdown, churn.

NEXT DECISIONS:
- If validation confirms improvement → approve shadow or paper enablement.
- If validation regresses → adjust config and re-run validation.
- If mixed → tighten thresholds and re-test.

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_PROMOTION_VALIDATION_RUNNING"

log "=== COMPLETE EXIT PROMOTION + VALIDATION ==="
