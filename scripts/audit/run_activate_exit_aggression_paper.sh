#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — ACTIVATE EXIT AGGRESSION (PAPER)
#
# PURPOSE:
#   - Apply the approved exit_weight:+0.15 change to the paper engine
#   - Enforce max loss and timebox
#   - Begin live evaluation immediately
#
# CONSTRAINTS:
#   - Paper-only
#   - Entries unchanged
#   - CI unchanged
#   - Auto-revert on breach or expiry
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

export MODE=PAPER
export EXIT_WEIGHT_DELTA=0.15
export MAX_LOSS_USD=25
export DURATION_HOURS=48

mkdir -p reports/runtime reports/audit

echo "=== PHASE 0: LOAD PROMOTION RECORD ==="
python3 scripts/runtime/load_promotion.py \
  --promotion reports/promotions/EXIT_AGGRESSION_PROMOTION_${DATE}.json \
  --assert-active \
  --output reports/runtime/ACTIVE_PROMOTION_${DATE}.json

echo "=== PHASE 1: APPLY EXIT WEIGHT OVERLAY ==="
python3 scripts/runtime/apply_exit_overlay.py \
  --base-config config/exit_signals.json \
  --weight-delta "${EXIT_WEIGHT_DELTA}" \
  --mode paper \
  --output config/overlays/exit_aggression_paper.json

echo "=== PHASE 2: ACTIVATE PAPER ENGINE WITH OVERLAY ==="
python3 scripts/runtime/restart_paper_engine.py \
  --exit-overlay config/overlays/exit_aggression_paper.json \
  --entries-unchanged \
  --ci-unchanged

echo "=== PHASE 3: ARM SAFETY GUARDRAILS ==="
python3 scripts/runtime/arm_loss_guard.py \
  --mode paper \
  --max-loss-usd "${MAX_LOSS_USD}" \
  --duration-hours "${DURATION_HOURS}" \
  --on-breach revert \
  --on-expiry revert \
  --output reports/runtime/EXIT_AGGRESSION_GUARD_${DATE}.json

echo "=== PHASE 4: START LIVE MONITORING ==="
python3 scripts/runtime/start_exit_experiment_monitor.py \
  --mode paper \
  --promotion reports/promotions/EXIT_AGGRESSION_PROMOTION_${DATE}.json \
  --metrics realized_pnl would_have_pnl exit_latency ci_interactions \
  --output reports/runtime/EXIT_AGGRESSION_MONITOR_${DATE}.json

echo "=== EXIT AGGRESSION ACTIVE IN PAPER ==="
