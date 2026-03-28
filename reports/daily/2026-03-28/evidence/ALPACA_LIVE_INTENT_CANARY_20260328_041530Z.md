# Alpaca live intent — canary (post-floor)

**UTC:** 2026-03-28T04:15:30Z (approx)  
**Floor:** `1774670865`  
**Script:** `scripts/audit/alpaca_live_intent_canary_sample.py`

## Window

- **Configured:** `--min-rows 20` with `--max-wait-sec 300` (5 minutes; full 30-minute window not completed in this session — market/off-hours and no fills).
- **Poll interval:** 20s

## Results (JSON summary)

```json
{
  "floor_ts": 1774670865.0,
  "sample_total_post_floor": 0,
  "count_good_ok": 0,
  "count_missing_intent_blocker": 0,
  "count_synthetic_or_other": 0,
  "example_rows_redacted": [],
  "wait_used_sec": 300
}
```

## Interpretation

- No `entry_decision_made` rows with `ts` strictly after the deploy floor appeared within the wait window (likely no new filled entries after restart during the observation period).

## Outcome

**INCONCLUSIVE / PARTIAL** — operator should re-run canary with `--max-wait-sec 1800` during active trading if a full 30-minute window is required.
