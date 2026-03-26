# Alpaca Promotion Decision — Data Readiness Gate

**UTC:** 2026-03-20  
**Gate:** ALPACA DATA READINESS & INTEGRITY (pre-promotion)  
**DATA_READY_FOR_AUDIT (scoped):** YES — see `CSA_REVIEW_ALPACA_DATA_READINESS.md`

---

## Decision

| Item | Decision |
|------|----------|
| **Promote one indicator/rule to LIVE PAPER (PROMOTED)** | **NO — DEFERRED** |
| **Reason** | Mission **SAFE MODE**: *“No strategy tuning, no promotion, no parameter changes until gate passes.”* The **data readiness** gate passes **for scoped PnL audit**; **promotion** remains **explicitly frozen** until SAFE MODE is lifted by authority outside this document. |
| **Shadow vs LIVE** | **No change** — all strategy experiments remain **SHADOW** or existing LIVE_PAPER state unchanged. |

---

## Optional learning promotion (LEARNING PROMOTION)

| Item | Decision |
|------|----------|
| **Diagnostic LEARNING PROMOTION** | **Not applied** — same SAFE MODE freeze. |

---

## Preconditions for future promotion (when allowed)

1. Quarantine or fix **2** defective rows in `logs/exit_attribution.jsonl`.  
2. Run ranked effectiveness / board shortlist on droplet (`alpaca_edge_2000` or successor) with **frozen inputs**.  
3. Human approval + CSA sign-off per `docs/ALPACA_PHASE4_PROMOTION_GATE_PLAN.md` / promotion gate state.

---

*CSA/SRE/Quant — no PROMOTED label assigned in this cycle.*
