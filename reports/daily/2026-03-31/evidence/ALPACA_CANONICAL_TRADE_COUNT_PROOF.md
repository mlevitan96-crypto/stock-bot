# ALPACA_CANONICAL_TRADE_COUNT_PROOF

## Function
- `src/governance/canonical_trade_count.py` — `compute_canonical_trade_count(root, floor_epoch=None|float)`

## Current snapshot (this run, no floor)

```json
{
  "total_trades_post_era": 0,
  "realized_pnl_sum_usd": 0,
  "last_exit_timestamp_utc": null,
  "next_milestone": 100,
  "remaining_to_next_milestone": 100,
  "trades_to_100": 100,
  "trades_to_250": 250,
  "sample_trade_keys": [],
  "era_cut_excluded_rows": 36,
  "floor_excluded_rows": 0,
  "skipped_no_trade_key": 0,
  "floor_epoch_utc": null
}
```

- **total_trades_post_era:** 0
- **trades_to_100 (distance):** 100
- **trades_to_250 (distance):** 250
- **next_milestone:** 100
- **remaining_to_next_milestone:** 100

## Consumers wired in repo
- Telegram milestones: `telemetry/alpaca_telegram_integrity/milestone.py`
- Dashboard `/api/situation`: `dashboard.py` `_get_situation_data_sync`
- Run this script for audit evidence bundles.
