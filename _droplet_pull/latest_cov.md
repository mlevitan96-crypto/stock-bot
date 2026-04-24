# ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260421_1624

DATA_READY: YES

- execution join coverage: **100.00%**
- fee computable (fills basis): **100.00%**
- slippage computable (exits with context+exit px): **90.76%**
- signal snapshot near exit: **90.76%**
- decision events (snapshots+intents): **3266**
- blocked/near-miss bucket coverage (5m symbol buckets with block detail ∩ eval buckets): **2064** / **2064** → **100.00%**
- CI reason on blocked intents: **100.00%** (1130/1130)
- UW coverage on snapshots: **100.00%** (configured=True)

## Join reasons
Counter({'paper_exit_economic_closure': 1775, 'exit_has_order_id': 1558, 'unified_trade_key': 663, 'symbol_time_order_proximity': 95})

