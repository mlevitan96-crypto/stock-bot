# CSA — PnL review closeout (20260327_PNL_FINAL)

## Checklist

| Criterion | Met |
|-----------|-----|
| A) Trade ID list reproducible | No |
| B) PnL reconciled fills/fees/ledger | No — no rows |
| C) Blocked/shadow opportunity | No — missing ledgers |
| D) 10+ analyses with artifacts | Yes — stub JSON+MD (n=0) |
| E) Profit levers ranked | Yes — CSA packet |
| F) Adversarial | Yes |
| Quant 5 angles implemented | No — blocked (artifacts document intent) |

## Blocker table

| id | field | detail |
|----|-------|--------|
| B1 | `complete_trade_ids` | artifact lacks full enumeration: have 0 ids, expected 44 (re-run forward truth runner with collect_complete_trade_ids; see telemetry gate + scripts/audit/alpaca_forward_truth_contr |
| B3 | `execution_joined.jsonl.gz` | replay_bundle_empty_or_tiny_bytes=48 |
| B3 | `fills.jsonl.gz` | replay_bundle_empty_or_tiny_bytes=37 |
| B4 | `workspace_exit_attribution_window` | local logs/exit_attribution.jsonl has 0 exits in [1774548000.0,1774555200.0] but certified JSON claims n=44 — droplet slice not in workspace. |
| B5 | reconciliation_rows | CSV has zero data rows until per-trade joins run on droplet export |

CSA_VERDICT: STILL_BLOCKED
