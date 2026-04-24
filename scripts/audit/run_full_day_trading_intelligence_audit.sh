#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — FULL DAY TRADING INTELLIGENCE GOVERNANCE
# WITH MANDATORY COUNTER-INTEL + SIGNAL SYSTEM REVIEW
# CSA + SRE + MULTI-PERSONA (MULTIPLE MODELS)
# SHADOW-ONLY | PAPER-ONLY | FAIL-CLOSED
# ============================================================
# Run on the DROPLET for real production data.
# See: reports/audit/FULL_DAY_TRADING_INTELLIGENCE_AUDIT_RUNBOOK.md

set -euo pipefail

export DATE="${DATE:-$(date -u +%Y-%m-%d)}"

echo "=== PHASE 0: SAFETY & GOVERNANCE LOCK ==="
export GOVERNANCE_MODE=SHADOW_ONLY
export ALLOW_LIVE_WRITES=false
export REQUIRE_COUNTER_INTEL=true

mkdir -p reports/{ledger,audit,experiments,ideas,board,tmp}

echo "=== PHASE 1: FULL DAY TRADE UNIVERSE (EXECUTED + BLOCKED + CI) ==="
python3 scripts/audit/reconstruct_full_trade_ledger.py \
  --date "$DATE" \
  --include-executed \
  --include-blocked \
  --include-counter-intel \
  --emit-would-have-pnl \
  --output reports/ledger/FULL_TRADE_LEDGER_${DATE}.json

python3 scripts/audit/verify_trade_ledger_integrity.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --fail-on-missing \
  --fail-on-partial

# CI emission (mandatory): ensure counter_intel events exist so Phase 3 can pass
if [ "${REQUIRE_COUNTER_INTEL:-false}" = "true" ] || [ "${MIN_CI_EVENTS:-0}" -gt 0 ]; then
  echo "=== PHASE 1b: COUNTER-INTEL EMISSION ==="
  python3 scripts/counter_intel/emit_counter_intel_events.py \
    --date "$DATE" \
    --ledger-input reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
    --output reports/tmp/COUNTER_INTEL_EVENTS_${DATE}.json
  python3 scripts/counter_intel/merge_counter_intel_into_ledger.py \
    --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
    --counter-intel reports/tmp/COUNTER_INTEL_EVENTS_${DATE}.json
fi

echo "=== PHASE 2: SRE DAY HEALTH CERTIFICATION ==="
python3 scripts/sre/run_day_health_audit.py \
  --date "$DATE" \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/audit/SRE_DAY_HEALTH_${DATE}.json

python3 scripts/sre/assert_clean_day.py \
  --input reports/audit/SRE_DAY_HEALTH_${DATE}.json

echo "=== PHASE 3: COUNTER-INTEL ASSERTION (MANDATORY) ==="
python3 scripts/csa/assert_counter_intel_present.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --min-events ${MIN_CI_EVENTS:-0}

echo "=== PHASE 4: CSA DECISION QUALITY & OPPORTUNITY COST ==="
python3 scripts/csa/analyze_decision_quality.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --classify-blocks \
  --classify-counter-intel \
  --compute-opportunity-cost \
  --output reports/audit/CSA_DECISION_QUALITY_${DATE}.json

echo "=== PHASE 5: SIGNAL SYSTEM EXPANSION (REAL PERTURBATIONS) ==="
python3 scripts/signals/explode_signal_weights.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --mode real \
  --entry-weight-deltas "${ENTRY_WEIGHT_DELTAS:--0.3,-0.2,-0.1,0.1,0.2,0.3}" \
  --exit-weight-deltas "${EXIT_WEIGHT_DELTAS:--0.3,-0.2,-0.1,0.1,0.2,0.3}" \
  --emit-interactions \
  --output reports/experiments/SIGNAL_WEIGHT_SWEEPS_${DATE}.json

python3 scripts/signals/evaluate_signal_profitability.py \
  --sweeps reports/experiments/SIGNAL_WEIGHT_SWEEPS_${DATE}.json \
  --require-nonzero-delta \
  --output reports/experiments/SIGNAL_PROFITABILITY_${DATE}.json

echo "=== PHASE 6: IDEA HARVESTING (MASS, NOT SINGLE) ==="
python3 scripts/ideas/harvest_promotion_candidates.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --decision-quality reports/audit/CSA_DECISION_QUALITY_${DATE}.json \
  --signal-profitability reports/experiments/SIGNAL_PROFITABILITY_${DATE}.json \
  --min-opportunity-cost-usd 10 \
  --emit-all-ideas \
  --output reports/ideas/RAW_IDEA_POOL_${DATE}.json

python3 scripts/ideas/deduplicate_and_cluster_ideas.py \
  --input reports/ideas/RAW_IDEA_POOL_${DATE}.json \
  --output reports/ideas/CLUSTERED_IDEAS_${DATE}.json

echo "=== PHASE 7: MULTI-PERSONA REVIEW ==="
python3 scripts/review/run_persona_reviews.py \
  --ideas reports/ideas/CLUSTERED_IDEAS_${DATE}.json \
  --personas CSA SRE QUANT RISK ADVERSARIAL BOARD \
  --output reports/experiments/PERSONA_REVIEWS_${DATE}.json

echo "=== PHASE 8: ROBUSTNESS & PROMOTION SCORING ==="
python3 scripts/experiments/score_ideas_for_promotion.py \
  --ideas reports/ideas/CLUSTERED_IDEAS_${DATE}.json \
  --reviews reports/experiments/PERSONA_REVIEWS_${DATE}.json \
  --dimensions expectancy consistency drawdown tail regime simplicity \
  --output reports/experiments/IDEA_SCORECARD_${DATE}.json

echo "=== PHASE 9: CSA PROMOTION VERDICT ==="
python3 scripts/csa/render_promotion_verdict.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --scorecard reports/experiments/IDEA_SCORECARD_${DATE}.json \
  --sre-health reports/audit/SRE_DAY_HEALTH_${DATE}.json \
  --require-counter-intel \
  --output reports/audit/CSA_DAY_PROMOTION_VERDICT_${DATE}.json

echo "=== PHASE 10: BOARD PACKET ==="
python3 scripts/board/generate_day_board_packet.py \
  --date "$DATE" \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --decision-quality reports/audit/CSA_DECISION_QUALITY_${DATE}.json \
  --signal-profitability reports/experiments/SIGNAL_PROFITABILITY_${DATE}.json \
  --scorecard reports/experiments/IDEA_SCORECARD_${DATE}.json \
  --verdict reports/audit/CSA_DAY_PROMOTION_VERDICT_${DATE}.json \
  --output reports/board/DAY_TRADING_INTELLIGENCE_BOARD_PACKET_${DATE}.md

echo "=== GOVERNANCE COMPLETE ==="
