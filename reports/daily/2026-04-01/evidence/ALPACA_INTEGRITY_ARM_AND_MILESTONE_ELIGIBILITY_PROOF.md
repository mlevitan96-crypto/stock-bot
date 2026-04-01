# ALPACA_INTEGRITY_ARM_AND_MILESTONE_ELIGIBILITY_PROOF

## Entrypoint

`scripts/run_alpaca_telegram_integrity_cycle.py` → `telemetry/alpaca_telegram_integrity/runner_core.py` — `run_integrity_cycle` calls `update_integrity_arm_state(root, anchor_et, cp_ok)` when `milestone_counting_basis == integrity_armed`.

## Run

```bash
cd /root/stock-bot && PYTHONPATH=. python3 scripts/run_alpaca_telegram_integrity_cycle.py \
  --root /root/stock-bot --dry-run --skip-warehouse
```

Captured: `ALPACA_INTEGRITY_CYCLE_DRYRUN.json`.

## `arm_epoch_utc` for session anchor ET

From dry-run output:

- **`session_anchor_et`:** `2026-04-01`
- **`milestone_integrity_arm.arm_epoch_utc`:** **`null`**
- **`milestone_integrity_arm.armed_at_utc_iso`:** **`null`**

**Reason:** `checkpoint_100_precheck_ok`: **false** with:

- `DATA_READY not YES (or unknown)` / `DATA_READY reported NO in latest coverage artifact`
- `strict LEARNING_STATUS is not ARMED (got 'BLOCKED')`

So `update_integrity_arm_state` did **not** arm (`milestone.py`: arm only when `precheck_ok` is true and `arm_epoch_utc` still null).

## Milestone snapshot (integrity_armed basis)

From same JSON:

- **`milestone_counting_basis`:** `integrity_armed`
- **`milestone.integrity_armed`:** **false**
- **`milestone.unique_closed_trades`:** **0** (floored until armed — `count_floor_utc_iso` shows not-armed message)
- **`milestone.realized_pnl_sum_usd`:** `0.0`

## 250 milestone `should_fire`

With **`unique_closed_trades == 0`** and target **250**, **`should_fire` is false** regardless of `fired_milestone` state. Formal `should_fire_milestone` from `telemetry/alpaca_telegram_integrity/milestone.py` was not separately executed here; integrity output already shows count 0 and not armed.

## Conclusion

**Session is not armed** (`arm_epoch_utc` unset). **250 milestone is not eligible** under `integrity_armed` counting until DATA_READY + strict ARMED + checkpoint precheck pass and non-zero post-arm counts apply.
