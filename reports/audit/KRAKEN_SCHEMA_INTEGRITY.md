# Kraken schema integrity (Phase 2)

## Planned checks

- Field presence stability over time  
- `trade_id` type consistency (string)  
- Timestamp ISO8601 UTC  
- No duplicate primary keys per stream  

## Result: **NOT EXECUTABLE**

No Kraken telemetry file set exists on the droplet for live Kraken trades. Schema stability **cannot** be measured.

**Status:** **BLOCKED** — same root cause as `KRAKEN_JOIN_COVERAGE.md`.

## Reference only (Alpaca, same repo)

Last line sampled from droplet `exit_attribution.jsonl` (2026-03-18): JSON with `symbol`, `timestamp`, `entry_timestamp`, `exit_reason`, `pnl`, … — **equities schema**, **not** Kraken pair schema. **Do not use** as Kraken schema proof.
