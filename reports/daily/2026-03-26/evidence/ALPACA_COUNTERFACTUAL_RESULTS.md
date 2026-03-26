# Alpaca Counterfactual Results (Phase 3, Path-Real)

**Mission:** Direction flip, delayed entry, regime-gated counterfactuals. Bars only; no guessed prices.  
**Authority:** QSA. READ-ONLY.  
**Date:** 2026-03-18.

---

## 1. Path-Real Constraint

- All counterfactual PnLs use **actual bar (or fill) prices** over the trade interval or a defined variant interval.
- **No synthetic or model-generated prices.** Source: data/bars_cache or Alpaca historical bars (symbol/date/resolution).

---

## 2. Counterfactual Types

### 2.1 Direction Flip

- **Definition:** Same entry_time → exit_time; opposite side (long → short, short → long). PnL = −(realized) for same size (path-real: bar path gives opposite sign).
- **Output:** Per-trade counterfactual_pnl_flip; aggregate: count of losers that would be winners if flipped; total PnL under flip.

| Metric | Value |
|--------|--------|
| Trades with flip PnL computed | (from bars) |
| Losers that would be winners (flip) | — |
| Total PnL (actual) | — |
| Total PnL (flip counterfactual) | — |

*(Populate when bar-level counterfactual script is run.)*

### 2.2 Delayed Entry

- **Definition:** Entry shifted +N minutes (e.g. +5, +15, +30); exit_time unchanged. Entry price = bar open at entry_time + N; path to exit from there.
- **Output:** Per-trade PnL for delay_5m, delay_15m, delay_30m; distribution vs actual.

| Delay | Trades | Mean PnL (delayed) | vs Actual (mean) |
|-------|--------|--------------------|------------------|
| +5m | — | — | — |
| +15m | — | — | — |
| +30m | — | — | — |

*(Populate when bar-level delayed-entry script is run.)*

### 2.3 Regime-Gated Entry

- **Definition:** Restrict to trades with entry_regime = X (e.g. RISK_ON, NEUTRAL). Compute baseline PnL for that subset; optionally compare flip/delayed within subset.
- **Output:** Conditional totals and counts by regime.

| entry_regime | Trades | Total PnL (actual) | Total PnL (flip) |
|--------------|--------|--------------------|------------------|
| (Populate) | | | |

---

## 3. Data Requirements

- TRADES_FROZEN.csv (entry_time, exit_time, symbol, side, entry_price, exit_price, size).
- Bars per trade (1Min or 5Min) from entry to exit. Missing bars → omit that trade from that counterfactual.

---

## 4. Implementation Note

- Use pipeline step2 bar fetch (fetch_bars_cached) and MFE/MAE-style path iteration; extend to compute flip (opposite sign) and delayed entry (new entry bar). See ALPACA_QUANT_COUNTERFACTUALS.md for spec. Script: e.g. `scripts/audit/run_alpaca_counterfactuals.py` (to be added or use replay counterfactual scripts).
