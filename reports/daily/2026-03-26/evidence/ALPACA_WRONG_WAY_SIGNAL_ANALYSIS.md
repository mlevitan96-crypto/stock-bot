# Alpaca Wrong-Way Signal Analysis (Phase 3, QSA)

**Mission:** Identify signals associated with worse outcomes (wrong-way).  
**Authority:** QSA. READ-ONLY.  
**Date:** 2026-03-18.

---

## 1. Definition

A **wrong-way signal** is one where higher signal strength (or presence) is associated with **lower** realized PnL or higher loss rate, after controlling for confounders (e.g. regime, side).

---

## 2. Approach

- **Entry components:** Correlate entry composite components (flow, dark_pool, iv_skew, regime_modifier, etc.) with realized_pnl_usd. Negative correlation or negative coefficient → candidate wrong-way.
- **Exit components:** High exit_* (e.g. score_deterioration, regime_shift) on losers is often *consequence* of loss; interpret as “exit pressure on losers” unless used as entry filter.
- **Regime / TOD:** Stratify by entry_regime, hour-of-day; flag regimes or hours with win rate significantly below average.
- **Red flags:** Signals that appear as top contributors on **losing** trades (from loss forensics) and have positive weight in composite → candidate for weight reduction or gate.

---

## 3. Findings (From Existing Loss Forensics)

From ALPACA_LOSS_FORENSICS_ENTRY_CAUSES.md:

- Top entry components on large losers often include: **flow**, **dark_pool**, **event**, **toxicity_penalty**, **greeks_gamma**, **market_tide**.
- Many losers have **missing entry score** (entry attribution empty on droplet).
- Not all losses are “wrong direction” at entry; some have moderate entry scores (3–5) and still lose.

**Wrong-way candidates (hypothesis):** Signals that repeatedly appear in losing-trade top contributions and may be overweight or mis-timed (e.g. flow in adverse regime, event alignment without calendar filter). Formal correlation/regression on full frozen dataset to be run when ≥500 trades and component-level data available.

---

## 4. Regime / TOD Wrong-Way

| entry_regime or hour_bucket | Win rate | Trades | Note |
|-----------------------------|----------|--------|------|
| (Populate from TRADES_FROZEN) | | | Flag if win rate &lt; threshold. |

---

## 5. Recommended Outputs (When Run on Full Dataset)

- **Wrong-way signal list:** signal_id, correlation_with_pnl, mean_signal_on_winners vs losers.
- **Regime/TOD table:** regime or hour, win_rate, count; flag below-threshold buckets.
- **Actionable:** Suggest gates (e.g. reduce weight when regime = X) or avoid entry in hour Y for Phase 4/5 testing.
