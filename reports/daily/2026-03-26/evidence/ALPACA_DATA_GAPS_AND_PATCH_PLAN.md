# Alpaca Data Gaps & Patch Plan (SRE / CSA)

**Context:** Produced alongside the data-readiness gate. **Scoped DATA_READY = YES** still applies for `exit_attribution`-first PnL work; this document tracks **reconciliation** and **telemetry completeness** gaps.

---

## 1. Gaps observed (droplet, 2026-03-20)

| Gap | Severity | Detail |
|-----|----------|--------|
| **2 bad rows** in `exit_attribution.jsonl` | **High** for strict completeness | Missing symbol, trade_id, PnL, timestamps, `direction_intel_embed` |
| **Raw `trade_id` mismatch** exit vs master | **High** for naive joins | 0 intersection — `open_*` vs `live:*` |
| **Normalized key overlap** exit vs master closed | **High** for unified ledger | **1** match in ~2.2k exits vs 160 master closes |
| **`attribution.jsonl` vs `exit_attribution`** drift | **Medium** | ~1.1k closed attribution keys not in exit key set |
| **`alpaca_exit_attribution.jsonl`** | **Low** (empty) | Emitter not writing; rely on main exit_attribution |
| **`exit_event.jsonl`** | **Low** (empty) | Unified replay path optional |
| **`alpaca_unified_events.jsonl`** vs exit volume | **Medium** | 233 vs 2,209 — partial unified history |

---

## 2. Patch plan (no execution in SAFE MODE)

1. **Quarantine bad lines:** Identify line numbers for the 2 defective JSONL rows; fix upstream writer or add validation in `append_exit_attribution` path so incomplete rows never append.  
2. **ID harmonization:** On exit write, emit **`live:SYMBOL:normalized_entry_ts`** as `trade_id` (or dual-write `stable_trade_id`) to match `master_trade_log` — see `main.py` stable_trade_id patterns.  
3. **Reconciliation job:** Scheduled `telemetry/exit_join_reconciler.py` + manifest diff report: exits without master, master closed without exit.  
4. **Dual-write audit:** Align `attribution.jsonl` close rows with `exit_attribution` keys or document intentional divergence (e.g. experiment-only).  
5. **Unified stream:** Ensure `emit_entry_attribution` / `emit_exit_attribution` run on all paths so `alpaca_unified_events.jsonl` tracks exit volume over time.

---

## 3. Additional trades / time

**Not required** for minimum N — already **2,204** unique closes. Additional calendar span helps **regime diversity**, not raw N.

---

*Patch execution deferred to post–SAFE MODE SRE work.*
