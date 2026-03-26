# Phase 4 — Freshness and staleness audit (SRE)

**Artifact:** `ALPACA_DATA_FRESHNESS_AUDIT_20260326_2015Z`  
**Method:** PowerShell `Get-Item` on `logs/*.jsonl` (UTC mtime). **Droplet not accessed.**

**Audit wall clock (approx):** 2026-03-26T16:27Z (during certification run).

---

## Surfaces

| File | Size (bytes) | Last write (UTC) | Age vs audit (approx) | Assessment |
|------|-------------:|------------------|------------------------|------------|
| alpaca_unified_events.jsonl | 88,575 | 2026-03-25T22:53:25Z | ~17.5 h | **Fresh** for dev activity |
| alpaca_entry_attribution.jsonl | 15,428 | 2026-03-25T22:53:25Z | ~17.5 h | **Fresh** |
| alpaca_exit_attribution.jsonl | 18,309 | 2026-03-25T22:53:25Z | ~17.5 h | **Fresh** |
| run.jsonl | 156,876 | 2026-01-27T22:56:13Z | ~58 d | **STALE** vs Alpaca streams |
| orders.jsonl | **0** | 2026-01-27T02:04:30Z | **Frozen / empty** | **BLOCKED** for execution truth |
| exit_attribution.jsonl | 38,088 | 2026-02-17T23:30:51Z | ~37 d | **STALE** vs Alpaca streams |

---

## SLA

Numeric SLA was not fixed in CSA contract text (`ALPACA_DATA_COMPLETENESS_CONTRACT_CSA_20260326.md`).  
**Operational rule used here:** Alpaca telemetry files should not lag **trading + unified** writers by more than **one session day** without explicit STALE banner elsewhere.

---

## Verdict (Phase 4)

**FRESHNESS: FAILED** for an integrated pipeline: `run.jsonl`, `orders.jsonl`, and `exit_attribution.jsonl` are **not co-moving** with `alpaca_*` logs in this workspace.  
**Droplet:** re-measure mtimes under live trading load.
