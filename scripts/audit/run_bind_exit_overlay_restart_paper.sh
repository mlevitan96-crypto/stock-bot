#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — BIND EXIT OVERLAY AND RESTART PAPER ENGINE
#
# PURPOSE:
#   - Make the exit aggression overlay live in the paper engine
#   - Restart under governance control
#   - Confirm the engine is running with the new behavior
#
# CONSTRAINTS:
#   - Paper-only
#   - Entries unchanged
#   - CI unchanged
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

export MODE=PAPER
export GOVERNED_TUNING_CONFIG=config/overlays/exit_aggression_paper.json

mkdir -p reports/runtime

echo "=== PHASE 0: VERIFY OVERLAY EXISTS ==="
test -f "${GOVERNED_TUNING_CONFIG}" || {
  echo "ERROR: Exit aggression overlay not found"
  exit 1
}

echo "=== PHASE 1: ACTIVATE OVERLAY FOR PAPER ENGINE ==="
python3 scripts/runtime/set_active_tuning_config.py \
  --mode paper \
  --config "${GOVERNED_TUNING_CONFIG}" \
  --output reports/runtime/ACTIVE_TUNING_CONFIG_${DATE}.json

echo "=== PHASE 2: RESTART PAPER ENGINE ==="
python3 scripts/runtime/restart_paper_engine.py \
  --mode paper \
  --reason "Activate exit aggression promotion ${DATE}"

echo "=== PHASE 3: VERIFY ENGINE STATE ==="
python3 scripts/runtime/verify_engine_state.py \
  --mode paper \
  --expect-overlay "${GOVERNED_TUNING_CONFIG}" \
  --output reports/runtime/PAPER_ENGINE_VERIFIED_${DATE}.json

echo "=== EXIT AGGRESSION NOW LIVE IN PAPER ==="
