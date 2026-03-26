# Alpaca Telemetry Inventory (Droplet)

**UTC:** 2026-03-18T20:04:38.586258+00:00

| Stream | Path | Status | Bytes | Lines | mtime_utc |
|--------|------|--------|-------|-------|-----------|
| unified | `logs/alpaca_unified_events.jsonl` | **MISSING** | 0 | 0 |  |
| entry_attr | `logs/alpaca_entry_attribution.jsonl` | **MISSING** | 0 | 0 |  |
| exit_attr_emit | `logs/alpaca_exit_attribution.jsonl` | **MISSING** | 0 | 0 |  |
| exit_attribution | `logs/exit_attribution.jsonl` | **OK** | 18159702 | 2006 | 2026-03-18T19:59:51.763027+00:00 |
| master_trade | `logs/master_trade_log.jsonl` | **OK** | 5218558 | 2601 | 2026-03-18T19:29:02.249209+00:00 |
| attribution | `logs/attribution.jsonl` | **OK** | 6006326 | 2006 | 2026-03-18T19:59:51.605024+00:00 |
| blocked | `state/blocked_trades.jsonl` | **OK** | 15618338 | 2307 | 2026-03-18T19:59:34.753689+00:00 |

## Schema version (sample)

- Last line schema hint (exit_attribution): `1.0.0`
- Emitter schema: `src/telemetry/alpaca_attribution_schema.py` SCHEMA_VERSION **1.2.0**

## Rotated / archived (sample ls)
```
/root/stock-bot/logs/alpaca_api.jsonl

```

## Append-only policy
Per MEMORY_BANK: `exit_attribution.jsonl`, `attribution.jsonl`, `master_trade_log.jsonl` must not be truncated by rotation.