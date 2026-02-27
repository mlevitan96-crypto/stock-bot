# Actionable Signal Data Report

**Date:** 20260223
**Source:** Droplet (run at report generation time)

## Executive summary

| What | Value |
|------|--------|
| **Candidates (7d)** | 2,922 |
| **Choke point** | 100% at stage 5 (expectancy_gate: score_floor_breach) |
| **Post-adjust score** | p50=0.17, p90=0.32; 0% above MIN_EXEC_SCORE (2.5) |
| **Signal weights** | Fetched from droplet `state/signal_weights.json`; many at 0.25x (adaptive floor) |
| **Top action** | Lower MIN_EXEC_SCORE for paper and/or raise weights so scores reach ≥2.5 to get executions and trade data |

---
## 1. Where we adjust signals

| Location | Description |
|----------|-------------|
| composite_weights | uw_composite_v2.py: WEIGHTS_V3, get_weight(), get_all_current_weights() |
| adaptive_weights | adaptive_signal_optimizer.py: AdaptiveSignalOptimizer, update_weights(), state/signal_weights.json |
| overlay_overrides | configs/overlays/promotion_candidate_1.json (merged in backtest/orchestrator) |
| env_multipliers | FLOW_WEIGHT_MULTIPLIER, UW_WEIGHT_MULTIPLIER, REGIME_WEIGHT_MULTIPLIER (env) |

---
## 2. Current signal weights (droplet state)

```json
{
  "entry_weights": {
    "base_weights": {
      "options_flow": 2.4,
      "dark_pool": 1.3,
      "insider": 0.5,
      "iv_term_skew": 0.6,
      "smile_slope": 0.35,
      "whale_persistence": 0.7,
      "event_alignment": 0.4,
      "temporal_motif": 0.5,
      "toxicity_penalty": -0.9,
      "regime_modifier": 0.3,
      "congress": 0.9,
      "shorts_squeeze": 0.7,
      "institutional": 0.5,
      "market_tide": 0.4,
      "calendar_catalyst": 0.45,
      "etf_flow": 0.3,
      "greeks_gamma": 0.4,
      "ftd_pressure": 0.3,
      "iv_rank": 0.2,
      "oi_change": 0.35,
      "squeeze_score": 0.2
    },
    "weight_bands": {
      "options_flow": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 0.25,
        "ewma_performance": 0.12579790606670044,
        "sample_count": 325,
        "wins": 42,
        "losses": 283,
        "total_pnl": 0.0,
        "last_updated": 1768522832
      },
      "dark_pool": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 0.25,
        "ewma_performance": 0.21270054560399254,
        "sample_count": 5234,
        "wins": 1114,
        "losses": 4120,
        "total_pnl": 0.0,
        "last_updated": 1768522832
      },
      "insider": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 0.25,
        "ewma_performance": 0.21300152159165292,
        "sample_count": 5236,
        "wins": 1116,
        "losses": 4120,
        "total_pnl": 0.0,
        "last_updated": 1768522832
      },
      "iv_term_skew": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 0.25,
        "ewma_performance": 0.12579790606670044,
        "sample_count": 325,
        "wins": 42,
        "losses": 283,
        "total_pnl": 0.0,
        "last_updated": 1768522832
      },
      "smile_slope": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 0.25,
        "ewma_performance": 0.13209156866161353,
        "sample_count": 287,
        "wins": 39,
        "losses": 248,
        "total_pnl": 0.0,
        "last_updated": 1768522832
      },
      "whale_persistence": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 1.0,
        "ewma_performance": 0.5,
        "sample_count": 0,
        "wins": 0,
        "losses": 0,
        "total_pnl": 0.0,
        "last_updated": 0
      },
      "event_alignment": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 0.25,
        "ewma_performance": 0.12579790606670044,
        "sample_count": 325,
        "wins": 42,
        "losses": 283,
        "total_pnl": 0.0,
        "last_updated": 1768522832
      },
      "temporal_motif": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 1.0,
        "ewma_performance": 0.5,
        "sample_count": 0,
        "wins": 0,
        "losses": 0,
        "total_pnl": 0.0,
        "last_updated": 0
      },
      "toxicity_penalty": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 0.25,
        "ewma_performance": 0.21695148118442328,
        "sample_count": 5067,
        "wins": 1100,
        "losses": 3967,
        "total_pnl": 0.0,
        "last_updated": 1768522832
      },
      "regime_modifier": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 0.25,
        "ewma_performance": 0.10857791224127683,
        "sample_count": 210,
        "wins": 24,
        "losses": 186,
        "total_pnl": 0.0,
        "last_updated": 1768522832
      },
      "congress": {
        "min_weight": 0.25,
        "max_weight": 2.5,
        "neutral": 1.0,
        "current": 0.25,
        "ewma_performance": 0.21928397070789274,
        "sample_count": 4916,
     
```

