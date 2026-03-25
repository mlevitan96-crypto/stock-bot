# ALPACA strict era entry filter - proof summary (20260325_1741Z)

## 1) STRICT_EPOCH_START and why

- **STRICT_EPOCH_START:** `1774458080.0` (2026-03-25T17:01:20Z UTC)
- **Why:** Forward-only strict learning boundary; cohort membership uses **position open** time from `trade_id`, not only exit time.

## 2) Cohort rule and code

- **Rule:** After exit-time floor (`open_ts_epoch`), include a trade only if open instant parsed from `open_<SYM>_<ISO8601>` is **>=** that floor. Pre-era opens that close post-era are excluded (`PREERA_OPEN`).
- **Implementation:** `telemetry/alpaca_strict_completeness_gate.py` (`evaluate_completeness`, `_open_epoch_from_trade_id`).

## 3) Exclusions

- **strict_cohort_excluded_preera_open_count:** 29
- **strict_cohort_exclusion_reasons:** `{"PREERA_OPEN": 29}`
- **excluded_trade_ids_capped (20):** `["open_AMD_2026-03-25T17:00:34.675846+00:00", "open_AMZN_2026-03-25T16:55:39.648677+00:00", "open_BA_2026-03-25T17:00:03.584932+00:00", "open_BAC_2026-03-25T16:52:51.211013+00:00", "open_COIN_2026-03-25T16:58:41.514540+00:00", "open_C_2026-03-25T16:58:28.765671+00:00", "open_LCID_2026-03-25T16:20:57.882391+00:00", "open_COP_2026-03-25T16:58:02.632944+00:00", "open_CVX_2026-03-25T16:59:07.620009+00:00", "open_JNJ_2026-03-25T16:53:04.682791+00:00", "open_F_2026-03-25T16:58:14.541016+00:00", "open_HD_2026-03-25T16:53:15.048423+00:00", "open_GM_2026-03-25T16:57:19.575655+00:00", "open_XLI_2026-03-25T16:53:20.639282+00:00", "open_GOOGL_2026-03-25T16:55:28.241602+00:00", "open_XOM_2026-03-25T16:54:55.424466+00:00", "open_XLF_2026-03-25T16:55:16.560850+00:00", "open_HOOD_2026-03-25T16:57:32.843472+00:00", "open_NFLX_2026-03-25T16:56:14.782732+00:00", "open_QQQ_2026-03-25T16:56:57.571323+00:00"]`
Sample excluded list includes an LCID trade_id (pre-era open).

**Note:** `trades_seen == 0` with positive `PREERA_OPEN` exclusions means every terminal close in the exit-time window came from a position **opened before** STRICT_EPOCH_START. Learning stays fail-closed until at least one close whose `trade_id` embeds an open time `>=` STRICT_EPOCH_START.


## 4) Strict audit (post filter)

- **trades_seen:** 0
- **trades_complete:** 0
- **trades_incomplete:** 0
- **reason_histogram:** `{}`

## 5) Chain matrices (up to 3)

Vacuous cohort: matrices may be empty. When `trades_incomplete > 0`, incomplete samples populate; when `ARMED`, complete samples populate.

```json
[]
```

## 6) CSA FINAL VERDICT

- **BLOCKED**
- **Exact condition:** NO_POST_DEPLOY_PROOF_YET

