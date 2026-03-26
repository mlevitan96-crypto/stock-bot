# PnL reconciliation (20260327_PNL_FINAL)

## Status

**STOP-GATE:** Reconciliation not executed — missing per-trade fills/fees/pnl joins in workspace.

### Blocker table

| id | field | detail |
|----|-------|--------|
| B1 | `complete_trade_ids` | artifact lacks full enumeration: have 0 ids, expected 44 (re-run forward truth runner with collect_complete_trade_ids; see telemetry gate + scripts/audit/alpaca_forward_truth_contract_runner.py). |
| B3 | `execution_joined.jsonl.gz` | replay_bundle_empty_or_tiny_bytes=48 |
| B3 | `fills.jsonl.gz` | replay_bundle_empty_or_tiny_bytes=37 |
| B4 | `workspace_exit_attribution_window` | local logs/exit_attribution.jsonl has 0 exits in [1774548000.0,1774555200.0] but certified JSON claims n=44 — droplet slice not in workspace. |

## Required join (droplet)

1. Load `exit_attribution.jsonl` exit rows → `pnl`, `entry_price`, `exit_price`, `qty`, `timestamp`, `entry_timestamp`.
2. Join `orders.jsonl` / fill events by `canonical_trade_id` alias closure (`run.jsonl` `canonical_trade_id_resolved`).
3. Sum fee rows per trade (if `fees.jsonl` or broker export).
4. `reconciliation_delta = net_pnl_computed - pnl_exit_attribution` (must be 0 or explained).
