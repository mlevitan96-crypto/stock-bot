# PHASE 4 — Freshness & Staleness Audit (SRE)

**Timestamp:** 2026-03-26 ~16:23 UTC  
**Host:** Alpaca droplet  

---

## 1. File mtimes (Unix epoch) and interpretation

Command: `stat -c '%n %Y %s'` on `/root/stock-bot/logs/…`

| File | mtime (epoch) | Size (bytes) | Notes |
|------|---------------|-------------:|-------|
| `alpaca_unified_events.jsonl` | 1774542185 | 3,171,048 | **Fresh** at audit (~same second as other core logs). |
| `orders.jsonl` | 1774542185 | 2,202,547 | **Fresh** |
| `run.jsonl` | 1774542185 | 10,985,007 | **Fresh** |
| `exit_attribution.jsonl` | 1774542185 | 29,234,354 | **Fresh** |
| `alpaca_exit_attribution.jsonl` | 1774542185 | 449,158 | **Fresh** |
| `alpaca_entry_attribution.jsonl` | **1774540271** | 2,720,720 | **Older mtime** (~32 min behind other surfaces at sample) — investigate burst entry emit vs continuous writer. |

**Human time (UTC):** `1774542185` → **2026-03-26 16:23:05 UTC** (approximate).

---

## 2. SLA comparison

Formal numeric **freshness SLA** for each JSONL is **not defined in repo docs audited here** beyond dashboard panel notes (not binding for Alpaca trade logs).  

**Qualitative assessment:**

- Core trading logs (`orders`, `run`, `exit_attribution`, `unified`) moved in lockstep at sample — **not frozen**.  
- `alpaca_entry_attribution.jsonl` **lagged** other writers at the sample — **flag** for partial stall or lower emit frequency.

---

## 3. Workspace contrast (non-production)

Local dev tree under `c:\Dev\stock-bot\logs` (Feb–Jan mtimes on `exit_attribution` / empty `orders`) is **not** live evidence — **droplet stats above are authoritative** for production.

---

## 4. Phase 4 verdict

**PASS with flag:** Writers are active on droplet; **one surface (`alpaca_entry_attribution.jsonl`) showed materially older mtime** than peers at the instant sampled — not fail-closed catastrophic, but **requires monitoring** and CSA SLA if numeric bounds are set.
