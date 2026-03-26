# QSA Review — Alpaca Profit Lab (Phase 6)

**Mission:** Explain why winners win (mechanism, not narrative).  
**Authority:** QSA (quant causality). READ-ONLY. No paper promotion in this block.  
**Date:** 2026-03-18.

---

## 1. Data & Contract

- Data contract: ALPACA_QUANT_DATA_CONTRACT.md, ALPACA_TRADES_FROZEN_DATASET_FREEZE.md.
- Join coverage: ALPACA_QUANT_JOIN_COVERAGE.md, ALPACA_TRADES_FROZEN_JOIN_COVERAGE.md.
- TRADES_FROZEN is canonical closed-trade list; path-real analysis uses bars when available.

## 2. Loss Causality (Phase 2)

- ALPACA_LOSS_CAUSALITY.md: direction correctness, MAE/MFE, entry vs exit, gap, regime mismatch; aggregates by cause, regime, symbol, time-of-day.
- Key mechanisms from forensics: regime_shift and sentiment/score deterioration drive many losing exits; entry quality mixed (many missing entry score).

## 3. Counterfactuals & Wrong-Way (Phase 3)

- ALPACA_COUNTERFACTUAL_RESULTS.md: direction flip, delayed entry, regime-gated (path-real only).
- ALPACA_WRONG_WAY_SIGNAL_ANALYSIS.md: signals associated with worse outcomes; regime/TOD flags.

## 4. Why Winners Win (Mechanism)

- **Top strategies (Phase 4):** From ALPACA_PROFIT_LAB_RANKED.md — ranked by total PnL and expectancy. Winners are strategy filters (e.g. regime, side, TOD) under which realized PnL is positive and stable.
- **Mechanism (not narrative):** (1) **Regime/side fit:** Trades in regimes and sides where price path and exit timing historically yielded positive expectancy. (2) **Exit alignment:** Lower exit pressure (regime_shift, score_deterioration) on winners. (3) **Avoid wrong-way:** Regimes/hours/signals flagged in wrong-way analysis are underweight or gated in winning subsets.
- **Robustness (Phase 5):** Top engines that remain stable under bootstrap, worst-day removal, and leave-one-symbol-out are scalable candidates; document in ALPACA_PROFIT_LAB_ROBUSTNESS.md.

*(Populate with concrete strategy IDs and mechanism bullets after Phase 4/5 runs on ≥500-trade dataset.)*
