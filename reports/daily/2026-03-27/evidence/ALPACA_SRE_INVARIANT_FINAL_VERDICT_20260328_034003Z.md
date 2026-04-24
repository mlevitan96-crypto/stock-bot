# SRE final verdict — Alpaca pipeline health (invariant pass)

**ET report date:** 2026-03-27  
**Generated (UTC):** 20260328_034003Z

## Reviewed

- JSONL log structure (decode integrity on core streams)
- Append-only shapes present on disk
- Audit vs live path parity (same files as strict gate)

## Verdict

**SRE_ALPACA_PIPELINE_HEALTHY**

Reason: Core JSONL streams present with zero decode errors in full-file scan.

## Log health detail

```json
{
  "log_paths": [
    {
      "path": "/root/stock-bot/logs/alpaca_unified_events.jsonl",
      "exists": true,
      "non_empty_lines": 1939,
      "json_decode_errors": 0
    },
    {
      "path": "/root/stock-bot/logs/alpaca_entry_attribution.jsonl",
      "exists": true,
      "non_empty_lines": 1299,
      "json_decode_errors": 0
    },
    {
      "path": "/root/stock-bot/logs/run.jsonl",
      "exists": true,
      "non_empty_lines": 2208,
      "json_decode_errors": 0
    },
    {
      "path": "/root/stock-bot/logs/exit_attribution.jsonl",
      "exists": true,
      "non_empty_lines": 3611,
      "json_decode_errors": 0
    },
    {
      "path": "/root/stock-bot/logs/orders.jsonl",
      "exists": true,
      "non_empty_lines": 2709,
      "json_decode_errors": 0
    }
  ],
  "aggregate_non_empty_lines": 11766,
  "aggregate_json_decode_errors": 0,
  "rotation_session_note": "Session boundaries are implicit in timestamps inside JSONL rows; log rotation policy is operator-managed (see docs/DATA_RETENTION_POLICY.md if present). This check does not rewrite telemetry.",
  "audit_live_parity": "Audit vs live: strict gate reads the same JSONL paths as runtime appenders (plus strict_backfill_* mirrors). No separate 'audit-only' truth store is required for these invariants.",
  "passes": true,
  "stub_shadow_normalized_keys_observed": 209,
  "raw_line_duplicate_groups_normalized": 209
}
```
