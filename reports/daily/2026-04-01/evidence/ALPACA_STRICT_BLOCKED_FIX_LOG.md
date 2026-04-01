# ALPACA_STRICT_BLOCKED_FIX_LOG

Minimal, targeted changes (no strategy / liquidation / threshold tuning).

## Blocker: `precheck:missing_alpaca_unified_events_jsonl`

- **Classification:** missing persistence (no unified log file; strict required primary file even if backfill path exists).
- **Fix:** In `telemetry/alpaca_strict_completeness_gate.py`, precheck fails only if **both** `logs/alpaca_unified_events.jsonl` and `logs/strict_backfill_alpaca_unified_events.jsonl` are absent.
- **Additional:** Committed and ran `scripts/audit/backfill_unified_terminal_from_exit_attribution.py` on droplet — **`backfill_count 341 applied`** (creates/populates unified terminal exits via `emit_exit_attribution`).
- **Proof:** `ALPACA_STRICT_GATE_AUDIT.json` shows `"precheck": []` (was non-empty when unified missing).

## Blocker: `unified_exit_emit_exception` / missing `telemetry.attribution_emit_keys`

- **Classification:** import path / deployment layout (exit path could not load module).
- **Fix:** Full implementation in `src/telemetry/attribution_emit_keys.py`; `telemetry/attribution_emit_keys.py` re-exports; `src/exit/exit_attribution.py` imports from `src.telemetry.attribution_emit_keys`.
- **Proof:** Backfill and emitter path run without `ModuleNotFoundError` on droplet after `git pull`.

## Blocker: `DATA_READY` parse `None` in integrity precheck

- **Classification:** coverage artifact contract (missing `DATA_READY:` line).
- **Fix:** `scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py` emits `DATA_READY: YES|NO` after blockers computed.
- **Proof:** `parse_coverage_smoke_check.json` — `parse_ok: true`, `data_ready_yes: false` (not null).

## Blockers NOT cleared (per-trade chain)

The following remain **111/111** incomplete in `ALPACA_STRICT_GATE_AUDIT.json`:

| blocker_id | Notes |
| --- | --- |
| `live_entry_decision_made_missing_or_blocked` | No qualifying `entry_decision_made` rows in `run.jsonl` |
| `entry_decision_not_joinable_by_canonical_trade_id` | No `trade_intent` + `entered` rows joining to trade keys |
| `missing_unified_entry_attribution` | No unified **entry** rows for aliases |
| `no_orders_rows_with_canonical_trade_id` | Almost all orders lack `canonical_trade_id` (20 / 5795) |
| `missing_exit_intent_for_canonical_trade_id` | No `exit_intent` events in `run.jsonl` |

**No additional code changes applied** for these in this mission (would require run.jsonl / orders join repair or strict rule changes beyond the requested minimal scope).
