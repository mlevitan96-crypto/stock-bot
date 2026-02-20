# Signal Edge Analysis Report

**Backtest dir:** `/root/stock-bot/backtests/1d_signal_summary_20260220_222408`
**Trades:** 0 | **Exits:** 0 | **Blocks:** 0

---

## 1. Data availability

No raw signal fields (trend_signal, momentum_signal, etc.) found in trade context.
Using **entry_score** and **regime_signal** (derived from market_regime) for analysis.

---

## 2. Regime-level summary (no signal bucketing)

| Regime | Trades | Win rate (%) | Avg P&L ($) | Total P&L ($) |
|--------|--------|--------------|-------------|---------------|

---

## 3. Global signal buckets (all regimes)

---

## 4. Per-regime signal buckets (where applicable)

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
