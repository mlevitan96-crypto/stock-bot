#!/usr/bin/env bash
# CURSOR_RUN_EXIT_PROMOTION_NOW.sh
# Final execution step.
# Runs the existing promotion script on the droplet to make
# the grid-approved exit strategy live in PAPER trading.

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
SCRIPT="scripts/CURSOR_EXECUTE_EXIT_PROMOTION_ON_DROPLET.sh"

cd "${REPO}" || exit 1

echo "=== RUNNING EXIT PROMOTION ON DROPLET ==="

if [ ! -f "${SCRIPT}" ]; then
  echo "ERROR: Promotion script not found: ${SCRIPT}"
  exit 1
fi

echo "Executing promotion script..."
bash "${SCRIPT}"

echo "=== EXIT STRATEGY PROMOTION COMPLETE ==="
echo "STATUS: PAPER trading now uses grid-approved exits"
echo "LIVE capital remains untouched"
