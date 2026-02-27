# Baseline v2 verification (2026-02-18)

## Outputs after deploy + re-run

- **effectiveness_aggregates.json** present: No — droplet `git pull` was “Already up to date”; the script that writes `effectiveness_aggregates.json` and `unclassified_count`/`unclassified_pct` is in local commits not yet pushed to origin. After pushing and pulling on droplet, re-run effectiveness to get these outputs.
- **entry_vs_exit_blame.json** includes **unclassified_count** / **unclassified_pct**: No (same as above; deploy latest from main then re-run)

### effectiveness_aggregates.json (excerpt)
```json
{}
```

### entry_vs_exit_blame.json (excerpt)
```json
{
  "total_losing_trades": 1808,
  "weak_entry_pct": 0.0,
  "exit_timing_pct": 0.0
}
```
