# Alpaca decision-path audit (test sink)

**Sink:** `C:\Dev\stock-bot\logs\test_run.jsonl`

## Per-row production audits

```json
{
  "per_row": [
    {
      "trade_id": "open_TESTPATH_2026-03-28T12:00:00+00:00",
      "status": "OK",
      "audit_ok": true,
      "live_truth": true,
      "score_tuple": [
        true,
        2,
        5
      ]
    },
    {
      "trade_id": "open_TESTPATH_2026-03-28T12:01:00+00:00",
      "status": "MISSING_INTENT_BLOCKER",
      "audit_ok": false,
      "live_truth": true,
      "score_tuple": [
        true,
        1,
        0
      ]
    }
  ],
  "synthetic_injection_fails": true,
  "best_row_prefers_richer": true,
  "blocker_fails_strict_ok": true
}
```

## Production run.jsonl integrity

- `run.jsonl` sha256 before: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `run.jsonl` sha256 after: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- **Unchanged:** True
