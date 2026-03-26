# Analysis F — GATE_VALUE (20260327_PNL_FINAL)

- **Cohort:** EXECUTED_QUALIFIED_LAST_WINDOW (intended); workspace blocked
- **Artifact:** `reports/ALPACA_PNL_GATE_VALUE_20260327_PNL_FINAL.json`
- **Rows:** n_trades=0

## So what

No numeric surface — ingest droplet truth bundle first.

## Blockers

```json
[
  {
    "id": "B1",
    "field": "complete_trade_ids",
    "detail": "artifact lacks full enumeration: have 0 ids, expected 44 (re-run forward truth runner with collect_complete_trade_ids; see telemetry gate + scripts/audit/alpaca_forward_truth_contract_runner.py)."
  },
  {
    "id": "B3",
    "field": "execution_joined.jsonl.gz",
    "detail": "replay_bundle_empty_or_tiny_bytes=48"
  },
  {
    "id": "B3",
    "field": "fills.jsonl.gz",
    "detail": "replay_bundle_empty_or_tiny_bytes=37"
  },
  {
    "id": "B4",
    "field": "workspace_exit_attribution_window",
    "detail": "local logs/exit_attribution.jsonl has 0 exits in [1774548000.0,1774555200.0] but certified JSON claims n=44 \u2014 droplet slice not in workspace."
  }
]
```
