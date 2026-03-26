# Alpaca Profit Lab — Robustness & Scalability (Phase 5, QSA)

**Mission:** For top engines: bootstrap resampling, worst-day removal, leave-one-symbol-out, gap stress; estimate leverage tolerance.  
**Authority:** QSA.  
**Date:** 2026-03-18.

---

## 1. Robustness Checks (To Run on Top Strategies from Phase 4)

| Check | Description | Output |
|-------|-------------|--------|
| **Bootstrap resampling** | Resample trades with replacement (e.g. 1000 runs); report CI for total PnL and expectancy. | Mean, 5th/95th percentile, std. |
| **Worst-day removal** | Drop the single calendar day that contributes most negative PnL; recompute total and expectancy. | PnL with worst day removed; sensitivity. |
| **Leave-one-symbol-out** | For each symbol in the strategy’s set, remove that symbol’s trades and recompute PnL. | Per-symbol sensitivity; min/max PnL. |
| **Gap stress** | Restrict to trades that have at least one overnight/weekend gap; or exclude gap trades. Compare PnL. | PnL with/without gaps. |
| **Leverage tolerance** | Scale position size (e.g. 1x, 1.5x, 2x) on same path; report drawdown and max adverse excursion. | Max drawdown, MAE distribution by scale. |

---

## 2. Data Requirements

- Top strategies from ALPACA_PROFIT_LAB_RAW_RESULTS.json (or RANKED.md) with trade-level detail (trade_key or trade_id list per strategy).
- TRADES_FROZEN + TRADE_TELEMETRY (for gap/MAE when available).
- Calendar day per trade (from entry_time or exit_time).

---

## 3. Recommendation

Implement a small script (e.g. `scripts/audit/run_alpaca_profit_lab_robustness.py`) that:

1. Loads top-k strategies and their constituent trade_keys from Phase 4 output.
2. For each strategy, loads corresponding rows from TRADES_FROZEN.
3. Runs bootstrap, worst-day removal, leave-one-symbol-out; writes results to this file or ALPACA_PROFIT_LAB_ROBUSTNESS_RESULTS.json.
4. Leverage tolerance can be simulated by scaling realized_pnl_usd (linear in size) and recomputing drawdown from equity curve.

---

## 4. Placeholder Results

| Strategy ID | Bootstrap 5th %ile | Bootstrap 95th %ile | Worst-day-removed PnL | LOSO min PnL | LOSO max PnL |
|-------------|--------------------|----------------------|------------------------|--------------|--------------|
| (Populate after Phase 4 + robustness run) | | | | | |
