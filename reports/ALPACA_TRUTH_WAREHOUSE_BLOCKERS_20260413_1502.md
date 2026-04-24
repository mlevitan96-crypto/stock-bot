# ALPACA_TRUTH_WAREHOUSE_BLOCKERS_20260413_1502

## Fail-closed

- FAIL execution_join_coverage: 39.68% (need >= 98.0%) Counter({'no_join': 38, 'unified_trade_key': 22, 'unified_exit_time_proximity': 3})
- FAIL slippage_coverage: 0.00% (need >= 95.0%) 
- FAIL corporate_actions: 0.00% (need >= 100.0%) NO_API_KEYS
- FAIL signal_snapshot_exits: 0.00% (need >= 95.0%) 
- FAIL blocked_boundary_coverage: 37.50% (need >= 50.0%) 
- FAIL ci_reason_blocked: 34.78% (need >= 95.0%) 

## Gates

- execution_join_coverage: 39.68% pass=False
- fee_coverage: 100.00% pass=True
- slippage_coverage: 0.00% pass=False
- corporate_actions: 0.00% pass=False
- signal_snapshot_exits: 0.00% pass=False
- blocked_boundary_coverage: 37.50% pass=False
- ci_reason_blocked: 34.78% pass=False
- uw_snapshot_presence: 100.00% pass=True

