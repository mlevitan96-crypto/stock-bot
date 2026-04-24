# HYPOTHESIS_COUNCIL_PHASE0_CONTEXT

## Baseline

- **git HEAD:** `e03f25ef06483e6e0157228d6821613aeac4085f`
- **systemctl stock-bot:** exit code `0` (see JSON for full text cap)
- **Evidence dir:** `/root/stock-bot/reports/daily/2026-04-01/evidence`

## Blocked-trades scan (displacement_blocked)

```json
{
  "displacement_blocked_rows_in_file": 5719,
  "unique_calendar_days_in_timestamp_prefix": 3,
  "first_timestamp_sample": "2026-03-30T17:12:28.216143+00:00",
  "last_timestamp_sample": "2026-04-01T19:59:28.210761+00:00",
  "approx_per_day_if_uniform": 1906.3333
}
```

## Dataset map (blocked file lines)

- `blocked_trades_jsonl.lines` (from BLOCKED_WHY_DATASET_MAP.json): **8669**
