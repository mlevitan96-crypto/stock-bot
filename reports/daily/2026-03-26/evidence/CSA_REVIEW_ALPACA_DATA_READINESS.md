# CSA Review — Alpaca Data Readiness Gate

**Date (UTC):** 2026-03-20  
**Inputs reviewed:** `ALPACA_DATA_SURFACE_INVENTORY.md`, `ALPACA_DATA_INTEGRITY_RESULTS.md`, `ALPACA_TRADE_SUFFICIENCY_VERDICT.md`  
**Authority:** [MEMORY_BANK.md](../../MEMORY_BANK.md) — droplet as truth gate

---

## Verdict

| Flag | Value |
|------|--------|
| **DATA_READY_FOR_AUDIT** | **YES** — **scoped** |

**Scope (mandatory):** Closed-trade **PnL + exit attribution** audits **must** use **`logs/exit_attribution.jsonl`** as the **authoritative** closed-trade source for Alpaca (per MEMORY_BANK Alpaca Data Sources). **Do not** require raw `trade_id` equality with `logs/master_trade_log.jsonl` for this gate — cross-stream IDs are **inconsistent by design** (`open_*` vs `live:*`) and normalized key overlap is negligible.

---

## If interpreted as “strict unified ledger join”

| Check | Result |
|-------|--------|
| Exit ↔ master closed join (normalized keys) | **~1 / 2,204** — **would be NO** |

That stricter interpretation is **not** adopted for this promotion-readiness gate because it conflates **PnL completeness** (satisfied by exit file) with **multi-file reconciliation** (failing until reconciler / ID unification).

---

## Blocking deficiencies (NONE for scoped PnL audit)

1. **Repair / quarantine:** **2** `exit_attribution` rows missing core fields — **block** only for **100% row-complete** claims until fixed.  
2. **Telemetry-backed readiness:** Many rows may still have empty `direction_intel_embed.intel_snapshot_entry` — affects **readiness scoring**, not raw PnL existence.

---

## Authorization

| Action | Allowed |
|--------|---------|
| Full **PnL + exit-side attribution** audit on **`exit_attribution.jsonl`** | **YES** |
| Claim **single unified trade_id** across master + exit without reconciliation tooling | **NO** |

---

## SAFE MODE note

Mission **SAFE MODE** (no strategy tuning / no promotion / no parameter changes until gate passes) is **satisfied for “data gate”**: gate **passes** for scoped data. **Promotion decisions remain frozen** under SAFE MODE until explicitly lifted — see `ALPACA_PROMOTION_DECISION.md`.

---

*CSA — governance gate only; execution remains read-only for audits.*
