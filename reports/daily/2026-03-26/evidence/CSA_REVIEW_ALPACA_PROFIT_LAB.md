# CSA Review — Alpaca Profit Lab (Phase 6)

**Mission:** Block or approve for **future** paper promotion (no promotion executed in this block).  
**Authority:** CSA (governance). READ-ONLY.  
**Date:** 2026-03-18.

---

## 1. Governance Stance

- **This block:** READ-ONLY. No execution changes. No paper promotion is applied in this block.
- **Future promotion:** Lab evidence (data truth, loss causality, counterfactuals, profit discovery, robustness) informs CSA decision to **block** or **approve** paper promotion in a later step per MEMORY_BANK and promotion gate.

## 2. Checklist (For Future Promotion Decision)

- [ ] Data contract and join coverage acceptable (Phase 0, 1).
- [ ] TRADES_FROZEN dataset ≥500 trades (prefer ≥2000); validation passed (trade_key uniqueness, timestamps, gaps).
- [ ] Loss causality and wrong-way analysis documented; no promotion of levers that are wrong-way unless explicitly overridden with justification.
- [ ] Top profit engines from Phase 4 identified; robustness (Phase 5) acceptable (bootstrap, worst-day, LOSO, gap stress).
- [ ] SRE certifies data integrity and path-real evaluation (SRE_REVIEW_ALPACA_PROFIT_LAB.md).

## 3. Verdict (To Populate When Promotion Is in Scope)

- **BLOCK** if: data integrity failed, join coverage below bar without accepted override, or top engines not robust.
- **APPROVE** if: data integrity certified, top engines robust, governance conditions met.
- **CONDITIONAL** if: approve only for specific regimes/symbol sets or with explicit risk limits.

*(No verdict executed in this block. Populate when promotion decision is requested.)*
