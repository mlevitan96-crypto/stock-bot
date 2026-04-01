# Milestone snapshot proof (250 target, eligibility only)

Source: `scripts/run_alpaca_telegram_integrity_cycle.py --dry-run` output `chain_fix_mission/ALPACA_INTEGRITY_CYCLE_DRYRUN_FULL.json`.

## `integrity_armed` counting basis

- `milestone.counting_basis`: `integrity_armed`
- `milestone.integrity_armed`: **false**
- `milestone.unique_closed_trades`: **0**
- `milestone.count_floor_utc_iso`: `(not armed — waiting for green DATA_READY + coverage + strict ARMED + exit probe)`

## Floored to zero?

**YES** — under `integrity_armed` basis, `unique_closed_trades` stays **0** until `arm_epoch_utc` is set. Strict is **ARMED**, exit probe passed, but **DATA_READY** is **NO**, so `precheck_ok` stays false and the arm epoch is not written.

## `should_fire` / Telegram

Dry-run did not send Telegram. With `unique_closed_trades=0`, milestone **250** cannot fire regardless of template logic.

## Counterfactual (not executed)

If governance switched `milestone_counting_basis` to `session_open`, the snapshot would count from regular session open without integrity arm — **policy change only**, out of scope for this chain mission.
