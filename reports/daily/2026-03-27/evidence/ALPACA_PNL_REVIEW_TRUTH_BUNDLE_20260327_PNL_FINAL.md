# Truth bundle manifest (20260327_PNL_FINAL)

- **JSON:** `reports\ALPACA_PNL_REVIEW_TRUTH_BUNDLE_20260327_PNL_FINAL.json`
- **CSV:** `reports/ALPACA_PNL_REVIEW_TRUTH_BUNDLE_20260327_PNL_FINAL.csv`

## Row counts

Workspace snapshot: **0** economic rows ingested (missing `logs/exit_attribution.jsonl` and empty replay gzip payloads).

## Evidence

```json
{
  "ts": "20260327_PNL_FINAL",
  "root": "C:\\Dev\\stock-bot",
  "last_window_truth_sha256": "43569a9782f2f3a50c79d99e5a12f415b5dc132aba9288959cba6e5d7f564ca4",
  "strict_gate_source_sha256": "2ad5fa9bd6371b542a3c9b7ed5f422294cab29a47bfa5641d7a46c8187b0f9ca",
  "exit_attribution_row_counts": {
    "total_parsed_lines": 36,
    "lines_in_certified_exit_window": 0,
    "certified_open_ts_epoch": 1774548000.0,
    "certified_exit_ts_max_epoch": 1774555200.0
  },
  "log_file_stats": {
    "exit_attribution.jsonl": {
      "path": "C:\\Dev\\stock-bot\\logs\\exit_attribution.jsonl",
      "exists": true,
      "bytes": 38088
    },
    "run.jsonl": {
      "path": "C:\\Dev\\stock-bot\\logs\\run.jsonl",
      "exists": true,
      "bytes": 156876
    },
    "alpaca_unified_events.jsonl": {
      "path": "C:\\Dev\\stock-bot\\logs\\alpaca_unified_events.jsonl",
      "exists": true,
      "bytes": 98116
    },
    "orders.jsonl": {
      "path": "C:\\Dev\\stock-bot\\logs\\orders.jsonl",
      "exists": true,
      "bytes": 0
    }
  },
  "replay_execution_truth": {
    "replay_dir": "C:\\Dev\\stock-bot\\replay\\alpaca_execution_truth_20260324_2109",
    "execution_joined.jsonl.gz": {
      "bytes": 48,
      "path": "C:\\Dev\\stock-bot\\replay\\alpaca_execution_truth_20260324_2109\\execution_joined.jsonl.gz"
    },
    "fills.jsonl.gz": {
      "bytes": 37,
      "path": "C:\\Dev\\stock-bot\\replay\\alpaca_execution_truth_20260324_2109\\fills.jsonl.gz"
    },
    "orders.jsonl.gz": {
      "bytes": 38,
      "path": "C:\\Dev\\stock-bot\\replay\\alpaca_execution_truth_20260324_2109\\orders.jsonl.gz"
    },
    "fees.jsonl.gz": {
      "bytes": 36,
      "path": "C:\\Dev\\stock-bot\\replay\\alpaca_execution_truth_20260324_2109\\fees.jsonl.gz"
    }
  },
  "dashboard_aggregate_ref": "C:\\Dev\\stock-bot\\reports\\ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z.json",
  "row_counts": {
    "exit_attribution": 0,
    "fills": 0,
    "orders": 0,
    "fees": 0
  },
  "extraction_commands": [
    "python -c \"from pathlib import Path; print(sum(1 for _ in open(Path('logs/exit_attribution.jsonl'))))\"  # droplet",
    "wc -l logs/run.jsonl logs/orders.jsonl logs/alpaca_unified_events.jsonl  # droplet",
    "python scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --help  # optional full bundle"
  ],
  "blockers": [
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
}
```
