# Signal funnel (Phase 1 full signal review)

Generated: 2026-02-24T16:00:23.577653+00:00
Window: last 7 days. Total candidates: **2922**

## Gate truth coverage

- **Stage 5 (expectancy) source:** ledger (inferred)
- **Gate truth coverage:** 64.8% (do not claim "100% expectancy choke" unless >= 95%).
- **Claim 100% choke allowed:** NO (coverage or pct insufficient)

## Dominant choke point

- **Stage:** 5_expectancy_gate
- **Reason:** expectancy_gate:score_floor_breach
- **Count:** 2922 (100.0%)

## Expectancy gate (score_floor_breach)

- **Pre-score availability rate:** 0.0% (expectancy fails with composite_pre_norm present). **Fallback when missing:** When composite_pre_norm is missing in ledger (from snapshot), pre-adjust stats use only rows that have it; distributions and % above MIN_EXEC_SCORE for pre-adjust may be based on a subset. Post-adjust always uses score_final.
- **Pre-adjust:** p10=0.000, p50=0.000, p90=0.000, count=0
- **Post-adjust:** p10=0.172, p50=0.172, p90=0.316, count=2922
- **% above MIN_EXEC_SCORE (2.5):** pre=0.0%, post=0.0%
- **Dominant reason post-adjust below floor:** score_floor_breach

## Per-stage counts and top reasons

### 1_universe_candidate_generation

- Count in: 2922

### 2_feature_availability

- Count in: 2922
- Top reasons:
  - has_score_components: 2922

### 3_uw_stage_outcomes

- Count in: 2922

### 4_adjustment_chain_deltas

- Count in: 2922

### 5_expectancy_gate

- Count in: 2922
- Top reasons:
  - expectancy_gate:score_floor_breach: 2922
- Examples (up to 20):
  - {'symbol': 'DIA', 'ts': 1771610343, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'COIN', 'ts': 1771610346, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}, 'source': 'ledger_inferred'}
  - {'symbol': 'LCID', 'ts': 1771610346, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}, 'source': 'ledger_inferred'}
  - {'symbol': 'SPY', 'ts': 1771610346, 'score_final': 1.055, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 1.055}, 'source': 'ledger_inferred'}
  - {'symbol': 'XLF', 'ts': 1771610346, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'CAT', 'ts': 1771610350, 'score_final': 1.055, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 1.055}, 'source': 'ledger_inferred'}
  - {'symbol': 'COP', 'ts': 1771610350, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'F', 'ts': 1771610350, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'JPM', 'ts': 1771610350, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}, 'source': 'ledger_inferred'}
  - {'symbol': 'NIO', 'ts': 1771610350, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}, 'source': 'ledger_inferred'}
  - {'symbol': 'SLB', 'ts': 1771610350, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'CVX', 'ts': 1771610351, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'RIVN', 'ts': 1771610351, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}, 'source': 'ledger_inferred'}
  - {'symbol': 'INTC', 'ts': 1771610371, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'AMD', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'GOOGL', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'MRNA', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'NVDA', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}
  - {'symbol': 'PLTR', 'ts': 1771610372, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}, 'source': 'ledger_inferred'}
  - {'symbol': 'TSLA', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}, 'source': 'ledger_inferred'}

### 6_risk_capacity_gates

- Count in: 2922

### 7_order_placement_outcomes

- Count in: 2922
- Top reasons:
  - filled: 10840
  - rejected: 963