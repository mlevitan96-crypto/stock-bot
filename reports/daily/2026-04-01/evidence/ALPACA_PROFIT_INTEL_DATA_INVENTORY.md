# ALPACA_PROFIT_INTEL_DATA_INVENTORY

- **Generated (UTC):** 2026-04-01T20:14:58.092904+00:00
- **Session anchor (ET):** 2026-04-01

## Row counts (full file scan)

| File | Rows | Present |
|------|------|--------|
| `exit_attribution.jsonl` | 432 | True |
| `orders.jsonl` | 10364 | True |
| `signal_context.jsonl` | 0 | True (file empty — no per-row UW subfield replay for Phase 2 beyond `score_snapshot`) |
| `run.jsonl` | 6321 | True |
| `score_snapshot.jsonl` | 2000 | True |
| `blocked_trades.jsonl` | 8669 | True |
| `alpaca_unified_events.jsonl` | 862 | True |

## Tail sample used for deep phases

- `exit_attribution` tail rows loaded: **432**
- `score_snapshot` tail rows loaded: **2000**
- `blocked_trades` tail rows loaded: **6052**
- `signal_context` tail rows loaded: **0**

## Join coverage (tail)

```json
{
  "exit_rows_in_tail_with_trade_id": 432,
  "exit_tail_with_canonical_trade_id": 432,
  "orders_tail_with_canonical_trade_id": 447
}
```

## SPI artifacts (newest)


