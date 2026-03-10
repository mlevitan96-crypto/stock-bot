#!/usr/bin/env bash
# ============================
# CURSOR BLOCK — FULL DAY TRADING INTELLIGENCE AUDIT
# CSA + SRE + MULTI-PERSONA GOVERNANCE
# SHADOW-ONLY | PAPER-ONLY | FAIL-CLOSED
# ============================
# Run on the DROPLET for real production data. Local runs use stale/wrong data.
# See: reports/audit/FULL_DAY_TRADING_INTELLIGENCE_AUDIT_RUNBOOK.md

set -euo pipefail

echo "=== PHASE 0: SAFETY & SCOPE LOCK ==="
export GOVERNANCE_MODE=SHADOW_ONLY
export ALLOW_LIVE_WRITES=false
export PROMOTION_ALLOWED=true
export DATE=${DATE:-$(date -u +%Y-%m-%d)}

mkdir -p reports/{audit,board,experiments,ledger,ideas,tmp}

echo "=== PHASE 1: FULL DAY TRADE UNIVERSE RECONSTRUCTION ==="
python scripts/audit/reconstruct_full_trade_ledger.py \
  --date "$DATE" \
  --include-executed \
  --include-blocked \
  --include-counter-intel \
  --emit-would-have-pnl \
  --output reports/ledger/FULL_TRADE_LEDGER_${DATE}.json

python scripts/audit/verify_trade_ledger_integrity.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --fail-on-missing \
  --fail-on-partial \
  --fail-on-duplicate

echo "=== PHASE 2: SRE SYSTEM HEALTH & TRUST CERTIFICATION ==="
python scripts/sre/run_day_health_audit.py \
  --date "$DATE" \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/audit/SRE_DAY_HEALTH_${DATE}.json

python scripts/sre/assert_clean_day.py \
  --input reports/audit/SRE_DAY_HEALTH_${DATE}.json

echo "=== PHASE 3: CSA DECISION QUALITY & OPPORTUNITY COST ANALYSIS ==="
python scripts/csa/analyze_decision_quality.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --classify-blocks \
  --classify-counter-intel \
  --compute-opportunity-cost \
  --output reports/audit/CSA_DECISION_QUALITY_${DATE}.json

echo "=== PHASE 4: IDEA HARVESTING (MASS EXTRACTION) ==="
python scripts/ideas/harvest_promotion_candidates.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --decision-quality reports/audit/CSA_DECISION_QUALITY_${DATE}.json \
  --min-opportunity-cost-usd 10 \
  --emit-all-ideas \
  --output reports/ideas/RAW_IDEA_POOL_${DATE}.json

python scripts/ideas/deduplicate_and_cluster_ideas.py \
  --input reports/ideas/RAW_IDEA_POOL_${DATE}.json \
  --output reports/ideas/CLUSTERED_IDEAS_${DATE}.json

echo "=== PHASE 5: MULTI-PERSONA REVIEW (PARALLEL) ==="
python scripts/review/run_persona_reviews.py \
  --ideas reports/ideas/CLUSTERED_IDEAS_${DATE}.json \
  --personas CSA SRE RISK QUANT ADVERSARIAL \
  --output reports/experiments/PERSONA_REVIEWS_${DATE}.json

echo "=== PHASE 6: ROBUSTNESS & PROMOTION SCORING ==="
python scripts/experiments/score_ideas_for_promotion.py \
  --ideas reports/ideas/CLUSTERED_IDEAS_${DATE}.json \
  --reviews reports/experiments/PERSONA_REVIEWS_${DATE}.json \
  --dimensions expectancy consistency drawdown tail regime simplicity \
  --output reports/experiments/IDEA_SCORECARD_${DATE}.json

echo "=== PHASE 7: CSA PROMOTION VERDICT ==="
python scripts/csa/render_promotion_verdict.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --scorecard reports/experiments/IDEA_SCORECARD_${DATE}.json \
  --sre-health reports/audit/SRE_DAY_HEALTH_${DATE}.json \
  --rules config/promotion_rules.json \
  --output reports/audit/CSA_DAY_PROMOTION_VERDICT_${DATE}.json

echo "=== PHASE 8: BOARD PACKET GENERATION ==="
python scripts/board/generate_day_board_packet.py \
  --date "$DATE" \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --decision-quality reports/audit/CSA_DECISION_QUALITY_${DATE}.json \
  --scorecard reports/experiments/IDEA_SCORECARD_${DATE}.json \
  --verdict reports/audit/CSA_DAY_PROMOTION_VERDICT_${DATE}.json \
  --output reports/board/DAY_TRADING_INTELLIGENCE_BOARD_PACKET_${DATE}.md

echo "=== PHASE 9: FINAL ASSERTIONS ==="
python scripts/audit/assert_artifacts_present.py \
  --required \
    reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
    reports/audit/SRE_DAY_HEALTH_${DATE}.json \
    reports/audit/CSA_DECISION_QUALITY_${DATE}.json \
    reports/ideas/CLUSTERED_IDEAS_${DATE}.json \
    reports/experiments/IDEA_SCORECARD_${DATE}.json \
    reports/audit/CSA_DAY_PROMOTION_VERDICT_${DATE}.json \
    reports/board/DAY_TRADING_INTELLIGENCE_BOARD_PACKET_${DATE}.md

echo "=== GOVERNANCE COMPLETE: DAY INTELLIGENCE AUDIT FINISHED ==="
