# Baseline v3 verification (2026-02-18)

## Commands run on droplet

```
git pull origin main
python3 scripts/analysis/run_effectiveness_reports.py --start 2026-02-01 --end 2026-02-18 --out-dir reports/effectiveness_baseline_blame_v3 2>&1
```

## Verification

| Check | Result |
|-------|--------|
| joined_count ≥ 20 | Yes (2000 from SUMMARY) |
| losers ≥ 5 | Yes (1292) |
| avg_profit_giveback populated | No (N/A; exit reasons show None) |
| blame: weak_entry_pct / exit_timing_pct / unclassified_pct | 0.0 / 0.0 / N/A (unclassified not in droplet report yet) |

## effectiveness_aggregates.json
```json
{}
```

## entry_vs_exit_blame.json (excerpt)
```json
{
  "total_losing_trades": 1292,
  "weak_entry_pct": 0.0,
  "exit_timing_pct": 0.0,
  "unclassified_count": null,
  "unclassified_pct": null
}
```

## EFFECTIVENESS_SUMMARY.md (head)
```
# Signal & Exit Effectiveness Summary

Generated: 2026-02-18T17:36:47.154199+00:00
Closed trades (joined): 2000

## 1. Signal effectiveness (top 15 by trade count)

| signal_id | trade_count | win_rate | avg_pnl | avg_MFE | avg_MAE | avg_giveback |
|-----------|-------------|----------|---------|---------|---------|--------------|

## 2. Exit effectiveness by exit_reason_code

| exit_reason_code | frequency | avg_realized_pnl | avg_giveback | % saved_loss | % left_money |
|------------------|-----------|------------------|--------------|--------------|---------------|
| signal_decay(0.96) | 245 | -0.1505 | None | 0.0 | 0.0 |
| signal_decay(0.90) | 107 | -0.175 | None | 0.0 | 0.0 |
| signal_decay(0.88) | 105 | -0.1531 | None | 0.0 | 0.0 |
| signal_decay(0.89) | 92 | -0.0718 | None | 0.0 | 0.0 |
| signal_decay(0.93) | 92 | -0.2158 | None | 0.0 | 0.0 |
| signal_decay(0.91) | 92 | -0.1534 | None | 0.0 | 0.0 |
| signal_decay(0.92) | 82 | -0.1437 | None | 0.0 | 0.0 |
| signal_decay(0.87) | 81 | -0.0724 | None | 0.0 | 0.0 |
| signal_decay(0.86) | 76 | -0.1036 | None | 0.0 | 0.0 |
| signal_decay(0.85) | 60 | -0.0877 | None | 0.0 | 0.0 |
| signal_decay(0.83) | 53 | -0.1509 | None | 0.0 | 0.0 |
| signal_decay(0.79) | 49 | -0.1813 | None | 0.0 | 0.0 |
| signal_decay(0.78) | 44 | -0.2894 | None | 0.0 | 0.0 |
| signal_decay(0.81) | 43 | -0.0708 | None | 0.0 | 0.0 |
| signal_decay(0.84) | 41 | -0.1421 | None | 0.0 | 0.0 |
| signal_decay(0.82) | 40 | -0.1347 | None | 0.0 | 0.0 |
| signal_decay(0.80) | 33 | -0.1491 | None | 0.0 | 0.0 |
| signal_decay(0.77) | 31 | -0.1348 | None | 0.0 | 0.0 |
| signal_decay(0.92)+flow_reversal | 26 | -0.115 | None | 0.0 | 0.0 |
| signal_decay(0.76) | 26 | -0.0942 | None | 0.0 | 0.0 |
| signal_decay(0.75) | 25 | -0.0169 | None | 0.0 | 0.0 |
| signal_decay(0.73) | 22 | 0.0018 | None | 0.0 | 0.0 |
| signal_decay(0.74) | 20 | 0.1 | None | 0.0 | 0.0 |
| signal_decay(0.91)+flow_reversal | 17 | 0.0059 | None | 0.0 | 0.0 |
| signal_decay(0.90)+flow_reversal
```
