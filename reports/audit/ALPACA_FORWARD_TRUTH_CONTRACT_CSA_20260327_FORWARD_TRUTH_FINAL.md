# CSA — Alpaca forward truth contract (parameters)

**Timestamp:** `20260327_FORWARD_TRUTH_FINAL`  
**Scope:** Alpaca only. No strategy changes. No gate relaxation. Additive repair only.

## Contract parameters (authoritative defaults)

| Parameter | Value |
|-----------|-------|
| `forward_window_hours` | 72 |
| `schedule` | Every 15 minutes (systemd timer) |
| `repair_max_rounds` | 6 (outer iterations; each invokes additive repair subprocess) |
| `repair_sleep_seconds` | 10 (between repair iteration and re-gate) |
| `repair_internal_rounds_per_iteration` | 1 (flush rounds per subprocess; keeps re-gates aligned with bounded repair) |
| `incident_if_incomplete_after_rounds` | true |
| `incident_severity` | LEARNING_BLOCKER |
| `strict_epoch_policy` | **Explicit policy C:** `open_ts_epoch = max(STRICT_EPOCH_START, now − forward_window_hours)` so the rolling window never starts before the module strict era constant (`telemetry/alpaca_strict_completeness_gate.STRICT_EPOCH_START`). `forward_since_epoch` is set equal to `open_ts_epoch` so forward/legacy split matches the same floor. |

## Success criteria (operational)

1. Scheduled job runs on the droplet and produces timestamped artifacts each invocation.  
2. If `trades_incomplete > 0`, bounded repair runs and the gate re-evaluates after each iteration.  
3. If incompletes persist, deterministic **INCIDENT** JSON + MD with trade_ids, reason histogram, recoverability, and next-action hints.  
4. If `trades_incomplete == 0`, **CERT_OK** in run JSON + MD.  
5. Exit codes: `0` = OK, `2` = incident, `1` = precheck/structural/timeout.

## Canonical implementation

- Runner: `scripts/audit/alpaca_forward_truth_contract_runner.py`  
- Strict gate: `telemetry/alpaca_strict_completeness_gate.py` (`evaluate_completeness`)  
- Additive repair: `scripts/audit/alpaca_strict_six_trade_additive_repair.py` (`--repair-all-incomplete-in-era`, `--max-repair-rounds`)  
- Scheduler: `deploy/systemd/alpaca-forward-truth-contract.{service,timer}` + `alpaca-forward-truth-contract-run.sh`
