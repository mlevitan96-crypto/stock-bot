# ALPACA_TRUTH_WAREHOUSE_COVERAGE_20260413_1502

DATA_READY: NO

- execution join coverage: **39.68%**
- fee computable (fills basis): **100.00%**
- slippage computable (exits with context+exit px): **0.00%**
- signal snapshot near exit: **0.00%**
- decision events (snapshots+intents): **101**
- blocked/near-miss bucket coverage (5m symbol buckets with block detail ∩ eval buckets): **21** / **56** → **37.50%**
- CI reason on blocked intents: **34.78%** (8/23)
- UW coverage on snapshots: **100.00%** (configured=False)

## Join reasons
Counter({'no_join': 38, 'unified_trade_key': 22, 'unified_exit_time_proximity': 3})

