#!/usr/bin/env bash
# Run equity governance autopilot in a loop on the droplet until GLOBAL STOPPING CONDITION is met.
# Usage: bash scripts/run_equity_governance_loop_on_droplet.sh
# Log: /tmp/equity_governance_autopilot.log (appended each cycle)

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
cd "${REPO}" || exit 1

CYCLE=0
while true; do
  CYCLE=$((CYCLE + 1))
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] === GOVERNANCE CYCLE ${CYCLE} ==="
  if ! bash scripts/CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Autopilot script failed. Exiting loop."
    exit 1
  fi
  # Check last run for stopping condition (last OUT_DIR is the one just written)
  LAST_OUT="$(ls -td reports/equity_governance/equity_governance_* 2>/dev/null | head -1)"
  if [ -n "${LAST_OUT}" ] && [ -f "${LAST_OUT}/lock_or_revert_decision.json" ]; then
    STOPPING="$(python3 -c "
import json
j=json.load(open('${LAST_OUT}/lock_or_revert_decision.json'))
print(j.get('stopping_condition_met', False))
" 2>/dev/null || echo "False")"
    if [ "${STOPPING}" = "True" ]; then
      echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Stopping condition met. Exiting loop."
      exit 0
    fi
  fi
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Next cycle in 60s..."
  sleep 60
done
