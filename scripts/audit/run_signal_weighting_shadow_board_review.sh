#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — CONTINUOUS SIGNAL WEIGHTING & SHADOW OPTIMIZATION
#
# PURPOSE:
#   - Board review of the proposal (CSA, Quant, Risk, SRE, Adversarial)
#   - Force consensus on the 5 board requirements
#   - Produce APPROVE + CSA execution verdict and instruct Cursor to proceed in shadow area
#
# CONSTRAINTS:
#   - No deferral to "more data"
#   - No architecture expansion beyond the shadow lab
#   - Decision required
# ============================================================

set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/board reports/experiments reports/audit

echo "=== PHASE 0: PROPOSAL (AUTHORITATIVE) ==="
PROPOSAL=reports/board/CONTINUOUS_SIGNAL_WEIGHTING_SHADOW_PROPOSAL.md
if [ ! -f "$PROPOSAL" ]; then
  echo "Proposal missing: $PROPOSAL" >&2
  exit 2
fi

echo "=== PHASE 1: MULTI-PERSONA BOARD REVIEW ==="
python3 scripts/review/run_persona_reviews.py \
  --input "$PROPOSAL" \
  --personas CSA SRE QUANT RISK ADVERSARIAL \
  --review-questions \
    "Do you agree that alpha signals should be weighted, not gated?" \
    "Do you approve creation of a shadow replay lab as read-only?" \
    "Do you authorize bulk weight sweeps in shadow only?" \
    "Do you confirm live promotions remain single-step, guarded, and reversible?" \
    "Do you direct Cursor to proceed with implementation in the shadow review area?" \
  --output reports/experiments/SIGNAL_WEIGHTING_SHADOW_REVIEWS_${DATE}.json

echo "=== PHASE 2: BOARD DECISION (APPROVE + 5 CONFIRMATIONS) ==="
python3 scripts/board/synthesize_board_decision.py \
  --reviews reports/experiments/SIGNAL_WEIGHTING_SHADOW_REVIEWS_${DATE}.json \
  --require-approval \
  --output reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md

echo "=== PHASE 3: CSA EXECUTION VERDICT ==="
python3 scripts/csa/render_execution_verdict.py \
  --decision reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/audit/CSA_SIGNAL_WEIGHTING_SHADOW_VERDICT_${DATE}.json

echo "=== PHASE 4: ASSERT ARTIFACTS AND APPROVAL ==="
python3 scripts/audit/assert_artifacts_present.py \
  --required \
    "$PROPOSAL" \
    reports/experiments/SIGNAL_WEIGHTING_SHADOW_REVIEWS_${DATE}.json \
    reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md \
    reports/audit/CSA_SIGNAL_WEIGHTING_SHADOW_VERDICT_${DATE}.json

if ! grep -q "APPROVE" reports/board/SIGNAL_WEIGHTING_SHADOW_DECISION_${DATE}.md; then
  echo "Board decision must be APPROVE to pass." >&2
  exit 1
fi

echo "=== SIGNAL WEIGHTING & SHADOW BOARD REVIEW COMPLETE — CURSOR INSTRUCTED TO PROCEED IN SHADOW AREA ==="
