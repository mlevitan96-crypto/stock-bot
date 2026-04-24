#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — ACTIVATE COUNTER-INTEL + REAL SIGNAL PRESSURE
# PURPOSE:
#   - Make CI emit (mandatory)
#   - Replace signal stubs with real perturbations
#   - Run first STRICT CI-GATED full-day audit
#
# SHADOW-ONLY | PAPER-ONLY | FAIL-CLOSED
# ============================================================
# Prerequisite: FULL_TRADE_LEDGER_${DATE}.json must exist (run Phase 1 or full audit once).
# On droplet: run from repo root after ledger is present.

set -euo pipefail

DATE="${DATE:-2026-03-10}"

export GOVERNANCE_MODE=SHADOW_ONLY
export ALLOW_LIVE_WRITES=false
export REQUIRE_COUNTER_INTEL=true
export MIN_CI_EVENTS=1

mkdir -p reports/{ledger,audit,experiments,ideas,board,tmp}

echo "=== PHASE A: COUNTER-INTEL EMISSION ASSERTION ==="
python3 scripts/counter_intel/emit_counter_intel_events.py \
  --date "$DATE" \
  --ledger-input reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/tmp/COUNTER_INTEL_EVENTS_${DATE}.json

python3 scripts/csa/assert_counter_intel_present.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --counter-intel reports/tmp/COUNTER_INTEL_EVENTS_${DATE}.json \
  --min-events "${MIN_CI_EVENTS}"

echo "=== PHASE B: REAL SIGNAL WEIGHT PERTURBATIONS (ENTRY + EXIT) ==="
python3 scripts/signals/explode_signal_weights.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --mode real \
  --entry-weight-deltas "-0.3,-0.2,-0.1,0.1,0.2,0.3" \
  --exit-weight-deltas "-0.3,-0.2,-0.1,0.1,0.2,0.3" \
  --emit-interactions \
  --output reports/experiments/SIGNAL_WEIGHT_SWEEPS_${DATE}.json

python3 scripts/signals/evaluate_signal_profitability.py \
  --sweeps reports/experiments/SIGNAL_WEIGHT_SWEEPS_${DATE}.json \
  --require-nonzero-delta \
  --output reports/experiments/SIGNAL_PROFITABILITY_${DATE}.json

echo "=== PHASE C: FULL STRICT GOVERNANCE RUN (ON DROPLET) ==="
python3 scripts/audit/run_full_day_trading_intelligence_audit_on_droplet.py \
  --date "$DATE" \
  --require-counter-intel \
  --min-ci-events "${MIN_CI_EVENTS}"

echo "=== PHASE D: FINAL ASSERTIONS ==="
python3 scripts/audit/assert_artifacts_present.py \
  --required \
    reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
    reports/audit/SRE_DAY_HEALTH_${DATE}.json \
    reports/audit/CSA_DECISION_QUALITY_${DATE}.json \
    reports/experiments/SIGNAL_PROFITABILITY_${DATE}.json \
    reports/experiments/IDEA_SCORECARD_${DATE}.json \
    reports/audit/CSA_DAY_PROMOTION_VERDICT_${DATE}.json \
    reports/board/DAY_TRADING_INTELLIGENCE_BOARD_PACKET_${DATE}.md

echo "=== STRICT GOVERNANCE RUN COMPLETE ==="
