# Alpaca SRE auto-repair engine — implementation

**Timestamp:** `20260327_SRE_AUTO_REPAIR_FINAL`

## Module

`scripts/audit/alpaca_sre_auto_repair_engine.py` — `run_sre_auto_repair(root, open_ts_epoch, forward_since_epoch, repair_max_rounds, repair_sleep_seconds, repair_mod=None)`.

## Flow

1. Run strict gate (same parameters as forward truth contract).  
2. If `trades_incomplete == 0` → return gate; `repair_actions_applied` empty.  
3. Classify each incomplete `trade_id` via `alpaca_sre_repair_playbooks.classify_trade`.  
4. If **no** trade is classified as known-repairable (all UNKNOWN) → set `immediate_unknown_escalation`; return without sidecar writes.  
5. Else for each outer round (≤ `repair_max_rounds`): apply `apply_backfill_for_trade_ids` for all incomplete trades **not** classified UNKNOWN; sleep; re-gate; append audit row with before/after `trades_incomplete` and per-tid class map.  
6. Return final gate, full `repair_actions_applied[]`, `classification_per_trade_id`, and `engine_meta`.

## Audit trail fields

- `repair_actions_applied[].round`, `trades_incomplete_before` / `after`, `classification_for_batch`, `applied_trade_ids`, line counts, skips.

## Integration

`alpaca_forward_truth_contract_runner.py` invokes the engine (replacing the subprocess repair loop). Exit codes unchanged: **0** CERT_OK, **2** INCIDENT, **1** precheck / load error / structural.
