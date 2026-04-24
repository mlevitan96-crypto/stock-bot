# BLOCKED_WHY_BARS_COVERAGE_PROOF
- Blocked rows: **8669**
- Rows with full horizon paths (Variant A, all five horizons): **8653**
- Coverage: **99.82%**

## Fail reasons (counts)

- `partial_horizon`: 16

## Hard gate
**PASS:** coverage >= 95%.

## API mapping proof (Phase 2.3)

| Item | Evidence |
|------|----------|
| Endpoint | `GET {ALPACA_DATA_URL or https://data.alpaca.markets}/v2/stocks/bars` |
| Implementation | `scripts/audit/fetch_alpaca_bars_for_counterfactuals.py` → `_fetch_bars_day()` builds query params `symbols`, `timeframe=1Min`, `start`, `end`, `limit=10000`, `sort=asc` |
| Auth headers | `APCA-API-KEY-ID`, `APCA-API-SECRET-KEY` from `_bars_headers()` (env `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` or aliases) |
| Merge blocked windows | Same script `--merge-blocked-state` unions `state/blocked_trades.jsonl` timestamps +61m per row with exit windows (`_load_blocked_windows`, `_merge_windows`) |
