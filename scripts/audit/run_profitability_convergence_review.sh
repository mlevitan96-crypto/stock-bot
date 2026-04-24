#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — PROFITABILITY CONVERGENCE REVIEW
#
# PURPOSE:
#   - Present a hard strategic proposal focused on near-term profit
#   - Force multi-persona critique (not agreement)
#   - Produce a consensus Top-5 actions optimized for profitability
#
# CONSTRAINTS:
#   - No architecture expansion
#   - No new personas
#   - No deferral to "more data"
#   - Actions must be executable within days, not weeks
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/board reports/experiments reports/audit

echo "=== PHASE 0: STRATEGIC PROPOSAL (AUTHORITATIVE) ==="
# Ensure proposal exists (create if missing)
if [ ! -f reports/board/PROFITABILITY_STRATEGY_PROPOSAL.md ]; then
  cat > reports/board/PROFITABILITY_STRATEGY_PROPOSAL.md << 'EOF'
# Profitability Convergence Proposal

Objective:
Achieve positive expectancy and controlled profitability in the shortest possible time without compromising system resilience.

Non-Negotiable Principles:
1. Learning without exposure is failure.
2. Counter-intelligence must justify its economic cost.
3. Exits are profit engines, not safety valves.
4. Every day must end with at least one promotable action.
5. Reversibility is allowed; indecision is not.

Immediate Strategic Directives:
A. Enforce a daily promotion quota (minimum 1 action/day).
B. Impose an opportunity-cost budget on Counter-Intelligence.
C. Run exit-only aggression experiments with fixed entries.
D. Reduce signal space to the smallest profitable subset.
E. Focus capital on symbols that already show edge.

Success Criteria:
- Positive paper PnL under constrained risk.
- Clear identification of at least one scalable edge.
- Reduction in blocked opportunity cost without tail blowups.
EOF
fi

echo "=== PHASE 1: MULTI-PERSONA BOARD REVIEW ==="
python3 scripts/review/run_persona_reviews.py \
  --input reports/board/PROFITABILITY_STRATEGY_PROPOSAL.md \
  --personas CSA SRE QUANT RISK ADVERSARIAL BOARD \
  --review-questions \
    "What will fail first if we execute this?" \
    "What is the fastest path to profit from your domain?" \
    "What must be cut or constrained immediately?" \
    "What single action would you promote tomorrow?" \
  --output reports/experiments/PROFITABILITY_PERSONA_REVIEWS_${DATE}.json

echo "=== PHASE 2: CONSENSUS SYNTHESIS (TOP-5) ==="
python3 scripts/board/synthesize_consensus_actions.py \
  --reviews reports/experiments/PROFITABILITY_PERSONA_REVIEWS_${DATE}.json \
  --criteria profitability speed reversibility risk \
  --max-actions 5 \
  --require-consensus \
  --output reports/board/PROFITABILITY_TOP_5_ACTIONS_${DATE}.md

echo "=== PHASE 3: CSA EXECUTION VERDICT ==="
python3 scripts/csa/render_execution_verdict.py \
  --actions reports/board/PROFITABILITY_TOP_5_ACTIONS_${DATE}.md \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/audit/CSA_PROFITABILITY_EXECUTION_VERDICT_${DATE}.json

echo "=== PHASE 4: FINAL ASSERTIONS ==="
python3 scripts/audit/assert_artifacts_present.py \
  --required \
    reports/board/PROFITABILITY_STRATEGY_PROPOSAL.md \
    reports/experiments/PROFITABILITY_PERSONA_REVIEWS_${DATE}.json \
    reports/board/PROFITABILITY_TOP_5_ACTIONS_${DATE}.md \
    reports/audit/CSA_PROFITABILITY_EXECUTION_VERDICT_${DATE}.json

echo "=== PROFITABILITY CONVERGENCE REVIEW COMPLETE ==="
