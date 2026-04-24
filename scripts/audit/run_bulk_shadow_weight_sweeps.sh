#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — BULK SHADOW SIGNAL WEIGHT SWEEPS
#
# BOARD-APPROVED SCOPE:
#   Shadow-only bulk optimization of signal weights
#
# PURPOSE:
#   - Run large-scale weight sweeps over historical ledgers
#   - Observe interaction effects and stability
#   - Rank configurations by expectancy and robustness
#
# CONSTRAINTS:
#   - Read-only
#   - No live or paper writes
#   - No auto-promotion
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/shadow/sweeps reports/shadow/rankings

echo "=== PHASE 0: ASSERT SHADOW REPLAY READY ==="
test -f reports/shadow/SHADOW_REPLAY_READY_${DATE}.json || {
  echo "ERROR: Shadow replay harness not ready"
  exit 1
}

echo "=== PHASE 1: GENERATE WEIGHT SWEEP GRID ==="
python3 scripts/shadow/generate_weight_sweep_grid.py \
  --signal-model shadow/config/WEIGHTED_SIGNAL_MODEL.json \
  --weight-range 0.5 1.5 \
  --step 0.1 \
  --max-combinations 1000 \
  --output reports/shadow/sweeps/WEIGHT_SWEEP_GRID_${DATE}.json

echo "=== PHASE 2: RUN SHADOW REPLAY SWEEPS ==="
python3 scripts/shadow/run_shadow_weight_sweeps.py \
  --replay-manifest reports/shadow/SHADOW_REPLAY_READY_${DATE}.json \
  --sweep-grid reports/shadow/sweeps/WEIGHT_SWEEP_GRID_${DATE}.json \
  --metrics realized_pnl drawdown stability turnover \
  --output reports/shadow/sweeps/WEIGHT_SWEEP_RESULTS_${DATE}.json

echo "=== PHASE 3: RANK CONFIGURATIONS ==="
python3 scripts/shadow/rank_weight_configurations.py \
  --results reports/shadow/sweeps/WEIGHT_SWEEP_RESULTS_${DATE}.json \
  --criteria expected_pnl stability drawdown \
  --top-n 10 \
  --output reports/shadow/rankings/WEIGHT_SWEEP_RANKING_${DATE}.json

echo "=== PHASE 4: EMIT PROMOTION SHORTLIST ==="
python3 scripts/shadow/emit_promotion_shortlist.py \
  --ranking reports/shadow/rankings/WEIGHT_SWEEP_RANKING_${DATE}.json \
  --output reports/shadow/PROMOTION_SHORTLIST_${DATE}.json

echo "=== BULK SHADOW WEIGHT OPTIMIZATION COMPLETE ==="
