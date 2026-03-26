# Alpaca Quant Lab — Counterfactuals & Path-Real Rules (QSA)

**Mission:** Phase 3 — Direction flip, delayed entry, regime-gated counterfactuals. Path-real only; no guessed prices.  
**Authority:** QSA.  
**Date:** 2026-03-18.

---

## 1. Path-Real Constraint

- **No guessed prices.** All counterfactual PnLs must use actual bar (or fill) prices over the trade interval or a well-defined variant interval.
- **Path-real only:** Use cached bars (data/bars_cache) or Alpaca historical bars for symbol/date; no synthetic or model-generated prices.

---

## 2. Counterfactual Types

### 2.1 Direction Flip

- **Definition:** For each closed trade, compute PnL if we had taken the opposite side (long → short, short → long) over the **same** entry_time → exit_time window.
- **Implementation:** From bars: for each bar, (close − open) for long vs (open − close) for short; aggregate to counterfactual PnL. Same path, opposite sign (for same-size position).
- **Output:** Per-trade counterfactual_pnl_flip; aggregate: how many losers would have been winners with flipped direction; total PnL under flip.

### 2.2 Delayed Entry

- **Definition:** For each trade, shift entry forward by +N minutes (e.g. +5, +15, +30); keep exit_time. Recompute PnL using bar path from new entry to exit.
- **Implementation:** From bars: entry_price_delayed = bar open at entry_time + N; path from that bar to exit. Realized PnL = f(entry_price_delayed, exit_price, side, size).
- **Output:** Per-trade PnL for delayed entry (e.g. delay_5m_pnl, delay_15m_pnl); distribution of improvement/decay vs actual.

### 2.3 Regime-Gated Counterfactuals

- **Definition:** Restrict to trades that satisfy a regime condition (e.g. entry_regime = RISK_ON, or exit_regime = chop). Compute baseline PnL for that subset; optionally compare to “flip” or “delayed” within the same subset.
- **Implementation:** Filter TRADES_FROZEN (and joined bars) by entry_regime or exit_regime; run direction-flip or delayed-entry on filtered set. Path-real from bars.
- **Output:** Conditional totals and counts; “would we have done better in RISK_ON only?” etc.

---

## 3. Data Requirements

- **TRADES_FROZEN.csv** (entry_time, exit_time, symbol, side, entry_price, exit_price, size or qty).
- **Bars** per trade (step2-style fetch): 1Min (or 5Min) bars from entry_time to exit_time. Missing bars → omit that trade from that counterfactual.

---

## 4. Implementation Notes

- Pipeline step2 already fetches bars and can compute MFE/MAE; extend the same bar loop to compute:
  - **Flip:** For same bars, PnL with opposite side (e.g. (exit_price − entry_price) * size for short if actual was long).
  - **Delayed entry:** Re-entry price = first bar after entry_time + N; then path to exit.
- Scripts such as `scripts/replay_exit_timing_counterfactuals.py` or replay scenarios may already support path-real variants; align counterfactual definitions with those contracts.

---

## 5. Output Artifacts (Recommended)

- **ALPACA_QUANT_COUNTERFACTUALS_SUMMARY.md:** Tables: direction flip (count better/worse, total PnL flip vs actual); delayed entry (by delay bucket); regime-gated (by regime, count, total PnL).
- **Per-trade CSV (optional):** trade_key, actual_pnl, flip_pnl, delay_5m_pnl, delay_15m_pnl, entry_regime, exit_regime — for downstream analysis.
