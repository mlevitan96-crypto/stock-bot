# EXEC_MODE_PAPER_PROMO_EVALUATION

**Status:** `FAIL` (automated gates on available data)

**Reasons:** `['B_tail_p05_worse_than_A_by_threshold_0_5']`

## paper_exec_mode_decisions.jsonl

- Total rows: 0; A rows: 0; B rows: 0
- B filled (has fill_price): 0; B errors: 0; cross events: 0
- B fill rate proxy: None

## Exit attribution proxy (ET hour parity)

```json
{
  "A_even_hour": {
    "label": "A_proxy_even_ET_hour",
    "trade_count": 170,
    "mean_pnl_per_trade": 0.312921,
    "total_pnl": 53.196521,
    "p05_pnl_per_trade": -3.41,
    "max_drawdown_proxy": -32.83
  },
  "B_odd_hour": {
    "label": "B_proxy_odd_ET_hour",
    "trade_count": 108,
    "mean_pnl_per_trade": -0.307657,
    "total_pnl": -33.226963,
    "p05_pnl_per_trade": -4.9,
    "max_drawdown_proxy": -56.107209
  }
}
```
