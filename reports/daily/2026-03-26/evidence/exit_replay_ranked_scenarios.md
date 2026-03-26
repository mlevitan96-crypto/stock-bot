# Exit Replay Grid Summary

**Window:** 2026-02-01 to 2026-03-02.
**Scenarios run:** 14.

## Baseline (current live-like)

- Total PnL: $-248.54
- Expectancy/trade: -0.0928
- Win rate: 33.2%
- Avg hold (min): 5.6
- Trades in scenario: 2678

## Top 5 scenarios (by expectancy, then win rate, then hold)

### 1. remove_exit_time_decay

- **Params:** min_hold=0 min, decay_threshold=0.0, remove_components=['exit_time_decay']
- Total PnL: $0.00 | Expectancy: 0.0000 | Win rate: 0.0% | Avg hold: None min | Trades: 0

### 2. remove_exit_flow_deterioration

- **Params:** min_hold=0 min, decay_threshold=0.0, remove_components=['exit_flow_deterioration']
- Total PnL: $0.00 | Expectancy: 0.0000 | Win rate: 0.0% | Avg hold: None min | Trades: 0

### 3. remove_exit_score_deterioration

- **Params:** min_hold=0 min, decay_threshold=0.0, remove_components=['exit_score_deterioration']
- Total PnL: $0.00 | Expectancy: 0.0000 | Win rate: 0.0% | Avg hold: None min | Trades: 0

### 4. remove_exit_time_decay_and_flow

- **Params:** min_hold=0 min, decay_threshold=0.0, remove_components=['exit_time_decay', 'exit_flow_deterioration']
- Total PnL: $0.00 | Expectancy: 0.0000 | Win rate: 0.0% | Avg hold: None min | Trades: 0

### 5. minhold_5

- **Params:** min_hold=5 min, decay_threshold=0.0, remove_components=[]
- Total PnL: $-27.00 | Expectancy: -0.0562 | Win rate: 38.5% | Avg hold: 24.53 min | Trades: 480

## All scenarios (ranked)

| Rank | Scenario | PnL | Expectancy | Win rate | Avg hold | Trades |
|------|----------|-----|------------|----------|----------|--------|
| 1 | remove_exit_time_decay | $0.00 | 0.0000 | 0.0% | N/A | 0 |
| 2 | remove_exit_flow_deterioration | $0.00 | 0.0000 | 0.0% | N/A | 0 |
| 3 | remove_exit_score_deterioration | $0.00 | 0.0000 | 0.0% | N/A | 0 |
| 4 | remove_exit_time_decay_and_flow | $0.00 | 0.0000 | 0.0% | N/A | 0 |
| 5 | minhold_5 | $-27.00 | -0.0562 | 38.5% | 24.5 | 480 |
| 6 | minhold_15 | $-12.62 | -0.0631 | 41.5% | 46.3 | 200 |
| 7 | baseline | $-248.54 | -0.0928 | 33.2% | 5.6 | 2678 |
| 8 | decay_080 | $-162.31 | -0.1027 | 33.5% | 5.7 | 1580 |
| 9 | decay_090 | $-83.39 | -0.1062 | 34.3% | 6.3 | 785 |
| 10 | minhold_15_decay_086 | $-9.87 | -0.1073 | 40.2% | 47.6 | 92 |
| 11 | decay_086 | $-132.13 | -0.1097 | 33.5% | 6.0 | 1205 |
| 12 | decay_074 | $-223.19 | -0.1102 | 32.3% | 5.0 | 2026 |
| 13 | minhold_60_decay_090 | $-2.12 | -0.2653 | 37.5% | 235.0 | 8 |
| 14 | minhold_60 | $-7.31 | -0.3180 | 39.1% | 177.4 | 23 |

---
Per-regime and per-component insights: see `scenarios/<name>/summary.json`.