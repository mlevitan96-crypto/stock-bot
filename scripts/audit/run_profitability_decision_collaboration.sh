#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — PROFITABILITY DECISION COLLABORATION
#
# PURPOSE:
#   - Review current evidence and constraints
#   - Force persona-specific recommendations
#   - Decide the single best path forward for near-term profit
#
# OUTPUT:
#   - One chosen path (with rationale)
#   - Immediate execution plan (next 48–72 hours)
#
# CONSTRAINTS:
#   - Must choose ONE primary path
#   - Must be executable immediately
#   - Must increase expected PnL (variance allowed)
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/board reports/experiments reports/audit

echo "=== PHASE 0: EVIDENCE SNAPSHOT ==="
python3 scripts/board/compile_profitability_evidence.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --ci-impact reports/audit/CSA_COUNTER_INTEL_IMPACT_${DATE}.json \
  --signal-profitability reports/experiments/SIGNAL_PROFITABILITY_${DATE}.json \
  --top-actions reports/board/PROFITABILITY_TOP_5_ACTIONS_${DATE}.md \
  --output reports/board/PROFITABILITY_EVIDENCE_SNAPSHOT_${DATE}.md

echo "=== PHASE 1: PERSONA RECOMMENDATIONS (DECISION-FOCUSED) ==="
python3 scripts/review/run_persona_reviews.py \
  --input reports/board/PROFITABILITY_EVIDENCE_SNAPSHOT_${DATE}.md \
  --personas CSA SRE QUANT RISK ADVERSARIAL BOARD \
  --review-questions \
    "Given the evidence, what single action most increases near-term profitability?" \
    "What is the primary risk of this action and how do we cap it?" \
    "What should we explicitly NOT do right now?" \
  --output reports/experiments/PROFITABILITY_DECISION_REVIEWS_${DATE}.json

echo "=== PHASE 2: DECISION SYNTHESIS (FORCED CHOICE) ==="
python3 scripts/board/decide_best_path_forward.py \
  --reviews reports/experiments/PROFITABILITY_DECISION_REVIEWS_${DATE}.json \
  --require-single-decision \
  --decision-criteria \
    expected_pnl \
    speed_to_signal \
    reversibility \
    operational_risk \
  --output reports/board/PROFITABILITY_DECISION_${DATE}.md

echo "=== PHASE 3: CSA EXECUTION AUTHORIZATION ==="
python3 scripts/csa/render_execution_verdict.py \
  --decision reports/board/PROFITABILITY_DECISION_${DATE}.md \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/audit/CSA_PROFITABILITY_DECISION_VERDICT_${DATE}.json

echo "=== PHASE 4: FINAL ASSERTIONS ==="
python3 scripts/audit/assert_artifacts_present.py \
  --required \
    reports/board/PROFITABILITY_EVIDENCE_SNAPSHOT_${DATE}.md \
    reports/experiments/PROFITABILITY_DECISION_REVIEWS_${DATE}.json \
    reports/board/PROFITABILITY_DECISION_${DATE}.md \
    reports/audit/CSA_PROFITABILITY_DECISION_VERDICT_${DATE}.json

echo "=== PROFITABILITY DECISION COMPLETE ==="
