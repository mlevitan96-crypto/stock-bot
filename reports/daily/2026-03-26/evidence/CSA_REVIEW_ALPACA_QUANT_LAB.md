# CSA Review — Alpaca Quant Lab (Phase 6)

**Mission:** Block or approve paper promotion based on lab evidence.  
**Authority:** CSA (governance).  
**Date:** 2026-03-18.

---

## 1. Governance Stance

- **READ-ONLY:** This lab makes no live or paper execution changes. Promotion decisions are separate.
- **Evidence:** Lab provides data truth, loss decomp, counterfactuals, profit discovery, and robustness. CSA uses this to block or approve paper promotion per MEMORY_BANK and promotion gate.

## 2. Checklist (To Complete After Phase 4/5)

- [ ] Data contract and join coverage acceptable for attribution conclusions (Phase 0).
- [ ] Top profit engines from Phase 4 identified and documented.
- [ ] Robustness (Phase 5): top engines stable under bootstrap and worst-day removal; no single-symbol dependency that would make promotion risky.
- [ ] Wrong-way signals and regime/TOD risks documented; no promotion of levers that are wrong-way unless explicitly overridden with justification.
- [ ] SRE certifies data integrity (SRE_REVIEW_ALPACA_QUANT_LAB.md).

## 3. Verdict (To Populate)

- **BLOCK** if: data integrity failed, join coverage below bar, or top engines are not robust.
- **APPROVE** if: data integrity certified, top engines robust, and governance conditions met.
- **CONDITIONAL** if: approve only for specific regimes/symbol sets or with explicit risk limits.

*(Populate after Phase 4/5 and SRE review.)*
