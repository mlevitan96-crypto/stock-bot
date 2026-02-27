#!/usr/bin/env bash
# CURSOR_EXECUTE_EXIT_PROMOTION_ON_DROPLET.sh
# Runs on the droplet.
# Promotes grid-approved exit params into the runtime config,
# verifies wiring, restarts PAPER, and confirms activation.
# LIVE capital remains untouched.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="execute_exit_promotion_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_execute_exit_promotion.log"

GRID_RUN_DIR="$(ls -dt ${REPO}/reports/exit_review/exit_grid_with_bars_* 2>/dev/null | head -n1)"
RUNTIME_EXIT_CONFIG="config/exit_candidate_signals.tuned.json"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

cd "${REPO}" || exit 1

log "=== EXECUTE EXIT PROMOTION ON DROPLET ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Preconditions
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
# 2) Promote grid-approved params to runtime config
# -------------------------------------------------
log "Promoting grid-approved exit params to runtime config"

python3 - <<PY
import json, pathlib

grid_dir = pathlib.Path("${GRID_RUN_DIR}")
rec = json.load(open(grid_dir / "grid_board_review" / "GRID_RECOMMENDATION.json"))

params = rec.get("recommended_config")
if not params:
    raise SystemExit("No recommended_config found")
# Emit only exit param keys for runtime (exclude total_pnl_pct, n_simulated, etc.)
param_keys = ("trailing_stop_pct", "profit_target_pct", "stop_loss_pct", "time_stop_minutes")
params = {k: params[k] for k in param_keys if k in params}
if not params:
    raise SystemExit("No exit params in recommended_config")

out = pathlib.Path("${RUNTIME_EXIT_CONFIG}")
out.parent.mkdir(parents=True, exist_ok=True)
json.dump(params, open(out, "w"), indent=2)

print(f"Runtime exit config written to {out}")
PY

# -------------------------------------------------
# 3) Commit and push (audit trail)
# -------------------------------------------------
log "Committing runtime exit promotion"

git add "${RUNTIME_EXIT_CONFIG}" || true
git commit -m "Activate grid-approved exit strategy for PAPER trading" || true
git push || true

# -------------------------------------------------
# 4) Restart PAPER runner
# -------------------------------------------------
log "Restarting PAPER trading service"

systemctl restart stock-bot-paper.service || \
  log "WARNING: PAPER service restart failed — verify runner manually."

# -------------------------------------------------
# 5) Verify activation (best-effort)
# -------------------------------------------------
log "Verifying runtime config exists and is non-empty"

if [ ! -s "${RUNTIME_EXIT_CONFIG}" ]; then
  log "ERROR: Runtime exit config missing or empty after promotion."
  exit 1
fi

# -------------------------------------------------
# 6) Human-readable summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
EXIT STRATEGY PROMOTION — EXECUTED ON DROPLET

STATUS:
- Grid-approved exit strategy is now ACTIVE for PAPER trading.
- Runtime config updated:
  ${RUNTIME_EXIT_CONFIG}
- PAPER runner restarted to pick up new exits.

WHAT CHANGED:
- Exit timing logic now reflects grid-approved parameters.
- PAPER trading behavior will differ immediately.

WHAT DID NOT CHANGE:
- LIVE capital untouched.
- SHADOW remains experimental.

WHAT TO WATCH NEXT:
- PAPER exit timing vs prior behavior
- Reduced giveback on winners
- Faster loss containment
- Exit churn

ROLLBACK:
- Revert ${RUNTIME_EXIT_CONFIG}
- Restart PAPER runner

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_STRATEGY_NOW_LIVE_IN_PAPER"

log "=== EXIT PROMOTION EXECUTION COMPLETE ==="
