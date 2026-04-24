# Alpaca entry decision uniqueness (Invariant A)

**Evidence host:** alpaca_droplet  
**ET report date:** 2026-03-27  
**Generated (UTC):** 20260328_034003Z

## Procedure

Full scan of unified log stream for `event_type=alpaca_entry_attribution`, grouped by `trade_id` (includes `strict_backfill_alpaca_unified_events.jsonl` when present).

**Invariant A (authoritative for structural “one decision per open”):** group by **normalized** `open_<SYM>_<UTC-second>` so microsecond vs `Z` string variants collapse (duplicate **lines** with divergent string forms are logged separately below).

## Results

| Metric | Value |
|--------|-------|
| Distinct raw `trade_id` strings with ≥1 entry row | 1669 |
| Raw strings with row count > 1 (log-line hygiene) | 209 |
| Distinct normalized open-trade keys (UTC second) | 1669 |
| Normalized keys with row count > 1 (includes stub shadows) | 209 |
| Normalized keys with **≥2 economic** entry payloads (blocking) | 0 |
| Normalized keys with stub + economic shadow lines (SRE hygiene) | 209 |
| PASS (Kraken-style double **decision** — economic dupes) | **YES** |
| PASS (raw string line count — informational) | **NO** |

## Proxy note

entry_decision_made is proxied by alpaca_entry_attribution (unified) and trade_intent entered; uniqueness keyed on trade_id applies to unified entry rows.

## Violation examples — raw string duplicates

```json
[
  {
    "trade_id": "open_GM_2026-03-25T17:35:44.149365+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:35:44.149365+00:00",
      "2026-03-25T17:35:44Z"
    ]
  },
  {
    "trade_id": "open_SLB_2026-03-25T17:35:58.181511+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:35:58.181511+00:00",
      "2026-03-25T17:35:58Z"
    ]
  },
  {
    "trade_id": "open_TSLA_2026-03-25T17:36:00.702283+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:00.702283+00:00",
      "2026-03-25T17:36:00Z"
    ]
  },
  {
    "trade_id": "open_MRNA_2026-03-25T17:36:19.569583+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:19.569583+00:00",
      "2026-03-25T17:36:19Z"
    ]
  },
  {
    "trade_id": "open_COIN_2026-03-25T17:36:36.155798+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:36.155798+00:00",
      "2026-03-25T17:36:36Z"
    ]
  },
  {
    "trade_id": "open_AMD_2026-03-25T17:36:41.154751+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:41.154751+00:00",
      "2026-03-25T17:36:41Z"
    ]
  },
  {
    "trade_id": "open_HOOD_2026-03-25T17:36:56.532735+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:56.532735+00:00",
      "2026-03-25T17:36:56Z"
    ]
  },
  {
    "trade_id": "open_SOFI_2026-03-25T17:37:05.823732+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:37:05.823732+00:00",
      "2026-03-25T17:37:05Z"
    ]
  }
]
```

## Violation examples — normalized key duplicates

```json
[
  {
    "normalized_trade_id": "open_GM_2026-03-25T17:35:44+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:35:44.149365+00:00",
      "2026-03-25T17:35:44Z"
    ]
  },
  {
    "normalized_trade_id": "open_SLB_2026-03-25T17:35:58+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:35:58.181511+00:00",
      "2026-03-25T17:35:58Z"
    ]
  },
  {
    "normalized_trade_id": "open_TSLA_2026-03-25T17:36:00+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:00.702283+00:00",
      "2026-03-25T17:36:00Z"
    ]
  },
  {
    "normalized_trade_id": "open_MRNA_2026-03-25T17:36:19+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:19.569583+00:00",
      "2026-03-25T17:36:19Z"
    ]
  },
  {
    "normalized_trade_id": "open_COIN_2026-03-25T17:36:36+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:36.155798+00:00",
      "2026-03-25T17:36:36Z"
    ]
  },
  {
    "normalized_trade_id": "open_AMD_2026-03-25T17:36:41+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:41.154751+00:00",
      "2026-03-25T17:36:41Z"
    ]
  },
  {
    "normalized_trade_id": "open_HOOD_2026-03-25T17:36:56+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:36:56.532735+00:00",
      "2026-03-25T17:36:56Z"
    ]
  },
  {
    "normalized_trade_id": "open_SOFI_2026-03-25T17:37:05+00:00",
    "row_count": 2,
    "timestamps": [
      "2026-03-25T17:37:05.823732+00:00",
      "2026-03-25T17:37:05Z"
    ]
  }
]
```

## Violation examples — economic payload duplicates (blocking if non-empty)

```json
[]
```
