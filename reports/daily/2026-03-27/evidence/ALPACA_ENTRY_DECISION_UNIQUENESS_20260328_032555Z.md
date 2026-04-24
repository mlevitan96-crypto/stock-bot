# Alpaca entry decision uniqueness (Invariant A)

**Evidence host:** local_workspace  
**ET report date:** 2026-03-27  
**Generated (UTC):** 20260328_032555Z

## Procedure

Full scan of unified log stream for `event_type=alpaca_entry_attribution`, grouped by `trade_id` (includes `strict_backfill_alpaca_unified_events.jsonl` when present).

## Results

| Metric | Value |
|--------|-------|
| Distinct trade_ids with ≥1 entry row | 5 |
| trade_ids with row count > 1 (must be 0) | 5 |
| PASS | **NO** |

## Proxy note

entry_decision_made is proxied by alpaca_entry_attribution (unified) and trade_intent entered; uniqueness keyed on trade_id applies to unified entry rows.

## Violation examples

```json
[
  {
    "trade_id": "open_TSLA_2026-03-14T12-00-00Z",
    "row_count": 10,
    "timestamps": [
      "2026-03-14T12:00:00+00:00",
      "2026-03-14T12:00:00+00:00",
      "2026-03-14T12:00:00+00:00",
      "2026-03-14T12:00:00+00:00",
      "2026-03-14T12:00:00+00:00"
    ]
  },
  {
    "trade_id": "parity_1",
    "row_count": 11,
    "timestamps": [
      "2026-03-17T16:10:55.021191+00:00",
      "2026-03-17T16:14:50.792393+00:00",
      "2026-03-17T16:23:26.821178+00:00",
      "2026-03-18T20:06:25.725500+00:00",
      "2026-03-25T16:27:44.615131+00:00"
    ]
  },
  {
    "trade_id": "parity_2",
    "row_count": 11,
    "timestamps": [
      "2026-03-17T16:10:55.025145+00:00",
      "2026-03-17T16:14:50.799369+00:00",
      "2026-03-17T16:23:26.824384+00:00",
      "2026-03-18T20:06:25.728834+00:00",
      "2026-03-25T16:27:44.618267+00:00"
    ]
  },
  {
    "trade_id": "inv",
    "row_count": 11,
    "timestamps": [
      "2026-03-17T16:10:55.031788+00:00",
      "2026-03-17T16:14:50.814003+00:00",
      "2026-03-17T16:23:26.829508+00:00",
      "2026-03-18T20:06:25.733972+00:00",
      "2026-03-25T16:27:44.766236+00:00"
    ]
  },
  {
    "trade_id": "open_AAPL_1",
    "row_count": 7,
    "timestamps": [
      "2026-03-17T16:00:00+00:00",
      "2026-03-17T16:00:00+00:00",
      "2026-03-17T16:00:00+00:00",
      "2026-03-17T16:00:00+00:00",
      "2026-03-17T16:00:00+00:00"
    ]
  }
]
```
