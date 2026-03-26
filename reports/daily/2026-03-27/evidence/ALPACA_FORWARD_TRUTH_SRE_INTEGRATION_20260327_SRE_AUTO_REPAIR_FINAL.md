# Forward truth contract ↔ SRE auto-repair integration

**Timestamp:** `20260327_SRE_AUTO_REPAIR_FINAL`

## Change

`scripts/audit/alpaca_forward_truth_contract_runner.py` loads `alpaca_sre_auto_repair_engine` via importlib and calls `run_sre_auto_repair` instead of spawning `alpaca_strict_six_trade_additive_repair.py` in a subprocess loop.

## Preserved behavior

- Rolling window: `open_ts_epoch = max(STRICT_EPOCH_START, now − window_hours)`.  
- Bounded iterations: `repair_max_rounds`, `repair_sleep_seconds`.  
- Exit **0** / **2** / **1** semantics.  
- CERT_OK / INCIDENT artifacts and incident JSON fields.

## New JSON fields (run record)

- `sre_auto_repair_engine: true`  
- `sre_repair_actions_applied` (audit trail; same array also under `repair_trace` for continuity)  
- `sre_classification_per_trade_id`  
- `sre_engine_meta` (`initial_trades_incomplete`, `immediate_unknown_escalation`, `rounds_executed`, …)  
- Incident: `sre_classification_sample`, `sre_immediate_unknown_escalation`, `sre_actions_count`

## UNKNOWN handling

Trades classified **UNKNOWN** never receive additive playbook application. If every incomplete trade is UNKNOWN, **no** repair rounds run (`immediate_unknown_escalation`). Mixed cohorts: only known-classified trades are backfilled each round.
