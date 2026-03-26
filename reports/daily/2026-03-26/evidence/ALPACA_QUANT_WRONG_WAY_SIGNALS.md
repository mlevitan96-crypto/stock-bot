# Alpaca Quant Lab — Wrong-Way Signals (QSA)

**Mission:** Phase 3 — Identify signals that associate with worse outcomes (wrong-way).  
**Authority:** QSA.  
**Date:** 2026-03-18.

---

## 1. Definition

A **wrong-way signal** is one where higher signal strength (or presence) is associated with **lower** realized PnL or higher loss rate, after controlling for obvious confounders (e.g. regime, side).

---

## 2. Approach

- **Entry components:** Correlate entry composite components (flow, dark_pool, iv_skew, regime_modifier, etc.) with realized_pnl_usd per trade. Negative correlation or negative coefficient in a simple regression → candidate wrong-way.
- **Exit components:** Correlate exit_* components (e.g. exit_score_deterioration, exit_regime_shift) with PnL. High exit deterioration may be a *consequence* of loss (post hoc); interpret as “exit pressure on losers” rather than wrong-way entry signal unless used as entry filter.
- **Regime / TOD:** Stratify by entry_regime, hour-of-day; identify regimes or hours where win rate is significantly below average (wrong-way regime or TOD).
- **Red flags:** Signals that consistently appear in top contributors for **losing** trades (from loss forensics) and have positive weight in the composite → candidate for reduction or gate.

---

## 3. Data

- TRADES_FROZEN + joined entry/exit attribution (component-level when available).
- Existing loss forensics: ALPACA_LOSS_FORENSICS_ENTRY_CAUSES.md lists top entry components for losers (e.g. flow, dark_pool, event, toxicity_penalty, greeks_gamma). If these same components are heavily weighted in composite and losers often have high values, that supports “wrong-way” hypothesis for those components in certain contexts.

---

## 4. Recommended Outputs

- **Wrong-way signal list:** Ranked by negative correlation or regression coefficient (e.g. signal_id, correlation_with_pnl, mean_signal_on_winners vs losers).
- **Regime/TOD wrong-way:** Table of (regime or hour_bucket, win_rate, count); flag regimes/hours below threshold.
- **Actionable:** Suggest gates (e.g. “reduce weight when regime = X”) or “avoid entry in hour Y” for testing in Phase 4/5.
