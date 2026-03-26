# PHASE 3 — Unified Terminal Emission Parity (Engineering)

**Timestamp:** 2026-03-26

---

## Objective

Every economic close that appends `exit_attribution.jsonl` continues to invoke `emit_exit_attribution(..., terminal_close=True)` with **consistent** `trade_key` / `canonical_trade_id` from the exit row (Phase 2), so unified `alpaca_exit_attribution` rows align with broker truth.

---

## Changes

1. **`src/exit/exit_attribution.py`**
   - Row-level **`trade_key` / `canonical_trade_id`** drive unified emit (see Phase 2).

2. **`src/telemetry/alpaca_attribution_emitter.py`**
   - On **schema validation failure** for exit, append one JSON line to **`logs/alpaca_emit_failures.jsonl`** (in addition to existing `emit_learning_blocker` + diag hook).
   - **No silent drop:** operator-visible audit trail when unified line is skipped.

3. **Operational backfill**
   - `scripts/audit/backfill_unified_terminal_from_exit_attribution.py` for historical rows missing unified terminal (dry-run by default).

---

## Residual gap (documented)

- **Past** closes emitted before this deploy may still lack unified terminals until **backfill** is run once on the droplet.
- Forward path (post-deploy) is expected to emit on every `append_exit_attribution` call that reaches `emit_exit_attribution`.
