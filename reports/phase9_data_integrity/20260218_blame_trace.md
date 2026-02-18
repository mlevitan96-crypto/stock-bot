# Blame classification trace (2026-02-18)

## 1) entry_vs_exit_blame.json (effectiveness_baseline_blame_v2)

```json
{
  "total_losing_trades": 1808,
  "weak_entry_count": 0,
  "weak_entry_pct": 0.0,
  "exit_timing_count": 0,
  "exit_timing_pct": 0.0,
  "examples_good_entry_bad_exit": [],
  "examples_bad_entry": []
}
```

## 2) Why everything is unclassified

- **Weak entry** requires `entry_score` present and **< 3.0**. Joined rows get `entry_score` from attribution (context.entry_score). If attribution does not write context.entry_score, joined rows lack it → score treated as 0 → condition `score > 0 and score < 3` is false.
- **Exit timing** requires `exit_quality_metrics.profit_giveback >= 0.3` or (MFE > 0 and PnL < 0). If exit_attribution rarely has profit_giveback/MFE (because high_water was missing), no loser is classified as exit_timing.
- **Result:** 100% unclassified until (1) attribution writes entry_score into context, (2) exit_attribution has giveback/MFE from high_water fix.

## 3) Modifications to blame logic

- **Do NOT loosen classification rules.** Only ensure **unclassified_count** and **unclassified_pct** are always present in the report so we never show silent 0/0.
- Script `scripts/analysis/run_effectiveness_reports.py` already includes unclassified_count and unclassified_pct in `build_entry_vs_exit_blame`; after deploy and re-run, baseline v3 will show them explicitly.
