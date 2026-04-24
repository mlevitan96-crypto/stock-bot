# BLOCKED_WHY_INFERENCE_RULES

1. **Decision time:** use `timestamp` from blocked row; if missing, row excluded from horizon replay (`skip=missing_symbol_or_timestamp`).
2. **Direction:** `_norm_side(row)` uses `side` then `direction`; values `long/buy/bull` → long; `short/sell/bear` → short; else `unknown` (excluded from directional PnL — returns `side_unknown`).
3. **No snapshot join in pipeline:** optional extension would match `score_snapshot` by symbol + nearest `ts_iso` ≤ block `timestamp` (not required for bar counterfactuals).
4. **Qty:** `notional_usd / decision_price` with floor 0.0001 (see `BLOCKED_WHY_BARS_COVERAGE.json` `notional_usd_for_qty`).
