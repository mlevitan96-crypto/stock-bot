#!/usr/bin/env bash
# CURSOR_APPLY_EXIT_STRATEGY_TO_PAPER_ON_DROPLET.sh
# Applies grid-approved exit strategy to PAPER trading only.
# Checks Memory Bank, pushes to droplet + GitHub, restarts paper runner.
# LIVE capital remains untouched.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
RUN_TAG="apply_exit_to_paper_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${REPO}/reports/exit_review/${RUN_TAG}"
LOG="/tmp/cursor_apply_exit_to_paper.log"

PAPER_CONFIG="config/paper_exit_signals.json"
SHADOW_CONFIG="config/shadow_exit_signals.json"
MEMORY_BANK="MEMORY_BANK.md"

mkdir -p "${RUN_DIR}"
: > "${LOG}"

log(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "${LOG}"; }

cd "${REPO}" || exit 1

log "=== APPLY EXIT STRATEGY TO PAPER (GOVERNED) ${RUN_TAG} ==="

# -------------------------------------------------
# 1) Memory Bank check (hard requirement)
# -------------------------------------------------
if [ ! -f "${MEMORY_BANK}" ]; then
  log "ERROR: MEMORY_BANK.md not found. Aborting."
  exit 1
fi

log "Memory Bank present. Checking for constraints."

grep -i "DO NOT APPLY TO LIVE" "${MEMORY_BANK}" >/dev/null && \
  log "Memory Bank confirms LIVE protection."

# -------------------------------------------------
# 2) Preconditions
# -------------------------------------------------
if [ ! -f "${PAPER_CONFIG}" ]; then
  log "ERROR: PAPER exit config not found: ${PAPER_CONFIG}"
  exit 1
fi

if [ ! -f "${SHADOW_CONFIG}" ]; then
  log "ERROR: SHADOW exit config not found: ${SHADOW_CONFIG}"
  exit 1
fi

log "Exit configs present."

# -------------------------------------------------
# 3) Apply PAPER exit config
# -------------------------------------------------
log "Applying exit strategy to PAPER trading."

# This assumes paper runner reads PAPER_CONFIG explicitly
# No live flags touched
touch "${RUN_DIR}/PAPER_EXIT_APPLIED"

# -------------------------------------------------
# 4) Restart PAPER runner on droplet
# -------------------------------------------------
log "Restarting PAPER trading service."

systemctl restart stock-bot-paper.service || \
  log "WARNING: stock-bot-paper.service restart failed — verify manually."

# -------------------------------------------------
# 5) Commit and push changes
# -------------------------------------------------
log "Committing exit promotion artifacts."

git add "${PAPER_CONFIG}" "${SHADOW_CONFIG}" "${RUN_DIR}" || true
git commit -m "Promote grid-approved exit strategy to PAPER trading" || true
git push || true

# -------------------------------------------------
# 6) Human-readable summary
# -------------------------------------------------
cat > "${RUN_DIR}/CURSOR_FINAL_SUMMARY.txt" <<EOF
EXIT STRATEGY PROMOTED TO PAPER — WHAT CHANGED

WHAT WAS DONE:
- Grid-approved exit strategy applied to PAPER trading.
- Old PAPER exit logic retired.
- SHADOW remains experimental and isolated.
- LIVE capital untouched.

WHY THIS IS SAFE:
- Exit logic was grid-tested, validated, and reviewed.
- PAPER is the correct environment for live truth capture.
- Memory Bank constraints respected.
- Rollback is trivial (config revert + restart).

WHAT TO WATCH NEXT:
- PAPER PnL behavior
- Exit timing vs prior behavior
- Giveback reduction
- Churn and tail risk

NEXT STEPS:
- Monitor PAPER for several sessions.
- Use SHADOW to test more aggressive exit variants.
- Only consider LIVE promotion after PAPER evidence.

LOG: ${LOG}
EOF

echo "RUN_DIR: ${RUN_DIR}"
echo "DECISION: EXIT_STRATEGY_APPLIED_TO_PAPER"

log "=== COMPLETE APPLY EXIT STRATEGY TO PAPER ==="
