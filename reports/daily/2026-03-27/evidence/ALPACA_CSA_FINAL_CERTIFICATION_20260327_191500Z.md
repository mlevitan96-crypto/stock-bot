# CSA final certification — Alpaca operational hardening (non-mutating)

**TS:** `20260327_191500Z`  
**Mission closure:** BOARD-CERTIFIED CLOSURE (NON-MUTATING)

---

## Final CSA statement

1. **All reviewed items** (1–5) are **labeling**, **certification**, or **shadow / offline analysis** only, when implemented per the board verdict table (`ALPACA_BOARD_VERDICT_TABLE_20260327_191500Z.md`).

2. **No trading behavior was modified** in this mission. The closure phase produced **artifacts only**; no repository or runtime mutation occurred.

3. **Any future implementation** must respect the **BLOCKED** variants below. Violations require a **new** CSA cycle — they are **not** covered by this approval.

---

## BLOCKED variants (implementation)

| ID | BLOCKED behavior |
|----|------------------|
| B1 | Loading or enforcing config from artifacts such that **live** thresholds or strategy mix **differ** from current droplet deploy without normal change control. |
| B2 | Using strict-completeness **certificate** to **replace** `evaluate_completeness` semantics, **bypass** promotion gates, or **auto-halt** entries without explicit governed runbook. |
| B3 | Using zero-fee **declaration** as the **sole** input to position sizing, margin, or risk limits (must remain **registry/env/broker** truth for live). |
| B4 | **Reading** meta-labels inside `decide_and_execute`, exit submission, or any **live** gate. |
| B5 | Applying exit A/B **winners** to **live** `exit_score_v2` weights, thresholds, or order logic **automatically**. |

---

## CSA verdict (exactly one)

**CSA_OPERATIONAL_HARDENING_APPROVED_NON_MUTATING**

---

*End of CSA final certification.*
