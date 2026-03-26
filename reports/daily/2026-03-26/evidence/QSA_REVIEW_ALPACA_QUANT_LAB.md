# QSA Review — Alpaca Quant Lab (Phase 6)

**Mission:** Explain why winners win.  
**Authority:** QSA (quant/stat).  
**Date:** 2026-03-18.

---

## 1. Data & Contract (Phase 0)

- Data contract and join coverage documented in ALPACA_QUANT_DATA_CONTRACT.md and ALPACA_QUANT_JOIN_COVERAGE.md.
- TRADES_FROZEN is the canonical closed-trade list; path-real analysis uses bars when available.

## 2. Features & Signals (Phase 1)

- Feature inventory and redundancy in ALPACA_QUANT_FEATURE_INVENTORY.md and ALPACA_QUANT_SIGNAL_REDUNDANCY.md.
- Entry composite has 20+ components; exit has exit_* attribution; regime/IV/squeeze clusters identified.

## 3. Loss Mechanisms (Phase 2)

- Loss decomp in ALPACA_QUANT_LOSS_DECOMP.md.
- Key: regime_shift and sentiment/score deterioration drive many losing exits; entry quality mixed (some missing entry score).

## 4. Counterfactuals & Wrong-Way (Phase 3)

- ALPACA_QUANT_COUNTERFACTUALS.md: direction flip, delayed entry, regime-gated (path-real only).
- ALPACA_QUANT_WRONG_WAY_SIGNALS.md: signals associated with worse outcomes; regime/TOD flags.

## 5. Why Winners Win (To Populate After Phase 4/5)

- **Top strategies (by PnL or expectancy):** List strategy IDs and filters (regime, side, etc.).
- **Explanation:** Which conditions (regime, side, TOD, signal subset) are associated with positive expectancy? E.g. “Long in RISK_ON with high flow contribution” or “Short in chop with strict exit_score_deterioration.”
- **Robustness:** From Phase 5, which top strategies remain stable under bootstrap and worst-day removal?

*(Populate after running Phase 4 profit discovery and Phase 5 robustness.)*
