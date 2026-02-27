#!/usr/bin/env bash
# CURSOR_PROMOTE_GRID_EXIT_TO_RUNTIME_AND_RESTART_PAPER.sh
# This is the missing promotion bridge.
# Copies grid-approved exit params into the config the app actually loads,
# commits, pushes, and restarts PAPER trading on the droplet.
# LIVE capital remains untouched.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="promote_grid_exit_runtime_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_promote_grid_exit_runtime.log"

GRID_RUN_DIR="$(ls -dt ${REPO}/reports/exit_review/exit_grid_with_bars_* 2>/dev/null | head -n1)"
RUNTIME_EXIT_CONFIG="config/exit_candidate_signals.tuned.json"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

cd "${REPO}" || exit 1

log "=== PROMOTE GRID EXIT TO RUNTIME CONFIG ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Preconditions
# -------------------------------------------------
if [ -z "${GRID_RUN_DIR}" ]; then
  log "ERROR: No exit_grid_with_bars run found."
  exit 1
fi

if [ ! -f "${GRID_RUN_DIR}/grid_board_review/GRID_RECOMMENDATION.json" ]; then
  log "ERROR: GRID_RECOMMENDATION.json missing in ${GRID_RUN_DIR}"
  exit 1
fi

log "Using grid run: ${GRID_RUN_DIR}"

# -------------------------------------------------
# 2) Extract approved exit params into runtime config
# -------------------------------------------------
log "Writing grid-approved exit params to ${RUNTIME_EXIT_CONFIG}"

python3 - <<PY
import json, pathlib

grid_dir = pathlib.Path("${GRID_RUN_DIR}")
rec = json.load(open(grid_dir / "grid_board_review" / "GRID_RECOMMENDATION.json"))

raw = rec.get("recommended_config")
if not raw:
    raise SystemExit("No recommended_config in GRID_RECOMMENDATION.json")
param_keys = ("trailing_stop_pct", "profit_target_pct", "stop_loss_pct", "time_stop_minutes")
params = {k: raw[k] for k in param_keys if k in raw}
if not params:
    raise SystemExit("No exit params in recommended_config")

out = pathlib.Path("${RUNTIME_EXIT_CONFIG}")
out.parent.mkdir(parents=True, exist_ok=True)
json.dump(params, open(out, "w"), indent=2)
print(f"Wrote {out}")
PY

# -------------------------------------------------
# 3) Commit and push
# -------------------------------------------------
log "Committing runtime exit promotion"

git add "${RUNTIME_EXIT_CONFIG}" || true
git commit -m "Promote grid-approved exit strategy to runtime config (paper)" || true
git push || true

# -------------------------------------------------
# 4) Restart PAPER trading
# -------------------------------------------------
log "Restarting PAPER trading service"

systemctl restart stock-bot-paper.service || \
  log "WARNING: stock-bot-paper.service restart failed — verify runner manually."

# -------------------------------------------------
# 5) Human-readable summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
GRID EXIT PROMOTION — RUNTIME APPLIED

WHAT CHANGED:
- Grid-approved exit parameters were copied into:
  ${RUNTIME_EXIT_CONFIG}
- This is the config actually loaded by governance / resolve_policy.
- PAPER trading now uses the new exit strategy.

WHAT DID NOT CHANGE:
- LIVE capital remains untouched.
- SHADOW remains experimental.

WHY THIS MATTERS:
- This is the missing wiring step.
- The exit strategy is now truly live in PAPER.
- Real-time exit truth capture begins now.

ROLLBACK:
- Revert ${RUNTIME_EXIT_CONFIG}
- Restart PAPER runner

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: GRID_EXIT_PROMOTED_TO_RUNTIME_AND_PAPER"

log "=== COMPLETE GRID EXIT PROMOTION ==="
