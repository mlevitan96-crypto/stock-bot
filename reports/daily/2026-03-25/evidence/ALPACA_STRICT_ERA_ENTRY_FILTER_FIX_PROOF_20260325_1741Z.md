# ALPACA strict era entry filter - full proof (20260325_1741Z)

## Audit JSON

```json
{
  "ROOT": "/root/stock-bot",
  "OPEN_TS_UTC_EPOCH": 1774458080.0,
  "STRICT_EPOCH_START": 1774458080.0,
  "strict_cohort_entry_era_floor_applied": true,
  "strict_cohort_excluded_preera_open_count": 29,
  "strict_cohort_exclusion_reasons": {
    "PREERA_OPEN": 29
  },
  "excluded_trade_ids_capped": [
    "open_AMD_2026-03-25T17:00:34.675846+00:00",
    "open_AMZN_2026-03-25T16:55:39.648677+00:00",
    "open_BA_2026-03-25T17:00:03.584932+00:00",
    "open_BAC_2026-03-25T16:52:51.211013+00:00",
    "open_COIN_2026-03-25T16:58:41.514540+00:00",
    "open_C_2026-03-25T16:58:28.765671+00:00",
    "open_LCID_2026-03-25T16:20:57.882391+00:00",
    "open_COP_2026-03-25T16:58:02.632944+00:00",
    "open_CVX_2026-03-25T16:59:07.620009+00:00",
    "open_JNJ_2026-03-25T16:53:04.682791+00:00",
    "open_F_2026-03-25T16:58:14.541016+00:00",
    "open_HD_2026-03-25T16:53:15.048423+00:00",
    "open_GM_2026-03-25T16:57:19.575655+00:00",
    "open_XLI_2026-03-25T16:53:20.639282+00:00",
    "open_GOOGL_2026-03-25T16:55:28.241602+00:00",
    "open_XOM_2026-03-25T16:54:55.424466+00:00",
    "open_XLF_2026-03-25T16:55:16.560850+00:00",
    "open_HOOD_2026-03-25T16:57:32.843472+00:00",
    "open_NFLX_2026-03-25T16:56:14.782732+00:00",
    "open_QQQ_2026-03-25T16:56:57.571323+00:00"
  ],
  "precheck": [],
  "trades_seen": 0,
  "trades_complete": 0,
  "trades_incomplete": 0,
  "reason_histogram": {},
  "incomplete_examples": [],
  "code_structural_trade_intent_no_canonical_on_entered": false,
  "LEARNING_STATUS": "BLOCKED",
  "learning_fail_closed_reason": "NO_POST_DEPLOY_PROOF_YET",
  "AUTHORITATIVE_JOIN_KEY_RULE": "Per closed trade: trade_key from unified alpaca_exit_attribution (or derived from open_{SYM}_{entry_ts} trade_id + exit row side). Expand aliases using undirected canonical_trade_id_intent <-> canonical_trade_id_fill edges from run.jsonl so trade_intent(entered) keyed at intent-time still joins to fill-time keys. Do not use a single per-symbol 'latest fill' as the join key (multiple positions per symbol would collide).",
  "incomplete_trade_ids_by_reason": {},
  "chain_matrices_sample": [],
  "chain_matrices_complete_sample": []
}
```

