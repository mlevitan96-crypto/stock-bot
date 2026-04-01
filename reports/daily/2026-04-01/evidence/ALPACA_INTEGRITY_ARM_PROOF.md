# Integrity arm proof (session `2026-04-01`)

## Commands

```bash
cd /root/stock-bot
PYTHONPATH=. python3 scripts/run_alpaca_telegram_integrity_cycle.py --root /root/stock-bot --dry-run
```

## Result: **NOT armed**

From `chain_fix_mission/ALPACA_INTEGRITY_CYCLE_DRYRUN_FULL.json`:

- `checkpoint_100_precheck_ok`: **false**
- `checkpoint_100_precheck_reasons`: includes **"DATA_READY reported NO in latest coverage artifact"**
- `milestone_integrity_arm.arm_epoch_utc`: **null**
- `state/alpaca_milestone_integrity_arm.json`: updated with `session_anchor_et` but **no** `arm_epoch_utc` until `precheck_ok` (see `telemetry/alpaca_telegram_integrity/milestone.py:update_integrity_arm_state`).

## Single remaining governance blocker (for arming)

**Warehouse `DATA_READY: NO`** driven by **blocked_candidate_coverage_pct ≈ 21.66%** in `ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1745.md`. Strict chain repair does not change this gate.

**Strict status:** **ARMED** (independent axis).
