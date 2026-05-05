# alpaca_truth_warehouse_manifest_20260425_1914

## Command
`python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --days 30 `

## Git
- HEAD: `fc96678308eca5f81cfe422b7a210957fa33cf69`

## Input surface hashes (partial file SHA256, capped)
- orders.jsonl: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- exit_attribution.jsonl: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- alpaca_unified_events.jsonl: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

## Outputs
- `replay\alpaca_truth_warehouse_20260425_1914`
- `replay\alpaca_execution_truth_20260425_1914`

## Row counts
- orders_norm: 0
- fills: 0
- exits: 0
- ledger: 0

## Gates
- execution_join_coverage: pass=True value=100.00%
- fee_coverage: pass=True value=100.00%
- slippage_coverage: pass=True value=100.00%
- corporate_actions: pass=True value=100.00%
- signal_snapshot_exits: pass=True value=100.00%
- blocked_boundary_coverage: pass=False value=0.00%
- ci_reason_blocked: pass=True value=100.00%
- uw_snapshot_presence: pass=True value=100.00%

## DATA_READY: NO