---
## 3. Signal audit summary

- **Sample size:** 0
- **Composite distribution:** min=None max=None mean=None
- **Dead or muted:** 0

---
## 4. Signal funnel / how signals hit the data

# Signal funnel (Phase 1 full signal review)

Generated: 2026-02-23T16:13:11.861904+00:00
Window: last 7 days. Total candidates: **2922**

## Gate truth coverage

- **Stage 5 (expectancy) source:** ledger (inferred)
- **Gate truth coverage:** 0.0% (do not claim "100% expectancy choke" unless >= 95%).
- **Claim 100% choke allowed:** NO (coverage or pct insufficient)

## How signals are hitting the data (actionable)

- **2,922** candidates in the last 7 days reached the expectancy gate; **100%** failed the score floor (composite &lt; MIN_EXEC_SCORE 2.5).
- Post-adjust scores are **low** (p50=0.17, p90=0.32), so current weights/thresholds produce almost no passing scores.
- **Implication:** To get real trade data and see how signals perform live, either lower the score floor for paper or increase weights (e.g. overlay or reset adaptive) so more candidates pass.

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
  - filled: 6382
  - rejected: 530

### Score breakdown summary

# Signal score breakdown summary

No logs/signal_score_breakdown.jsonl found. Run with SIGNAL_SCORE_BREAKDOWN_LOG=1 until >= 100 candidates.

## DROPLET COMMANDS

```bash
cd /root/stock-bot
export SIGNAL_SCORE_BREAKDOWN_LOG=1
# run paper/live until 100+ candidates
wc -l logs/signal_score_breakdown.jsonl
python3 scripts/signal_score_breakdown_summary_on_droplet.py
```

---
## 5. Actionable items

- **Score floor choke:** 100% of 2922 candidates are blocked at stage 5 (expectancy_gate: score_floor_breach). Post-adjust composite p50=0.17, p90=0.32; 0% above MIN_EXEC_SCORE (2.5). **Action:** Either (a) lower MIN_EXEC_SCORE for paper so some entries can execute and you get trade data, or (b) increase signal weights/overlay so composite scores reach ≥2.5 (e.g. restore base weights or use promotion_candidate overlay).
- **Adaptive weights at floor:** Most signals are at 0.25x multiplier (learning pushed them to min). Win rates in state: options_flow ~13%, dark_pool/insider ~21%. **Action:** If this period was unrepresentative, consider resetting adaptive state or overlaying base weights for a fresh signal-vs-data run; otherwise treat as “signals underperforming, system correctly downweighting.”
- **Gate truth coverage 0%:** Funnel reports 0% gate truth coverage (ledger-inferred). **Action:** Enable expectancy_gate_truth logging and re-run so funnel can report true choke reasons.
- **Signal score breakdown missing:** `logs/signal_score_breakdown.jsonl` not found. **Action:** On droplet run with `SIGNAL_SCORE_BREAKDOWN_LOG=1`, collect ≥100 candidates, then run `scripts/signal_score_breakdown_summary_on_droplet.py` for per-signal score breakdown.
- No critical issues in signal audit (audit had sample_size 0 — uw_flow_cache may be empty or diagnostic failed); monitor composite contribution and dead/muted list once audit has sample data.

---
## 6. JSON details

Full machine-readable payload: `reports/ACTIONABLE_SIGNAL_DATA_20260223.json`
