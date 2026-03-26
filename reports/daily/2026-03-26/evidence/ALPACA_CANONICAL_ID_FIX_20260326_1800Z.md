# PHASE 2 — Canonical ID Unification (Engineering)

**Timestamp:** 2026-03-26

---

## Objective

Single canonical join string (`symbol|SIDE|entry_epoch`) aligned across intent, metadata, orders, exit rows, and unified events.

---

## Changes (code)

1. **`_emit_trade_intent`**
   - New optional `canonical_trade_id_override`.
   - When `decision_outcome=entered` and override set, **stores and emits that id** (no `datetime.now()` anchor).
   - Adds **`trade_key`** field to `run.jsonl` (same value as canonical when known).

2. **Entry path (filled immediate)**
   - **`trade_intent(entered)` moved to after `mark_open` + `emit_entry_attribution`.**
   - Override resolved from **`position_metadata.canonical_trade_id`**, else **`build_trade_key(symbol, side, entry_ts)`** from metadata `entry_ts`.
   - Logs `telemetry.trade_intent_missing_canonical_after_mark_open` if neither is available.

3. **`mark_open` / `_persist_position_metadata`**
   - Unchanged formula: `build_trade_key(symbol, normalize_side(...), entry_ts)` — remains source of truth after fill.

4. **`log_exit_attribution`**
   - Merges **`canonical_trade_id`, `decision_event_id`, `entry_ts`, …** from `position_metadata.json` into the working `metadata` dict before exit processing.
   - **`exit_attribution` record** gets explicit **`canonical_trade_id` / `trade_key`** when derivable from merged metadata + `entry_ts_iso_attr`.

5. **`append_exit_attribution`**
   - Prefers **`rec["trade_key"]` / `rec["canonical_trade_id"]`** before recomputing / in-memory symbol keys.

6. **Post-exit**
   - **`clear_symbol_attribution_keys(symbol)`** after `_emit_exit_intent` to prevent stale per-symbol state.

---

## Backfill

- **Deterministic unified terminal backfill** (optional operator action):  
  `scripts/audit/backfill_unified_terminal_from_exit_attribution.py`  
  (`--dry-run` first). Does **not** rewrite `run.jsonl` (historical intent/exit_intent gaps remain until new trades).

---

## Files touched

- `main.py`
- `src/exit/exit_attribution.py`
- `telemetry/attribution_emit_keys.py` (consumer only; `clear_symbol_attribution_keys` now used)
