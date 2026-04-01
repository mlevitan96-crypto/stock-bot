# ALPACA_STRICT_BLOCKED_ROOT_CAUSE

## Strict gate implementation

| Item | Location |
| --- | --- |
| **Evaluator** | `telemetry/alpaca_strict_completeness_gate.py` — `evaluate_completeness(...)` |
| **Integrity caller** | `telemetry/alpaca_telegram_integrity/checks.py` — `run_strict_completeness(root)` |
| **Primary artifacts** | JSON stdout from `scripts/alpaca_strict_completeness_gate.py --audit`; integrity cycle embeds subset in `run_integrity_cycle` output |

## Status (post-pull, 2026-04-01 UTC)

From `ALPACA_STRICT_GATE_AUDIT.json`:

- **`LEARNING_STATUS`:** `BLOCKED`
- **`learning_fail_closed_reason`:** `incomplete_trade_chain`
- **`precheck`:** `[]` (was `missing_alpaca_unified_events_jsonl` before primary file + backfill; see fix log)
- **`trades_seen`:** 111  
- **`trades_complete`:** 0  
- **`trades_incomplete`:** 111  

## Precheck identifiers (when they fire)

Defined in `evaluate_completeness` (same file): `missing_exit_attribution_jsonl`, `missing_alpaca_unified_events_jsonl` (only if **both** `logs/alpaca_unified_events.jsonl` and `logs/strict_backfill_alpaca_unified_events.jsonl` absent), `missing_orders_jsonl`, `missing_run_jsonl`.

## Failing per-trade checks (stable names)

From `reason_histogram` (all 111 trades share the same set):

| Blocker ID | Reads | Expected | Observed (sample) | Code pointer |
| --- | --- | --- | --- | --- |
| `live_entry_decision_made_missing_or_blocked` | `logs/run.jsonl` (+ backfill) `event_type == entry_decision_made` | Row passing `audit_entry_decision_made_row_ok` for opens ≥ `LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH` (2026-03-28 UTC) | `grep -c entry_decision_made run.jsonl` → **0** on droplet | ```347:358:telemetry/alpaca_strict_completeness_gate.py``` |
| `entry_decision_not_joinable_by_canonical_trade_id` | Same stream: `trade_intent` with `decision_outcome == entered` | Row for symbol with `canonical_trade_id` or `trade_key` in alias set for trade | **0** `trade_intent` with `entered` in `run.jsonl` (only 3 `trade_intent`, all `blocked` in sampled head) | ```360:367:telemetry/alpaca_strict_completeness_gate.py``` |
| `missing_unified_entry_attribution` | `logs/alpaca_unified_events.jsonl` (+ backfill): `event_type == alpaca_entry_attribution` | At least one unified entry row keyed by an alias | Backfill added **exit** terminals only; no matching entry rows for these keys | ```368:368:telemetry/alpaca_strict_completeness_gate.py``` |
| `no_orders_rows_with_canonical_trade_id` | `logs/orders.jsonl` (+ backfill): `canonical_trade_id` on order rows | Order rows grouped by `canonical_trade_id` intersecting aliases | `5795` order rows, **`20`** with `canonical_trade_id` (droplet count) | ```369:369:telemetry/alpaca_strict_completeness_gate.py``` |
| `missing_exit_intent_for_canonical_trade_id` | `run.jsonl`: `event_type == exit_intent` | Exit intent rows keyed by alias | `grep -c exit_intent run.jsonl` → **0** | ```370:370:telemetry/alpaca_strict_completeness_gate.py``` |

### Sample incomplete row

```json
{
  "trade_id": "open_AMD_2026-04-01T13:37:47.001990+00:00",
  "trade_key": "AMD|LONG|1775050667",
  "reasons": [
    "live_entry_decision_made_missing_or_blocked",
    "entry_decision_not_joinable_by_canonical_trade_id",
    "missing_unified_entry_attribution",
    "no_orders_rows_with_canonical_trade_id",
    "missing_exit_intent_for_canonical_trade_id"
  ]
}
```

(Full list in `ALPACA_STRICT_GATE_AUDIT.json`.)

## Prior hard failure (resolved for precheck only)

- **`unified_exit_emit_exception`** in `run.jsonl`: `ModuleNotFoundError: telemetry.attribution_emit_keys` from `src/exit/exit_attribution.py` — addressed by canonical module under `src/telemetry/attribution_emit_keys.py` and import fix (see fix log).

## Command used

```bash
cd /root/stock-bot && PYTHONPATH=. python3 scripts/alpaca_strict_completeness_gate.py --root /root/stock-bot --audit
```

Output captured: `ALPACA_STRICT_GATE_AUDIT.json`.
