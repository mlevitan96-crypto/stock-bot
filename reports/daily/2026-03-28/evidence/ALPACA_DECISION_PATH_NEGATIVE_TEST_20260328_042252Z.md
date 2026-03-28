# Alpaca decision-path negative test

Injected replay with `score=None`, empty comps, no intelligence_trace → `MISSING_INTENT_BLOCKER`.

```json
{
  "event_type": "entry_decision_made",
  "entry_intent_synthetic": false,
  "entry_intent_source": "live_runtime",
  "entry_intent_status": "MISSING_INTENT_BLOCKER",
  "entry_intent_error": "entry_score_total_non_numeric",
  "symbol": "TESTPATH",
  "side": "buy",
  "canonical_trade_id": "NEG|LONG|1",
  "trade_id": "open_TESTPATH_2026-03-28T12:01:00+00:00",
  "trade_key": "NEG|LONG|1",
  "decision_event_id": "dry-de-neg",
  "time_bucket_id": "dry-tb-neg",
  "symbol_normalized": "TESTPATH",
  "signal_trace": {
    "policy_anchor": "alpaca_equity_default",
    "_blocker": true,
    "reason": "entry_score_total_non_numeric"
  },
  "entry_score_total": null,
  "entry_score_components": {
    "_blocked": true,
    "reason": "entry_score_total_non_numeric"
  },
  "ts": "2026-03-28T04:22:52.155367+00:00"
}
```

- **audit_entry_decision_made_row_ok:** False (expected)
