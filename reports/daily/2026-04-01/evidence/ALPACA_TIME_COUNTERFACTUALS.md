# ALPACA_TIME_COUNTERFACTUALS

## Status: +1m/+5m/+15m simulated exits

- **Bars file missing** under `artifacts/market_data/alpaca_bars.jsonl` — **no** per-trade minute-step simulation in this campaign.

## MFE vs realized pnl% proxy (rows with both)

- Pairs: **0**
- Distribution of `(mfe_pct - pnl_pct)` — positive ⇒ left favorable excursion on table (sign depends on convention):

```json
{
  "giveback_or_left_on_table_delta_stats": {
    "n": 0
  }
}
```

## Limitation

- MFE is path-dependent; without bar replay, minute buckets are **not** computed here.

