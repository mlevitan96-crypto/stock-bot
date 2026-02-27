# Baseline v3 verification post-deploy (2026-02-18)

## Command
```
python3 scripts/analysis/run_effectiveness_reports.py --start 2026-02-01 --end 2026-02-18 --out-dir reports/effectiveness_baseline_blame_v3 2>&1
```

## Verification (after adding scripts/analysis and re-pull + re-run)

| Check | Result |
|-------|--------|
| joined_count | 2000 |
| total_losing_trades | 1292 |
| avg_profit_giveback | null (no exit_quality_metrics in logs yet; fix deployed for new exits) |
| weak_entry_pct | 0.0 |
| exit_timing_pct | 0.0 |
| unclassified_pct | 100.0 |
| unclassified_count | 1292 |

## effectiveness_aggregates.json
```json
{"joined_count": 2000, "total_losing_trades": 1292, "win_rate": 0.354, "avg_profit_giveback": null}
```

## entry_vs_exit_blame.json (excerpt)
```json
{"total_losing_trades": 1292, "weak_entry_pct": 0.0, "exit_timing_pct": 0.0, "unclassified_count": 1292, "unclassified_pct": 100.0}
```

## Top 3 exit reasons (by loss contribution proxy: freq * |avg_pnl|)
```
[]
```

## Note

After adding `scripts/analysis` (attribution_loader, run_effectiveness_reports) to the repo and pushing (commit 515bcf1), droplet pulled and re-ran effectiveness successfully. Outputs are authoritative. Giveback remains null until new exits (after deploy) produce exit_quality_metrics in logs.
