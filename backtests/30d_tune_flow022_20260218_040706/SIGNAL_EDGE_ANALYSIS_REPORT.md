# Signal Edge Analysis Report

**Backtest dir:** `/root/stock-bot/backtests/30d_tune_flow022_20260218_040706`
**Trades:** 535 | **Exits:** 1618 | **Blocks:** 0

---

## 1. Data availability

Signals found in trade context: trend_signal, momentum_signal, volatility_signal, regime_signal, sector_signal, reversal_signal, breakout_signal, mean_reversion_signal.

---

## 2. Regime-level summary (no signal bucketing)

| Regime | Trades | Win rate (%) | Avg P&L ($) | Total P&L ($) |
|--------|--------|--------------|-------------|---------------|
| MIXED | 535 | 15.51 | -0.05 | -28.94 |

---

## 3. Global signal buckets (all regimes)

### trend_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 535 | 15.51 | -0.05 | -0.1503 |

### momentum_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 535 | 15.51 | -0.05 | -0.1503 |

### volatility_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 535 | 15.51 | -0.05 | -0.1503 |

### regime_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 535 | 15.51 | -0.05 | -0.1503 |

### sector_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 535 | 15.51 | -0.05 | -0.1503 |

### reversal_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 535 | 15.51 | -0.05 | -0.1503 |

### breakout_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 535 | 15.51 | -0.05 | -0.1503 |

### mean_reversion_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 535 | 15.51 | -0.05 | -0.1503 |

### entry_score

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| positive | 535 | 15.51 | -0.05 | -0.1503 |

---

## 4. Per-regime signal buckets (where applicable)

### trend_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 535 | 15.51 | -0.05 |

### momentum_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 535 | 15.51 | -0.05 |

### volatility_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 535 | 15.51 | -0.05 |

### regime_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 535 | 15.51 | -0.05 |

### sector_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 535 | 15.51 | -0.05 |

### reversal_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 535 | 15.51 | -0.05 |

### breakout_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 535 | 15.51 | -0.05 |

### mean_reversion_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 535 | 15.51 | -0.05 |

### entry_score (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| positive | 535 | 15.51 | -0.05 |

---

## 5. Summary for weight tuning

- **trend_signal:** insufficient bucket data
- **momentum_signal:** insufficient bucket data
- **volatility_signal:** insufficient bucket data
- **regime_signal:** insufficient bucket data
- **sector_signal:** insufficient bucket data
- **reversal_signal:** insufficient bucket data
- **breakout_signal:** insufficient bucket data
- **mean_reversion_signal:** insufficient bucket data
- **entry_score:** insufficient bucket data

---

## 6. Limitations

- This analysis is **descriptive**, not causal. Correlation does not imply causation.
- Raw signals (trend_signal, momentum_signal, etc.) may not be logged in attribution context.
- When missing, we use entry_score and regime_signal (derived from market_regime).
- To enable full per-signal edge analysis, add raw signal fields to attribution context at entry.
