# ALPACA forward parity counts (20260326_1707Z)

## Forward cohort only (exit_ts / unified ts ≥ DEPLOY_TS)

| Metric | Count |
|--------|------:|
| Economic closes (`exit_attribution.jsonl`) | 0 |
| Unified terminal closes (`alpaca_unified_events.jsonl`) | 0 |
| Parity (0 tolerance) | **PASS** |
| `alpaca_emit_failures.jsonl` new lines since deploy | 0 |

## Note

With **zero** forward closes, parity is **vacuously** equal; this does **not** satisfy the mission’s requirement to prove a **non-empty** forward cohort is perfect.

Machine JSON: `reports/ALPACA_FORWARD_PARITY_COUNTS_20260326_1707Z.json`
