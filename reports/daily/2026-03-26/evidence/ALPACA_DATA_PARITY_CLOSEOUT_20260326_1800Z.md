# STOP-GATE — CSA Final Verdict: Alpaca Data Parity Repair

**Timestamp:** 2026-03-26  
**Mission:** ALPACA DATA PARITY REPAIR — RUN FORWARD UNTIL STRICT GATE PASSES

---

## Verdict

### **STILL_BLOCKED**

Engineering fixes are **implemented in the workspace** and **synthetic strict-gate proof passes**, but **production strict completeness is not yet certified** because:

1. **Droplet reran the gate with pre-deploy code** — result still **BLOCKED** (81/197 complete, ~41% coverage). See `reports/audit/ALPACA_STRICT_GATE_RERUN_20260326_1800Z.md`.
2. **Historical `run.jsonl` does not contain post-fix `trade_intent` / `trade_key` rows** for already-closed trades; strict gate will keep failing those IDs until logs age out or a **separate approved backfill** for `run.jsonl` is executed (not implemented — higher risk than unified backfill).
3. **Unified historical parity** may require one-time **`backfill_unified_terminal_from_exit_attribution.py`** on the droplet after review.

---

## What was delivered (telemetry-only)

- Canonical alignment: **trade_intent(entered) after mark_open** with metadata-derived id.
- Exit row + unified emit: **row-level `trade_key` / `canonical_trade_id`**, clearer emit failure log.
- Gate: **`trade_key` on intents + exit_intent indexing**.
- SRE: **cache atomic write hardening**, **dashboard timestamp** fix.
- **Tests + optional unified backfill script.**

---

## Remaining defects (must clear for DATA_PARITY_RESTORED)

| # | Item | Owner action |
|---|------|----------------|
| 1 | **Deploy** repair to Alpaca host and **restart** `stock-bot.service` | Ops |
| 2 | **Re-run** strict gate on droplet with same epoch | SRE |
| 3 | **Optional:** unified terminal **backfill** (script; dry-run first) | CSA-approved ops |
| 4 | **Optional:** `run.jsonl` historical repair or **wait for cohort rollover** | CSA policy |
| 5 | Monitor **`logs/alpaca_emit_failures.jsonl`** after deploy | SRE |

---

## CSA signature line

- [ ] **DATA_PARITY_RESTORED** — *Deferred until post-deploy gate PASS.*  
- [x] **STILL_BLOCKED** — As above.

**Signed:** _________________________ **Date:** ___________
