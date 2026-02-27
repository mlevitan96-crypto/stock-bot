# Baseline effectiveness v2 (post-fix run) — 2026-02-18

## Run

- **Command (on droplet):**  
  `python3 scripts/analysis/run_effectiveness_reports.py --start 2026-02-01 --end $(date +%F) --out-dir reports/effectiveness_baseline_blame_v2`
- **Output dir:** `reports/effectiveness_baseline_blame_v2` (on droplet).

## Confirmation

| Check | Result |
|-------|--------|
| joined_count ≥ 20 | Yes (2846) |
| losers ≥ 5 | Yes (1783) |
| giveback populated | No — still N/A (exit reasons show avg_giveback None; upstream logs lack exit_quality_metrics) |
| blame non-degenerate or unclassified explicit | weak_entry_pct=0, exit_timing_pct=0 → effectively **100% unclassified** (neither weak entry nor exit timing classified). Code fix adds unclassified_pct; after deploy + re-run, entry_vs_exit_blame.json will show unclassified_pct explicitly. |

## Blame split (from run 2026-02-18)

- **weak_entry_pct:** 0  
- **exit_timing_pct:** 0  
- **unclassified_pct:** 100 (implicit: all 1783 losers unclassified until entry_score / giveback present in joined data)

## Top harmful signals / giveback exits

- **Signal effectiveness:** Table in EFFECTIVENESS_SUMMARY.md on droplet (signal_id, trade_count, win_rate, avg_pnl, avg_MFE, avg_MAE, avg_giveback). Many rows may have null giveback/MFE.
- **Exit effectiveness:** Top exit_reason_code by frequency: signal_decay(0.96), signal_decay(0.90), signal_decay(0.88), …; avg_giveback = None for reported reasons (no giveback in logs).
- **Top giveback exits:** N/A until giveback is populated from upstream.

## Next steps

1. Deploy effectiveness script changes (unclassified_pct, effectiveness_aggregates.json) to droplet and re-run baseline v2 to get explicit unclassified_pct in entry_vs_exit_blame.json.
2. Improve upstream: ensure exit_attribution logs include exit_quality_metrics (and MFE/high_water where needed) so giveback can be computed and aggregated.
3. After giveback and blame are trustworthy, use baseline_v2 (or a later re-run) for next-lever selection (entry vs exit).
