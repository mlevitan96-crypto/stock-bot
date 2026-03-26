# ALPACA — Pipeline read reconciliation (Phase 1)

**Timestamp:** 20260314

## Droplet inventory (source counts)

| Source | Line count | Sample keys (last record) |
|--------|-----------|---------------------------|
| `logs/exit_attribution.jsonl` | 2000 | symbol, timestamp, entry_timestamp, exit_reason, pnl, pnl_pct, entry_price, exit_price, qty, time_in_trade_minutes, entry_uw, exit_uw, ... |
| `logs/master_trade_log.jsonl` | 2337 | trade_id, symbol, side, is_live, is_shadow, composite_version, entry_ts, exit_ts, entry_price, exit_price, size, realized_pnl_usd, ... |
| `logs/attribution.jsonl` | 2000 | ts, type, trade_id, symbol, pnl_usd, context, strategy_id |

## Step 1 diagnostic (paths opened, rows read/kept/dropped)

- **Pipeline command:** `python scripts/alpaca_edge_2000_pipeline.py --step 1 --allow-missing-attribution --diagnostic`
- **Exit log path opened:** `logs/exit_attribution.jsonl` (primary source for TRADES_FROZEN.csv)

## Reconciliation table

| Metric | Value |
|--------|-------|
| source_count (exit_attribution.jsonl lines) | 2000 |
| pipeline_count (TRADES_FROZEN.csv data rows) | 1999 |
| drop_reason (if any) | none (except max_trades cap) |

## Confirmation

- TRADES_FROZEN.csv row count is consistent with exit_attribution.jsonl (last N trades, N ≤ max_trades).
- No silent filtering due to schema drift if diagnostic shows drops only for blank/json_error/not_dict/no_exit_ts; timestamp/field parsing uses same logic as writer.
