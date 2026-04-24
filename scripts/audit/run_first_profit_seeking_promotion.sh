#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — FIRST PROFIT-SEEKING PROMOTION
#
# PURPOSE:
#   - Satisfy the daily promotion quota with a real behavior change
#   - Apply exit-only aggression (highest upside / lowest coupling)
#   - Activate immediately in paper trading
#
# CONSTRAINTS:
#   - Entries unchanged
#   - CI unchanged
#   - Paper-only
#   - Reversible
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

export GOVERNANCE_MODE=SHADOW_ONLY
export ALLOW_LIVE_WRITES=false
export PROMOTION_TYPE=EXIT_AGGRESSION

mkdir -p reports/promotions reports/audit

echo "=== PHASE 0: SELECT EXIT AGGRESSION PARAMETERS ==="
python3 scripts/experiments/select_exit_aggression_params.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --candidates \
      "exit_delay:+2_bars" \
      "exit_delay:+4_bars" \
      "exit_confirmations:-1" \
      "exit_weight:+0.15" \
  --selection-criteria \
      expected_pnl \
      tail_risk \
      reversibility \
  --output reports/promotions/EXIT_AGGRESSION_SELECTION_${DATE}.json

echo "=== PHASE 1: PROMOTE EXIT CHANGE TO PAPER ==="
python3 scripts/promotions/promote_exit_experiment.py \
  --selection reports/promotions/EXIT_AGGRESSION_SELECTION_${DATE}.json \
  --mode paper \
  --max-loss-usd 25 \
  --duration-hours 48 \
  --output reports/promotions/EXIT_AGGRESSION_PROMOTION_${DATE}.json

echo "=== PHASE 2: CSA PROMOTION RECORD ==="
python3 scripts/csa/record_promotion.py \
  --promotion reports/promotions/EXIT_AGGRESSION_PROMOTION_${DATE}.json \
  --reason "Daily promotion quota — profit-seeking exit aggression" \
  --output reports/audit/CSA_PROMOTION_RECORD_${DATE}.json

echo "=== PHASE 3: ASSERT QUOTA SATISFIED ==="
python3 scripts/audit/assert_daily_promotion.py \
  --date "$DATE" \
  --promotion-record reports/audit/CSA_PROMOTION_RECORD_${DATE}.json

echo "=== EXIT AGGRESSION PROMOTION ACTIVE ==="
