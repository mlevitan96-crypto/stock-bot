# alpaca_truth_warehouse_manifest_20260324_2109

## Command
`python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --days 180 --max-compute`

## Git
- HEAD: `7bc6594b70a13551ad647684db2e904a7f5dfd83`

## Input surface hashes (partial file SHA256, capped)
- orders.jsonl: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- exit_attribution.jsonl: `4e8726d01e47ba23c8be31bb2cf27b31c258be276a26ccc264e04e9140e7153a`
- alpaca_unified_events.jsonl: `e40be91b7a039ee8d535becae9821e4b423ffa9c48972461f9b98aeed31dc8fc`

## Outputs
- `replay\alpaca_truth_warehouse_20260324_2109`
- `replay\alpaca_execution_truth_20260324_2109`

## Row counts
- orders_norm: 0
- fills: 0
- exits: 45
- ledger: 45

## Gates
- execution_join_coverage: pass=False value=0.00%
- fee_coverage: pass=False value=0.00%
- slippage_coverage: pass=False value=0.00%
- corporate_actions: pass=False value=0.00%
- signal_snapshot_exits: pass=False value=0.00%
- blocked_boundary_coverage: pass=False value=22.77%
- ci_reason_blocked: pass=False value=34.78%
- uw_snapshot_presence: pass=True value=100.00%

## DATA_READY: NO

