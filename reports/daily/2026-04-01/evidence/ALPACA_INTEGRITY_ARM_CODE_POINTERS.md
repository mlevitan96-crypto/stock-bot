# ALPACA_INTEGRITY_ARM_CODE_POINTERS

## Arming writes `state/alpaca_milestone_integrity_arm.json`
- **File:** `telemetry/alpaca_telegram_integrity/milestone.py`
- **Function:** `update_integrity_arm_state(root, session_anchor_et, precheck_ok)`
- **Boolean to set `arm_epoch_utc`:** `precheck_ok is True` AND `st.get('arm_epoch_utc') is None` AND same `session_anchor_et`
- **Reset:** if `session_anchor_et` on disk != current anchor → `arm_epoch_utc` cleared to `None`

## `precheck_ok` source (integrity cycle)
- **File:** `telemetry/alpaca_telegram_integrity/runner_core.py`
- **Function:** `_checkpoint_100_integrity_ok(cov, strict, cov_reasons, schema_reasons, max_age_h)`
- **Passes only if `len(bad)==0` where `bad` accumulates:**
  1. `cov.path is None` → `missing_coverage_artifact`
  2. `cov.age_hours > max_age_h` → stale coverage
  3. `cov.data_ready_yes is not True` → DATA_READY not YES
  4. all strings in `cov_reasons` (thresholds + stale_or_missing_warehouse_coverage from runner)
  5. all strings in `schema_reasons` (exit tail probe: missing field in > max(5, lines/4) rows)
  6. `strict.get('LEARNING_STATUS') != 'ARMED'`

## Milestone snapshot when unarmed
- **File:** `telemetry/alpaca_telegram_integrity/milestone.py` — `build_milestone_snapshot`
- **Condition:** `counting_basis == 'integrity_armed'` and `arm_epoch_utc is None` → `integrity_armed=False`, `unique_closed_trades=0`

## Integrity cycle entrypoint
- **Script:** `scripts/run_alpaca_telegram_integrity_cycle.py` → `telemetry.alpaca_telegram_integrity.runner_core.run_integrity_cycle`
- **systemd:** `deploy/systemd/alpaca-telegram-integrity.service` + `.timer`

## ripgrep (telemetry/scripts/src)
### Pattern: `milestone_counting_basis`

```
(no matches)
```

### Pattern: `integrity_armed`

```
(no matches)
```

### Pattern: `alpaca_milestone_integrity_arm`

```
(no matches)
```

### Pattern: `arm_epoch_utc`

```
(no matches)
```

### Pattern: `build_milestone_snapshot`

```
(no matches)
```

### Pattern: `MilestoneSnapshot`

```
(no matches)
```

