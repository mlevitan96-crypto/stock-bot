# ALPACA_250_THRESHOLD_GROUND_TRUTH

## Definition sources (loaded)
- `docs/pnl_audit/REQUIRED_FIELDS.md` exists: **True**
- `ALPACA_CANONICAL_TRADE_DEFINITION.md` (evidence): **True** — path used: `/root/stock-bot/reports/daily/2026-03-31/evidence/ALPACA_CANONICAL_TRADE_DEFINITION.md`

## Method (matches `compute_canonical_trade_count`, no floor)
- Ledger: `logs/exit_attribution.jsonl`
- Unit: unique `trade_key` = `build_trade_key(symbol, side, entry_ts)`
- Exclude: `learning_excluded_for_exit_record` (era cut)
- Require: parsable exit timestamp
- Order: ascending by **first** qualifying exit epoch per key (chronological closes)
- Identity for audit: `trade_id` from the row that supplied that first close (fallback `canonical_trade_id`)

## Results
- **total_post_era_trades:** 280
- **count >= 250:** YES
- **Trade #250 (chronological first close per trade_key):**
  - `trade_id`: `open_NFLX_2026-04-01T13:37:25.983043+00:00`
  - `trade_key`: `NFLX|LONG|1775050645`
  - `exit_ts`: `2026-04-01T15:58:06.836045+00:00`

- **Full id list:** `reports/daily/2026-04-01/evidence/ALPACA_250_THRESHOLD_GROUND_TRUTH_TRADE_IDS.json`
