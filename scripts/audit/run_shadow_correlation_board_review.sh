#!/usr/bin/env bash
# Board + CSA review of Shadow Signal Correlation & Cluster proposal; decide strategy to test.
set -euo pipefail

DATE="${DATE:-2026-03-10}"

mkdir -p reports/board reports/experiments reports/audit

echo "=== BOARD REVIEW: SHADOW SIGNAL CORRELATION & CLUSTER PROPOSAL ==="
test -f reports/board/SHADOW_SIGNAL_CORRELATION_CLUSTER_PROPOSAL.md || { echo "ERROR: Proposal missing"; exit 1; }

echo "=== PERSONA REVIEW (CSA, SRE, QUANT, RISK, ADVERSARIAL) ==="
python3 scripts/review/run_persona_reviews.py \
  --input reports/board/SHADOW_SIGNAL_CORRELATION_CLUSTER_PROPOSAL.md \
  --personas CSA SRE QUANT RISK ADVERSARIAL \
  --review-questions \
    "Does this analysis make sense for improving weight and signal decisions without changing behavior?" \
    "What could go wrong (e.g. overfitting to synthetic backfill, small sample)?" \
    "What is the best strategy to test: (A) run once on current backfill, (B) run weekly as backfill grows, (C) run only when native emission replaces backfill, (D) other?" \
  --output reports/experiments/CORRELATION_CLUSTER_REVIEWS_${DATE}.json

echo "=== SYNTHESIZE STRATEGY-TO-TEST DECISION ==="
python3 scripts/board/synthesize_correlation_strategy_decision.py \
  --reviews reports/experiments/CORRELATION_CLUSTER_REVIEWS_${DATE}.json \
  --output reports/board/CORRELATION_STRATEGY_DECISION_${DATE}.md

echo "=== CSA EXECUTION VERDICT ==="
python3 scripts/csa/render_execution_verdict.py \
  --decision reports/board/CORRELATION_STRATEGY_DECISION_${DATE}.md \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/audit/CSA_CORRELATION_STRATEGY_VERDICT_${DATE}.json

echo "=== BOARD REVIEW COMPLETE — STRATEGY LOCKED ==="
