# STOP-GATE 2 — CSA Final Verdict (mandatory)

**Certification:** ALPACA TRADE DATA COLLECTION — PROVE OR FAIL CLOSED  
**Closeout time:** 2026-03-26 ~16:23 UTC  
**Operator:** Cursor automated audit + droplet SSH evidence  

---

## Verdict (choose one)

### **NO-GO**

**Alpaca trade data collection is not certified** as complete, uniformly joinable, and safe for **strict causal / learning** use **under the repo’s fail-closed gate and the CSA “PERFECT DATA COLLECTION” definition** without explicit exceptions.

---

## Exact blockers (must clear before trading for data-certification purposes)

1. **Unified terminal coverage gap:** In the last **72h**, **252** distinct `trade_id` had `alpaca_exit_attribution` + `terminal_close` in `alpaca_unified_events.jsonl` vs **682** closes in `exit_attribution.jsonl` — ratio **~0.37**. Clause **A/B** of the CSA contract is **not met** for the unified stream.  
   - **Artifact:** `reports/ALPACA_EVENT_FLOW_COUNTS_20260326_1622Z.json`, `reports/audit/ALPACA_EVENT_FLOW_COUNTS_20260326_1622Z.md`

2. **Strict completeness BLOCKED:** Post-epoch cohort: **192** trades seen, **76** complete, **116** incomplete; `learning_fail_closed_reason: incomplete_trade_chain`.  
   - **Artifact:** `reports/ALPACA_STRICT_COMPLETENESS_GATE_20260326_1622Z.json`, Phase 3 audit markdown.

3. **Decision / exit_intent join failures:** **116** occurrences of `entry_decision_not_joinable_by_canonical_trade_id`; **92** of `missing_exit_intent_for_canonical_trade_id` — breaks **C)** unless CSA narrows the certified path to legacy profitability logs only.

4. **Canonical key inconsistency (sample):** Live unified exit tail shows **`trade_key` vs `canonical_trade_id` mismatch** on at least one production row (HOOD) — risk for **duplicate or partial joins**.

5. **Operational reconciliation risk:** Log evidence of **Alpaca positions not reflected in local state** at sample time — undermines confidence in execution ↔ state ↔ logs alignment.

6. **Human CSA stop-gate 0:** Contract in `reports/audit/ALPACA_DATA_COMPLETENESS_CONTRACT_CSA_20260326.md` is **proposed** — **no human CSA approval** recorded in this run.

---

## What *is* in reasonable shape (context only — does not override NO-GO)

- **Droplet services** `stock-bot`, `uw-flow-daemon`, `stock-bot-dashboard` were **active**; core JSONLs **updated** at audit instant.  
- **`orders.jsonl` non-empty** (3,981 lines total on host) — unlike empty dev snapshots.  
- **Profitable PnL review** may still use `exit_attribution.jsonl` per prior summaries — **that is a narrower goal** than this certification.

---

## Recommended next actions (diagnostic / governance — not trading logic)

1. **Human CSA:** Approve or revise `ALPACA_DATA_COMPLETENESS_CONTRACT_CSA_20260326.md`.  
2. **Engineering (with CSA approval):** Align `trade_intent` / `canonical_trade_id_resolved` / `exit_intent` emission with live enters and exits; or **widen** the strict gate with documented exceptions.  
3. **Backfill / forward fix:** Raise unified `alpaca_exit_attribution` + `terminal_close` coverage to **parity** with `exit_attribution` for the certified window **or** formally exclude pre-emit era with cutoff dates.  
4. **Investigate** HOOD-class `trade_key` vs `canonical_trade_id` divergence.  
5. **Re-run** this certification pack (all phases) after fixes; require **strict gate ARMED** and unified/exist ratio **≈1** (per CSA tolerance).

---

## Artifact index

| Artifact |
|----------|
| `reports/audit/ALPACA_DATA_COMPLETENESS_CONTRACT_CSA_20260326.md` |
| `reports/audit/ALPACA_DATA_PIPELINE_HEALTH_20260326_1622Z.md` |
| `reports/audit/ALPACA_EVENT_FLOW_COUNTS_20260326_1622Z.md` |
| `reports/ALPACA_EVENT_FLOW_COUNTS_20260326_1622Z.json` |
| `reports/audit/ALPACA_JOIN_INTEGRITY_AUDIT_20260326_1622Z.md` |
| `reports/audit/ALPACA_DATA_FRESHNESS_AUDIT_20260326_1622Z.md` |
| `reports/audit/ALPACA_DATA_FAILURE_MODES_20260326_1622Z.md` |
| `reports/audit/ALPACA_DATA_ADVERSARIAL_REVIEW_20260326_1622Z.md` |
| `reports/ALPACA_STRICT_COMPLETENESS_GATE_20260326_1622Z.json` |
| `scripts/audit/alpaca_event_flow_audit.py` |

---

### CSA signature line (human)

- [ ] **DATA_COLLECTION_CERTIFIED** — *Not selected.*  
- [x] **NO-GO** — As above.

**Signed:** _________________________ **Date:** ___________
