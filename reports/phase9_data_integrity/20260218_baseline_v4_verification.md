# Baseline v4 verification (2026-02-18)

## Commands (droplet)

```bash
git pull origin main
python3 scripts/analysis/run_effectiveness_reports.py --start 2026-02-01 --end 2026-02-18 --out-dir reports/effectiveness_baseline_blame_v4
```

## Verification

| Check | Result |
|-------|--------|
| joined_count | 2000 |
| total_losing_trades | 1292 |
| avg_profit_giveback | null |
| weak_entry_pct | 0.0 |
| exit_timing_pct | 0.0 |
| unclassified_pct | 100.0 |
| unclassified_count | 1292 |

## Exit quality coverage

- **Proof reference:** `reports/phase9_data_integrity/20260218_exit_quality_emission_proof.md`
- **Result:** with_exit_quality_metrics = 0 in newest 500 exit_attribution lines (no new exits observed since deploy; see diagnosis in proof).
- **Attribution:** Last 200 attribution lines have entry_score in context (200/200). Blame remains 100% unclassified likely because joined rows do not receive entry_score—join key (symbol + entry_timestamp bucket) may not match between exit and entry records, or exit records lack entry_timestamp.

## Conclusion

- Baseline v4 ran successfully; outputs present.
- unclassified_pct still 100%; weak_entry_pct and exit_timing_pct 0. Next: fix join (ensure exit records have entry_timestamp matching entry’s entry_ts) and/or wait for new exits with exit_quality_metrics, then re-run.
