# Alpaca join integrity blocker

- **What failed:** Join coverage below threshold (min 98.0%).
- **Counts:** total trades=3, entry_matched=0, exit_matched=0, join_coverage_entry_pct=0.0%, join_coverage_exit_pct=0.0%.

## Sample mismatch patterns (up to 20 each)

### trade_keys in TRADES_FROZEN.csv with no entry attribution

- `AAPL|LONG|2026-01-23T15:54:43+00:00`
- `AAPL|LONG|2026-01-01T00:00:00+00:00`

### trade_keys in TRADES_FROZEN.csv with no exit attribution

- `AAPL|LONG|2026-01-23T15:54:43+00:00`
- `AAPL|LONG|2026-01-01T00:00:00+00:00`
