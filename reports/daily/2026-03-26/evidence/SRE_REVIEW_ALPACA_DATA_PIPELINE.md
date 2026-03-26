# SRE Review — Alpaca Data Pipeline

**UTC:** 2026-03-20 · **Droplet:** `/root/stock-bot` · **commit:** `28abc2a33e365caa58736b99a175ae360f9d1447`

---

## Plumbing correctness

| Path | Status | Notes |
|------|--------|-------|
| `logs/exit_attribution.jsonl` | **OK** (append-only, 2,209 lines) | Canonical closed-trade sink per MEMORY_BANK |
| `logs/master_trade_log.jsonl` | **OK** | Larger lineage log; ID scheme differs from exit |
| `logs/attribution.jsonl` | **OK** | Dual-write drift vs exit for subset of closes |
| `logs/alpaca_unified_events.jsonl` | **Partial** | 233 lines — not full parity with exit volume |
| Retention-protected paths | **Policy** | Per `docs/DATA_RETENTION_POLICY.md` — supervisor must skip destructive rotation |

---

## Completeness vs design

- **2** malformed exit rows — **writer/guard** should reject incomplete records.  
- **Join keys:** Pipeline is **not** “incorrect” for using `live:*` in master and `open_*` in exit — but **operators** must not assume raw join without normalization (documented in inventory).

---

## SRE sign-off

**Data plumbing (ingest + retention policy alignment):** **OK with follow-ups** listed in `ALPACA_DATA_GAPS_AND_PATCH_PLAN.md`.

---

*SRE*
