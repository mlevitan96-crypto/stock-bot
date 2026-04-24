# alpaca_truth_warehouse_manifest_20260413_1502

## Command
`python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --days 90 --max-compute`

## Git
- HEAD: `178606d9a6c34aaed4015160cd4e6d6be508e56c`

## Input surface hashes (partial file SHA256, capped)
- orders.jsonl: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- exit_attribution.jsonl: `4e8726d01e47ba23c8be31bb2cf27b31c258be276a26ccc264e04e9140e7153a`
- alpaca_unified_events.jsonl: `bf1ee7b2a89d4d288d4fa90d2c4503c66ba11abf558408eabb6f4045a354994b`

## Outputs
- `replay\alpaca_truth_warehouse_20260413_1502`
- `replay\alpaca_execution_truth_20260413_1502`

## Row counts
- orders_norm: 0
- fills: 0
- exits: 63
- ledger: 63

## Gates
- execution_join_coverage: pass=False value=39.68%
- fee_coverage: pass=True value=100.00%
- slippage_coverage: pass=False value=0.00%
- corporate_actions: pass=False value=0.00%
- signal_snapshot_exits: pass=False value=0.00%
- blocked_boundary_coverage: pass=False value=37.50%
- ci_reason_blocked: pass=False value=34.78%
- uw_snapshot_presence: pass=True value=100.00%

## DATA_READY: NO

