#!/usr/bin/env bash
# ============================================================
# CURSOR BLOCK — COUNTER-INTEL SEMANTIC HARDENING
# PURPOSE:
#   - Make CI explain itself
#   - Couple CI to entry + exit signals
#   - Surface CI opportunity cost vs protection
#
# SHADOW-ONLY | PAPER-ONLY | FAIL-CLOSED
# ============================================================
# Prerequisite: FULL_TRADE_LEDGER_${DATE}.json and optionally
# COUNTER_INTEL_EVENTS (or ledger counter_intel) present.

set -euo pipefail

DATE="${DATE:-2026-03-10}"

export GOVERNANCE_MODE=SHADOW_ONLY
export ALLOW_LIVE_WRITES=false
export REQUIRE_COUNTER_INTEL=true
export MIN_CI_EVENTS=1

mkdir -p reports/{ledger,audit,experiments,board}

echo "=== PHASE CI-1: ENRICH COUNTER-INTEL EVENTS ==="
python3 scripts/counter_intel/enrich_counter_intel_events.py \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --require-fields \
      blocked_signal_ids \
      blocked_signal_weights \
      exit_signal_state \
      risk_reason \
      would_have_pnl \
  --output reports/experiments/COUNTER_INTEL_ENRICHED_${DATE}.json

echo "=== PHASE CI-2: ASSERT CI SEMANTIC COMPLETENESS ==="
python3 scripts/csa/assert_counter_intel_semantics.py \
  --counter-intel reports/experiments/COUNTER_INTEL_ENRICHED_${DATE}.json \
  --fail-on-missing-explanations

echo "=== PHASE CI-3: CI ECONOMIC IMPACT ANALYSIS ==="
python3 scripts/csa/analyze_counter_intel_impact.py \
  --counter-intel reports/experiments/COUNTER_INTEL_ENRICHED_${DATE}.json \
  --ledger reports/ledger/FULL_TRADE_LEDGER_${DATE}.json \
  --output reports/audit/CSA_COUNTER_INTEL_IMPACT_${DATE}.json

echo "=== PHASE CI-4: BOARD VISIBILITY ==="
python3 scripts/board/append_ci_section_to_board_packet.py \
  --board reports/board/DAY_TRADING_INTELLIGENCE_BOARD_PACKET_${DATE}.md \
  --ci-impact reports/audit/CSA_COUNTER_INTEL_IMPACT_${DATE}.json

echo "=== CI HARDENING COMPLETE ==="
