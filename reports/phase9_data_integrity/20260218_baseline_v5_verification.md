# Baseline v5 verification (2026-02-18)

## Command
```
python3 scripts/analysis/run_effectiveness_reports.py --start 2026-02-01 --end 2026-02-18 --out-dir reports/effectiveness_baseline_blame_v5 2>&1
```

## Metrics
| Metric | Value |
|--------|--------|
| joined_count | 2000 |
| total_losing_trades | 1292 |
| weak_entry_pct | 0.0 |
| exit_timing_pct | 0.0 |
| unclassified_pct | 100.0 |
| unclassified_count | 1292 |
| avg_profit_giveback | None |

## entry_vs_exit_blame.json (excerpt)
```json
{
  "total_losing_trades": 1292,
  "weak_entry_pct": 0.0,
  "exit_timing_pct": 0.0,
  "unclassified_count": 1292,
  "unclassified_pct": 100.0
}
```

## effectiveness_aggregates.json (excerpt)
```json
{
  "joined_count": 2000,
  "total_losing_trades": 1292
}
```

## Join / giveback
- Join uses trade_id (primary) or symbol|entry_ts_bucket (fallback); see attribution_loader docstring.
- giveback populated: False
