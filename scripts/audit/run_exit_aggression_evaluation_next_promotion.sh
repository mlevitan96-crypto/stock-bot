#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — EXIT AGGRESSION EVALUATION + NEXT PROMOTION
#
# PURPOSE:
#   - Evaluate the live exit aggression experiment
#   - Decide: EXTEND, AMPLIFY, or REVERT
#   - Force selection of the NEXT promotable action
#
# CONSTRAINTS:
#   - Decision required even if data is weak
#   - One next promotion must be selected
#   - No architecture changes
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/experiments reports/board reports/audit

echo "=== PHASE 0: COLLECT EXIT EXPERIMENT METRICS ==="
python3 scripts/runtime/collect_exit_experiment_metrics.py \
  --promotion reports/promotions/EXIT_AGGRESSION_PROMOTION_${DATE}.json \
  --monitor reports/runtime/EXIT_AGGRESSION_MONITOR_${DATE}.json \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/experiments/EXIT_AGGRESSION_RESULTS_${DATE}.json

echo "=== PHASE 1: CSA EVALUATION (FORCED VERDICT) ==="
python3 scripts/csa/evaluate_exit_experiment.py \
  --results reports/experiments/EXIT_AGGRESSION_RESULTS_${DATE}.json \
  --criteria realized_pnl would_have_pnl exit_latency tail_risk \
  --require-verdict \
  --output reports/audit/CSA_EXIT_EXPERIMENT_VERDICT_${DATE}.json

echo "=== PHASE 2: DECIDE NEXT PROMOTION (MANDATORY) ==="
python3 scripts/board/decide_next_promotion.py \
  --previous-promotion reports/promotions/EXIT_AGGRESSION_PROMOTION_${DATE}.json \
  --verdict reports/audit/CSA_EXIT_EXPERIMENT_VERDICT_${DATE}.json \
  --candidate-types \
      "ci_budget_relaxation" \
      "signal_pruning" \
      "symbol_focus" \
      "exit_amplification" \
  --require-selection \
  --output reports/board/NEXT_PROMOTION_DECISION_${DATE}.md

echo "=== PHASE 3: CSA AUTHORIZATION OF NEXT PROMOTION ==="
python3 scripts/csa/render_execution_verdict.py \
  --decision reports/board/NEXT_PROMOTION_DECISION_${DATE}.md \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/audit/CSA_NEXT_PROMOTION_VERDICT_${DATE}.json

echo "=== PHASE 4: ASSERT CONTINUOUS PROMOTION ==="
python3 scripts/audit/assert_continuous_promotion.py \
  --date "$DATE" \
  --current reports/audit/CSA_EXIT_EXPERIMENT_VERDICT_${DATE}.json \
  --next reports/audit/CSA_NEXT_PROMOTION_VERDICT_${DATE}.json

echo "=== EXIT EXPERIMENT EVALUATED — NEXT PROMOTION LOCKED ==="
