# Signal funnel (Phase 1 full signal review)

Generated: 2026-02-20T20:14:51.970431+00:00
Window: last 7 days. Total candidates: **2922**

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
  - {'symbol': 'DIA', 'ts': 1771610343, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'COIN', 'ts': 1771610346, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}}
  - {'symbol': 'LCID', 'ts': 1771610346, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}}
  - {'symbol': 'SPY', 'ts': 1771610346, 'score_final': 1.055, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 1.055}}
  - {'symbol': 'XLF', 'ts': 1771610346, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'CAT', 'ts': 1771610350, 'score_final': 1.055, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 1.055}}
  - {'symbol': 'COP', 'ts': 1771610350, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'F', 'ts': 1771610350, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'JPM', 'ts': 1771610350, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}}
  - {'symbol': 'NIO', 'ts': 1771610350, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}}
  - {'symbol': 'SLB', 'ts': 1771610350, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'CVX', 'ts': 1771610351, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'RIVN', 'ts': 1771610351, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}}
  - {'symbol': 'INTC', 'ts': 1771610371, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'AMD', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'GOOGL', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'MRNA', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'NVDA', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}
  - {'symbol': 'PLTR', 'ts': 1771610372, 'score_final': 0.172, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.172}}
  - {'symbol': 'TSLA', 'ts': 1771610372, 'score_final': 0.316, 'gate_reason': 'expectancy_gate:score_floor_breach', 'measured': {'composite_score': 0.316}}

### 6_risk_capacity_gates

- Count in: 2922

### 7_order_placement_outcomes

- Count in: 2922
- Top reasons:
  - filled: 6382
  - rejected: 530