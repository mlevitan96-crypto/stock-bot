# ALPACA strict completeness arming - proof summary (20260325_1724Z)

## 1) STRICT_EPOCH_START and why

- **STRICT_EPOCH_START:** `1774458080.0` (2026-03-25T17:01:20+00:00)
- **Why:** Forward-only strict learning cohort boundary from `stock-bot.service` restart / chain-validation era (2026-03-25T17:01:20Z UTC).

## 2) Wait outcome and first post-era evidence

- **WAIT_STATUS:** `POST_ERA_EVIDENCE_SATISFIED`
- **Evidence snapshot (last iteration):** `{
"iteration": 8,
"exit_attribution_post_era_count": 7,
"orders_close_position_post_era_count": 7,
"unified_alpaca_exit_post_era_count": 7,
"examples_exit_attribution": [
{
"symbol": "AMD",
"timestamp": "2026-03-25T17:31:19.010694+00:00",
"trade_id": "open_AMD_2026-03-25T17:00:34.675846+00:00"
},
{
"symbol": "AMZN",
"timestamp": "2026-03-25T17:31:22.289151+00:00",
"trade_id": "open_AMZN_2026-03-25T16:55:39.648677+00:00"
},
{
"symbol": "BA",
"timestamp": "2026-03-25T17:31:25.531246+00:00",
"trade_id": "open_BA_2026-03-25T17:00:03.584932+00:00"
}
],
"examples_orders_close": [
{
"symbol": "AMD",
"timestamp": "2026-03-25T17:31:19.010473+00:00"
},
{
"symbol": "AMZN",
"timestamp": "2026-03-25T17:31:22.288988+00:00"
},
{
"symbol": "BA",
"timestamp": "2026-03-25T17:31:25.530973+00:00"
}
],
"examples_unified_exit": [
{
"symbol": "AMD",
"timestamp": "2026-03-25T17:31:19.010694+00:00",
"trade_id": "open_AMD_2026-03-25T17:00:34.675846+00:00"
},
{
"symbol": "AMZN",
"timestamp": "2026-03-25T17:31:22.289151+00:00",
"trade_id": "open_AMZN_2026-03-25T16:55:39.648677+00:00"
},
{
"symbol": "BA",
"timestamp": "2026-03-25T17:31:25.531246+00:00",
"trade_id": "open_BA_2026-03-25T17:00:03.584932+00:00"
}
]
}`


**First post-era terminal close (exit_attribution):** {
  "symbol": "AMD",
  "timestamp": "2026-03-25T17:31:19.010694+00:00",
  "trade_id": "open_AMD_2026-03-25T17:00:34.675846+00:00"
}

**First post-era unified exit:** {
  "symbol": "AMD",
  "timestamp": "2026-03-25T17:31:19.010694+00:00",
  "trade_id": "open_AMD_2026-03-25T17:00:34.675846+00:00"
}

## 3) Strict audit (`open_ts_epoch=1774458080.0`)

- **trades_seen:** 7
- **trades_complete:** 6
- **trades_incomplete:** 1
- **reason_histogram:** `{"entry_decision_not_joinable_by_canonical_trade_id": 1, "missing_unified_entry_attribution": 1, "no_orders_rows_with_canonical_trade_id": 1, "missing_exit_intent_for_canonical_trade_id": 1}`

## 4) Chain matrices (up to 3)

```json
[
  {
    "trade_id": "open_LCID_2026-03-25T16:20:57.882391+00:00",
    "symbol": "LCID",
    "authoritative_join_key": "LCID|LONG|1774455657",
    "trade_key_from_exit": "LCID|LONG|1774455657",
    "alias_sample": [
      "LCID|LONG|1774455657"
    ],
    "matrix": {
      "trade_intent_entered_present": false,
      "unified_entry_attribution_present": false,
      "orders_rows_canonical_trade_id_present": false,
      "exit_intent_keyed_present": false,
      "unified_exit_attribution_terminal_close": true,
      "exit_attribution_jsonl_row": true
    },
    "reasons": [
      "entry_decision_not_joinable_by_canonical_trade_id",
      "missing_unified_entry_attribution",
      "no_orders_rows_with_canonical_trade_id",
      "missing_exit_intent_for_canonical_trade_id"
    ]
  },
  {
    "trade_id": "open_AMD_2026-03-25T17:00:34.675846+00:00",
    "symbol": "AMD",
    "authoritative_join_key": "AMD|LONG|1774458034",
    "trade_key_from_exit": "AMD|LONG|1774458034",
    "alias_sample": [
      "AMD|LONG|1774458017",
      "AMD|LONG|1774458034"
    ],
    "matrix": {
      "trade_intent_entered_present": true,
      "unified_entry_attribution_present": true,
      "orders_rows_canonical_trade_id_present": true,
      "exit_intent_keyed_present": true,
      "unified_exit_attribution_terminal_close": true,
      "exit_attribution_jsonl_row": true
    },
    "reasons": []
  },
  {
    "trade_id": "open_AMZN_2026-03-25T16:55:39.648677+00:00",
    "symbol": "AMZN",
    "authoritative_join_key": "AMZN|LONG|1774457739",
    "trade_key_from_exit": "AMZN|LONG|1774457739",
    "alias_sample": [
      "AMZN|LONG|1774457730",
      "AMZN|LONG|1774457739"
    ],
    "matrix": {
      "trade_intent_entered_present": true,
      "unified_entry_attribution_present": true,
      "orders_rows_canonical_trade_id_present": true,
      "exit_intent_keyed_present": true,
      "unified_exit_attribution_terminal_close": true,
      "exit_attribution_jsonl_row": true
    },
    "reasons": []
  }
]
```

## 5) CSA FINAL VERDICT

- **BLOCKED**
- **Exact condition:** incomplete_trade_chain

