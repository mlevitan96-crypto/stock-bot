# ALPACA_INTEGRITY_ARM_STATE_INSPECTION

- **`state/alpaca_milestone_integrity_arm.json` exists:** True
```json
{
  "arm_epoch_utc": null,
  "armed_at_utc_iso": null,
  "session_anchor_et": "2026-04-01"
}
```

- **`arm_epoch_utc` present:** False
- **`session_anchor_et`:** `2026-04-01`

## Milestone 250 state
- **Path:** `/root/stock-bot/state/alpaca_milestone_250_state.json` exists: True
```json
{
  "fired_milestone": false,
  "last_count": 0,
  "session_anchor_et": "2026-04-01"
}
```

## Integrity cycle state (reference)
- **Path:** `/root/stock-bot/state/alpaca_telegram_integrity_cycle.json` exists: True
```json
{
  "cooldowns": {
    "integrity_general": "2026-03-31T03:27:34.681283+00:00"
  },
  "cycle_count": 288,
  "force_next_warehouse": false,
  "last_good": {
    "DATA_READY": null,
    "LEARNING_STATUS": "BLOCKED",
    "coverage_path": "/root/stock-bot/reports/ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260401_1649.md",
    "execution_join_pct": 100.0,
    "fee_pct": 100.0,
    "slippage_pct": 100.0,
    "utc": "2026-04-01T16:49:57.610335+00:00"
  },
  "last_observed": {
    "LEARNING_STATUS": "BLOCKED"
  },
  "version": 1
}
```
