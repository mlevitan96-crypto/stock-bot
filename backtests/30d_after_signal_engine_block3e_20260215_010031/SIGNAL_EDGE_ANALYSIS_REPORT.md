# Signal Edge Analysis Report

**Backtest dir:** `/root/stock-bot/backtests/30d_after_signal_engine_block3e_20260215_010031`
**Trades:** 2243 | **Exits:** 2815 | **Blocks:** 2000

---

## 1. Data availability

Signals found in trade context: regime_signal.

---

## 2. Regime-level summary (no signal bucketing)

| Regime | Trades | Win rate (%) | Avg P&L ($) | Total P&L ($) |
|--------|--------|--------------|-------------|---------------|
| MIXED | 2233 | 15.09 | -0.07 | -155.48 |
| UNKNOWN | 10 | 30.0 | -0.67 | -6.67 |

---

## 3. Global signal buckets (all regimes)

### trend_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| missing | 2243 | 15.16 | -0.07 | -0.153 |

### momentum_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| missing | 2243 | 15.16 | -0.07 | -0.153 |

### volatility_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| missing | 2243 | 15.16 | -0.07 | -0.153 |

### regime_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 2243 | 15.16 | -0.07 | -0.153 |

### sector_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| missing | 2243 | 15.16 | -0.07 | -0.153 |

### reversal_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| missing | 2243 | 15.16 | -0.07 | -0.153 |

### breakout_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| missing | 2243 | 15.16 | -0.07 | -0.153 |

### mean_reversion_signal

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| missing | 2243 | 15.16 | -0.07 | -0.153 |

### entry_score

| Bucket | Trades | Win rate (%) | Avg P&L ($) | Expectancy |
|--------|--------|--------------|-------------|------------|
| near_zero | 10 | 30.0 | -0.67 | -0.2925 |
| positive | 2233 | 15.09 | -0.07 | -0.1537 |

---

## 4. Per-regime signal buckets (where applicable)

### trend_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 2233 | 15.09 | -0.07 |

**UNKNOWN**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 10 | 30.0 | -0.67 |

### momentum_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 2233 | 15.09 | -0.07 |

**UNKNOWN**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 10 | 30.0 | -0.67 |

### volatility_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 2233 | 15.09 | -0.07 |

**UNKNOWN**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 10 | 30.0 | -0.67 |

### regime_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 2233 | 15.09 | -0.07 |

**UNKNOWN**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 10 | 30.0 | -0.67 |

### sector_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 2233 | 15.09 | -0.07 |

**UNKNOWN**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 10 | 30.0 | -0.67 |

### reversal_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 2233 | 15.09 | -0.07 |

**UNKNOWN**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 10 | 30.0 | -0.67 |

### breakout_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 2233 | 15.09 | -0.07 |

**UNKNOWN**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 10 | 30.0 | -0.67 |

### mean_reversion_signal (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 2233 | 15.09 | -0.07 |

**UNKNOWN**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| missing | 10 | 30.0 | -0.67 |

### entry_score (by regime)

**MIXED**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| positive | 2233 | 15.09 | -0.07 |

**UNKNOWN**

| Bucket | Trades | Win rate (%) | Avg P&L ($) |
|--------|--------|--------------|-------------|
| near_zero | 10 | 30.0 | -0.67 |

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
