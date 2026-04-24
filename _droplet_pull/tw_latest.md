# ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260421_1726

DATA_READY: YES

- execution join coverage: **100.00%**
- fee computable (fills basis): **100.00%**
- slippage computable (exits with context+exit px): **90.88%**
- signal snapshot near exit: **90.88%**
- decision events (snapshots+intents): **3095**
- blocked/near-miss bucket coverage (5m symbol buckets with block detail ∩ eval buckets): **2044** / **2044** → **100.00%**
- CI reason on blocked intents: **100.00%** (904/904)
- UW coverage on snapshots: **100.00%** (configured=True)

## Join reasons
Counter({'paper_exit_economic_closure': 1782, 'exit_has_order_id': 1611, 'unified_trade_key': 656, 'symbol_time_order_proximity': 95})

