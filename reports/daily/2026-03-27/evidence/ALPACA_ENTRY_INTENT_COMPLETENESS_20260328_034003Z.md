# Alpaca entry intent completeness (Kraken field mapping)

**Evidence host:** alpaca_droplet  
**ET report date:** 2026-03-27  
**Generated (UTC):** 20260328_034003Z

## Kraken → Alpaca mapping

| Kraken (mission) | Alpaca |
|------------------|--------|
| signal_trace | intelligence_trace (trade_intent, joined) OR raw_signals (unified/dedicated alpaca_entry_attribution) |
| entry_score_total | composite_score (unified or logs/alpaca_entry_attribution.jsonl) |
| entry_score_components | contributions or raw_signals (same sources) |

## Strict cohort context

- `trades_seen` (strict window): 255
- `trades_complete`: 255
- `trade_intent` entered rows scanned (run.jsonl + strict_backfill): 579
- Non-synthetic `trade_intent` entered rows: 0

## Sample

- Sample size: **255** (target ≥20 strict-complete trades; full set if smaller)
- signal_trace pass: **False** (0/255 OK)
- entry_score_total pass: **False** (0/255 OK)
- entry_score_components pass: **False** (0/255 OK)

## Violations (capped)

```json
[
  {
    "trade_id": "open_PLTR_2026-03-27T13:37:23.892879+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_AMD_2026-03-27T13:37:29.024491+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_GM_2026-03-27T13:37:14.425311+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_BA_2026-03-27T13:35:39.204583+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_TSLA_2026-03-27T13:37:40.460081+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_BAC_2026-03-27T13:36:38.714955+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_NVDA_2026-03-27T13:38:03.620450+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_MRNA_2026-03-27T13:37:52.268924+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_COP_2026-03-27T13:39:02.565081+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_MS_2026-03-27T13:39:25.367322+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_HOOD_2026-03-27T13:38:09.872446+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_HD_2026-03-27T13:37:04.803714+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_JPM_2026-03-27T13:36:23.375857+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_XLP_2026-03-27T13:36:49.362388+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_INTC_2026-03-27T13:38:15.749574+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_LCID_2026-03-27T13:37:04.806312+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_LOW_2026-03-27T13:37:04.806994+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_MA_2026-03-27T13:37:04.807565+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_META_2026-03-27T13:37:04.808116+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_MSFT_2026-03-27T13:37:04.808604+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_XLI_2026-03-27T13:37:05.050548+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_XLF_2026-03-27T13:34:19.395274+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_XLV_2026-03-27T13:35:17.808622+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_IWM_2026-03-27T13:37:04.804359+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  },
  {
    "trade_id": "open_QQQ_2026-03-27T13:37:05.048433+00:00",
    "signal_trace": false,
    "entry_score_total": false,
    "entry_score_components": false,
    "had_joined_trade_intent": true
  }
]
```

## Full machine JSON

```json
{
  "strict_completeness_trades_seen": 255,
  "strict_completeness_complete": 255,
  "trade_intent_entered_rows_total": 579,
  "trade_intent_entered_non_synthetic_count": 0,
  "sample_trade_ids": [
    "open_PLTR_2026-03-27T13:37:23.892879+00:00",
    "open_AMD_2026-03-27T13:37:29.024491+00:00",
    "open_GM_2026-03-27T13:37:14.425311+00:00",
    "open_BA_2026-03-27T13:35:39.204583+00:00",
    "open_TSLA_2026-03-27T13:37:40.460081+00:00",
    "open_BAC_2026-03-27T13:36:38.714955+00:00",
    "open_NVDA_2026-03-27T13:38:03.620450+00:00",
    "open_MRNA_2026-03-27T13:37:52.268924+00:00",
    "open_COP_2026-03-27T13:39:02.565081+00:00",
    "open_MS_2026-03-27T13:39:25.367322+00:00",
    "open_HOOD_2026-03-27T13:38:09.872446+00:00",
    "open_HD_2026-03-27T13:37:04.803714+00:00",
    "open_JPM_2026-03-27T13:36:23.375857+00:00",
    "open_XLP_2026-03-27T13:36:49.362388+00:00",
    "open_INTC_2026-03-27T13:38:15.749574+00:00",
    "open_LCID_2026-03-27T13:37:04.806312+00:00",
    "open_LOW_2026-03-27T13:37:04.806994+00:00",
    "open_MA_2026-03-27T13:37:04.807565+00:00",
    "open_META_2026-03-27T13:37:04.808116+00:00",
    "open_MSFT_2026-03-27T13:37:04.808604+00:00",
    "open_XLI_2026-03-27T13:37:05.050548+00:00",
    "open_XLF_2026-03-27T13:34:19.395274+00:00",
    "open_XLV_2026-03-27T13:35:17.808622+00:00",
    "open_IWM_2026-03-27T13:37:04.804359+00:00",
    "open_QQQ_2026-03-27T13:37:05.048433+00:00",
    "open_XLE_2026-03-27T13:37:05.050098+00:00",
    "open_XLK_2026-03-27T13:37:05.050967+00:00",
    "open_LCID_2026-03-27T14:13:44.570577+00:00",
    "open_PLTR_2026-03-27T14:13:57.582321+00:00",
    "open_GM_2026-03-27T14:14:10.444138+00:00",
    "open_HOOD_2026-03-27T14:14:19.727991+00:00",
    "open_SOFI_2026-03-27T14:14:32.505126+00:00",
    "open_NIO_2026-03-27T14:14:46.004754+00:00",
    "open_COIN_2026-03-27T14:14:57.236249+00:00",
    "open_COP_2026-03-27T14:15:14.800791+00:00",
    "open_F_2026-03-27T14:15:25.293321+00:00",
    "open_SLB_2026-03-27T14:15:34.825504+00:00",
    "open_RIVN_2026-03-27T14:15:39.989954+00:00",
    "open_BA_2026-03-27T14:18:40.422901+00:00",
    "open_BAC_2026-03-27T14:19:19.590080+00:00",
    "open_XOM_2026-03-27T14:16:13.675938+00:00",
    "open_C_2026-03-27T14:17:44.068035+00:00",
    "open_CVX_2026-03-27T14:16:30.330251+00:00",
    "open_MS_2026-03-27T14:16:52.421008+00:00",
    "open_MA_2026-03-27T14:17:05.400231+00:00",
    "open_XLP_2026-03-27T14:17:52.257370+00:00",
    "open_XLI_2026-03-27T14:18:14.261300+00:00",
    "open_WFC_2026-03-27T14:18:27.065990+00:00",
    "open_DIA_2026-03-27T14:19:32.931715+00:00",
    "open_JPM_2026-03-27T14:18:58.516844+00:00",
    "open_LCID_2026-03-27T14:54:15.142103+00:00",
    "open_PLTR_2026-03-27T14:54:28.273106+00:00",
    "open_AMD_2026-03-27T15:00:23.634231+00:00",
    "open_GM_2026-03-27T14:54:39.394796+00:00",
    "open_BAC_2026-03-27T14:59:50.084532+00:00",
    "open_HOOD_2026-03-27T14:54:45.215020+00:00",
    "open_C_2026-03-27T14:56:45.952255+00:00",
    "open_INTC_2026-03-27T14:54:58.650182+00:00",
    "open_SOFI_2026-03-27T14:55:12.013525+00:00",
    "open_NIO_2026-03-27T14:55:21.418073+00:00",
    "open_COP_2026-03-27T14:55:38.267195+00:00",
    "open_COIN_2026-03-27T14:55:44.465493+00:00",
    "open_MS_2026-03-27T14:56:03.063013+00:00",
    "open_F_2026-03-27T14:56:14.320601+00:00",
    "open_SLB_2026-03-27T14:56:23.425713+00:00",
    "open_RIVN_2026-03-27T14:56:56.816340+00:00",
    "open_XLK_2026-03-27T14:57:02.167207+00:00",
    "open_CVX_2026-03-27T14:57:35.476827+00:00",
    "open_XOM_2026-03-27T14:57:53.851211+00:00",
    "open_XLE_2026-03-27T14:58:04.216627+00:00",
    "open_WFC_2026-03-27T14:58:21.821072+00:00",
    "open_MA_2026-03-27T14:58:39.307924+00:00",
    "open_NFLX_2026-03-27T14:59:06.632158+00:00",
    "open_JPM_2026-03-27T14:59:22.214606+00:00",
    "open_QQQ_2026-03-27T15:00:11.008581+00:00",
    "open_NVDA_2026-03-27T15:01:06.628237+00:00",
    "open_XLP_2026-03-27T15:01:44.500423+00:00",
    "open_TSLA_2026-03-27T15:02:43.414458+00:00",
    "open_BAC_2026-03-27T15:46:52.333891+00:00",
    "open_C_2026-03-27T15:42:18.094438+00:00",
    "open_COIN_2026-03-27T15:40:33.537821+00:00",
    "open_COP_2026-03-27T15:38:35.544469+00:00",
    "open_CVX_2026-03-27T15:47:30.451441+00:00",
    "open_F_2026-03-27T15:40:38.209694+00:00",
    "open_GM_2026-03-27T15:38:44.558243+00:00",
    "open_HOOD_2026-03-27T15:39:28.835064+00:00",
    "open_JPM_2026-03-27T15:46:30.629025+00:00",
    "open_LCID_2026-03-27T15:45:05.175362+00:00",
    "open_LOW_2026-03-27T15:41:00.909354+00:00",
    "open_PLTR_2026-03-27T15:39:10.394512+00:00",
    "open_MA_2026-03-27T15:45:51.962826+00:00",
    "open_NVDA_2026-03-27T15:39:13.831208+00:00",
    "open_MRNA_2026-03-27T15:39:26.534557+00:00",
    "open_MS_2026-03-27T15:41:56.080173+00:00",
    "open_MSFT_2026-03-27T15:39:43.719688+00:00",
    "open_UNH_2026-03-27T15:39:49.544035+00:00",
    "open_SOFI_2026-03-27T15:39:52.048545+00:00",
    "open_TGT_2026-03-27T15:40:14.904263+00:00",
    "open_RIVN_2026-03-27T15:42:26.284570+00:00",
    "open_SLB_2026-03-27T15:40:40.645295+00:00",
    "open_XLK_2026-03-27T15:43:54.093145+00:00",
    "open_XLI_2026-03-27T15:43:59.661205+00:00",
    "open_XLV_2026-03-27T15:44:09.162652+00:00",
    "open_WFC_2026-03-27T15:45:34.521993+00:00",
    "open_XLP_2026-03-27T15:47:09.498369+00:00",
    "open_XOM_2026-03-27T15:47:40.525711+00:00",
    "open_AMD_2026-03-27T15:38:55.393953+00:00",
    "open_TSLA_2026-03-27T15:39:01.893558+00:00",
    "open_INTC_2026-03-27T15:39:31.129680+00:00",
    "open_LCID_2026-03-27T16:20:43.778560+00:00",
    "open_GM_2026-03-27T16:20:57.243087+00:00",
    "open_PLTR_2026-03-27T16:21:20.378088+00:00",
    "open_COIN_2026-03-27T16:21:29.550118+00:00",
    "open_BAC_2026-03-27T16:25:21.041488+00:00",
    "open_C_2026-03-27T16:22:10.149175+00:00",
    "open_SOFI_2026-03-27T16:21:34.961665+00:00",
    "open_COP_2026-03-27T16:21:45.204821+00:00",
    "open_MS_2026-03-27T16:21:50.453925+00:00",
    "open_SLB_2026-03-27T16:22:03.562268+00:00",
    "open_RIVN_2026-03-27T16:22:15.844786+00:00",
    "open_XLK_2026-03-27T16:22:24.452759+00:00",
    "open_F_2026-03-27T16:22:41.374115+00:00",
    "open_XOM_2026-03-27T16:23:18.848454+00:00",
    "open_XLE_2026-03-27T16:23:40.743809+00:00",
    "open_WFC_2026-03-27T16:23:53.272199+00:00",
    "open_MA_2026-03-27T16:24:01.481501+00:00",
    "open_CVX_2026-03-27T16:24:19.130331+00:00",
    "open_JPM_2026-03-27T16:24:51.449229+00:00",
    "open_JNJ_2026-03-27T16:25:40.926940+00:00",
    "open_XLP_2026-03-27T16:25:57.475575+00:00",
    "open_XLI_2026-03-27T16:26:07.717788+00:00",
    "open_XLV_2026-03-27T16:26:15.275464+00:00",
    "open_HOOD_2026-03-27T16:26:27.033192+00:00",
    "open_QQQ_2026-03-27T16:26:27.289284+00:00",
    "open_NVDA_2026-03-27T16:27:06.684112+00:00",
    "open_NIO_2026-03-27T15:39:58.269241+00:00",
    "open_CVX_2026-03-27T17:03:19.227991+00:00",
    "open_COP_2026-03-27T17:03:57.664452+00:00",
    "open_TGT_2026-03-27T17:04:05.840968+00:00",
    "open_MRNA_2026-03-27T17:04:19.197889+00:00",
    "open_UNH_2026-03-27T17:04:32.546452+00:00",
    "open_SLB_2026-03-27T17:04:45.612064+00:00",
    "open_XOM_2026-03-27T17:05:16.551855+00:00",
    "open_PFE_2026-03-27T17:05:28.149052+00:00",
    "open_JNJ_2026-03-27T17:05:48.179762+00:00",
    "open_WMT_2026-03-27T17:06:09.251867+00:00",
    "open_PLTR_2026-03-27T17:06:34.561197+00:00",
    "open_MSFT_2026-03-27T17:06:43.375453+00:00",
    "open_SOFI_2026-03-27T17:06:53.174309+00:00",
    "open_F_2026-03-27T17:07:45.192428+00:00",
    "open_HOOD_2026-03-27T17:08:52.944853+00:00",
    "open_HD_2026-03-27T17:03:46.057917+00:00",
    "open_LOW_2026-03-27T17:03:32.186967+00:00",
    "open_AMD_2026-03-27T17:07:40.662085+00:00",
    "open_TSLA_2026-03-27T17:07:53.459563+00:00",
    "open_NVDA_2026-03-27T17:07:59.338738+00:00",
    "open_AAPL_2026-03-27T17:08:13.014043+00:00",
    "open_INTC_2026-03-27T17:09:01.458738+00:00",
    "open_XLK_2026-03-27T17:09:40.668153+00:00",
    "open_C_2026-03-27T17:09:30.249376+00:00",
    "open_COIN_2026-03-27T17:07:23.312644+00:00",
    "open_GM_2026-03-27T17:06:28.997705+00:00",
    "open_MA_2026-03-27T17:10:10.954891+00:00",
    "open_MS_2026-03-27T17:09:23.862309+00:00",
    "open_NIO_2026-03-27T17:06:59.431303+00:00",
    "open_RIVN_2026-03-27T17:08:05.917288+00:00",
    "open_WFC_2026-03-27T17:09:53.310243+00:00",
    "open_AAPL_2026-03-27T17:47:09.684929+00:00",
    "open_AMD_2026-03-27T17:43:26.661037+00:00",
    "open_PLTR_2026-03-27T17:43:13.865150+00:00",
    "open_AMZN_2026-03-27T17:49:47.136316+00:00",
    "open_C_2026-03-27T17:46:20.209529+00:00",
    "open_COIN_2026-03-27T17:45:32.433568+00:00",
    "open_COP_2026-03-27T17:45:19.294502+00:00",
    "open_TSLA_2026-03-27T17:43:39.763118+00:00",
    "open_CVX_2026-03-27T17:47:17.529822+00:00",
    "open_NVDA_2026-03-27T17:43:42.694172+00:00",
    "open_GOOGL_2026-03-27T17:52:24.930561+00:00",
    "open_HOOD_2026-03-27T17:44:05.915547+00:00",
    "open_MRNA_2026-03-27T17:43:55.462787+00:00",
    "open_INTC_2026-03-27T17:44:14.900030+00:00",
    "open_LCID_2026-03-27T17:53:04.953756+00:00",
    "open_LOW_2026-03-27T17:46:58.646367+00:00",
    "open_MA_2026-03-27T17:49:21.524891+00:00",
    "open_UNH_2026-03-27T17:44:30.889645+00:00",
    "open_MS_2026-03-27T17:46:10.517947+00:00",
    "open_SOFI_2026-03-27T17:44:33.063286+00:00",
    "open_MSFT_2026-03-27T17:48:24.564672+00:00",
    "open_PFE_2026-03-27T17:49:26.564847+00:00",
    "open_TGT_2026-03-27T17:45:52.587694+00:00",
    "open_RIVN_2026-03-27T17:47:04.131709+00:00",
    "open_SLB_2026-03-27T17:46:38.427590+00:00",
    "open_WFC_2026-03-27T17:48:52.729086+00:00",
    "open_WMT_2026-03-27T17:49:00.788248+00:00",
    "open_XLK_2026-03-27T17:47:15.338552+00:00",
    "open_XLE_2026-03-27T17:49:58.557484+00:00",
    "open_XOM_2026-03-27T17:47:29.694341+00:00",
    "open_AAPL_2026-03-27T18:29:02.259927+00:00",
    "open_AMD_2026-03-27T18:27:01.657869+00:00",
    "open_AMZN_2026-03-27T18:30:02.644607+00:00",
    "open_BA_2026-03-27T18:26:41.565932+00:00",
    "open_C_2026-03-27T18:33:16.545492+00:00",
    "open_GM_2026-03-27T17:43:08.512156+00:00",
    "open_NIO_2026-03-27T17:44:57.527697+00:00",
    "open_COIN_2026-03-27T18:32:11.864343+00:00",
    "open_F_2026-03-27T17:46:15.641894+00:00",
    "open_TSLA_2026-03-27T18:25:54.507197+00:00",
    "open_COP_2026-03-27T18:28:47.926563+00:00",
    "open_CVX_2026-03-27T18:26:20.229271+00:00",
    "open_XOM_2026-03-27T18:26:33.022490+00:00",
    "open_NVDA_2026-03-27T18:27:41.528122+00:00",
    "open_MRNA_2026-03-27T18:28:02.444524+00:00",
    "open_MSFT_2026-03-27T18:28:11.783704+00:00",
    "open_UNH_2026-03-27T18:28:29.178487+00:00",
    "open_TGT_2026-03-27T18:29:19.718014+00:00",
    "open_SLB_2026-03-27T18:29:28.996108+00:00",
    "open_GOOGL_2026-03-27T18:30:21.670497+00:00",
    "open_LOW_2026-03-27T18:29:50.318674+00:00",
    "open_HD_2026-03-27T18:30:56.157674+00:00",
    "open_HOOD_2026-03-27T18:32:45.936704+00:00",
    "open_INTC_2026-03-27T18:31:49.379219+00:00",
    "open_JNJ_2026-03-27T18:31:31.352390+00:00",
    "open_PFE_2026-03-27T18:30:39.658961+00:00",
    "open_WMT_2026-03-27T18:31:15.301913+00:00",
    "open_PLTR_2026-03-27T18:31:40.089300+00:00",
    "open_SOFI_2026-03-27T18:31:54.405115+00:00",
    "open_MS_2026-03-27T18:33:08.630491+00:00",
    "open_LCID_2026-03-27T19:08:21.386032+00:00",
    "open_PLTR_2026-03-27T19:08:33.157217+00:00",
    "open_GM_2026-03-27T19:08:46.359104+00:00",
    "open_AMD_2026-03-27T19:08:59.291778+00:00",
    "open_TSLA_2026-03-27T19:09:25.192128+00:00",
    "open_HOOD_2026-03-27T19:09:34.293508+00:00",
    "open_UNH_2026-03-27T19:09:44.631586+00:00",
    "open_C_2026-03-27T19:12:20.376525+00:00",
    "open_INTC_2026-03-27T19:09:57.679484+00:00",
    "open_SOFI_2026-03-27T19:10:16.336086+00:00",
    "open_NIO_2026-03-27T19:10:35.299114+00:00",
    "open_COP_2026-03-27T19:10:46.916642+00:00",
    "open_TGT_2026-03-27T19:11:16.117179+00:00",
    "open_MS_2026-03-27T19:11:30.032732+00:00",
    "open_SLB_2026-03-27T19:12:03.913375+00:00",
    "open_COIN_2026-03-27T19:16:07.511055+00:00",
    "open_RIVN_2026-03-27T19:12:28.795963+00:00",
    "open_CVX_2026-03-27T19:13:44.399432+00:00",
    "open_XLK_2026-03-27T19:12:44.404539+00:00",
    "open_F_2026-03-27T19:16:07.760115+00:00",
    "open_XOM_2026-03-27T19:13:55.764104+00:00",
    "open_LOW_2026-03-27T19:16:08.005004+00:00",
    "open_WMT_2026-03-27T19:14:14.661192+00:00",
    "open_MA_2026-03-27T19:15:25.682777+00:00",
    "open_PFE_2026-03-27T19:14:52.467447+00:00",
    "open_MRNA_2026-03-27T19:16:08.264366+00:00",
    "open_WFC_2026-03-27T19:15:06.902812+00:00",
    "open_XLE_2026-03-27T19:16:08.518236+00:00"
  ],
  "sample_size": 255,
  "kraken_field_mapping": {
    "signal_trace": "intelligence_trace (trade_intent, joined) OR raw_signals (unified/dedicated alpaca_entry_attribution)",
    "entry_score_total": "composite_score (unified or logs/alpaca_entry_attribution.jsonl)",
    "entry_score_components": "contributions or raw_signals (same sources)"
  },
  "pass_signal_trace": false,
  "pass_entry_score_total": false,
  "pass_entry_score_components": false,
  "pass_all": false,
  "no_sample_reason": null,
  "violations": [
    {
      "trade_id": "open_PLTR_2026-03-27T13:37:23.892879+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_AMD_2026-03-27T13:37:29.024491+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_GM_2026-03-27T13:37:14.425311+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_BA_2026-03-27T13:35:39.204583+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_TSLA_2026-03-27T13:37:40.460081+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_BAC_2026-03-27T13:36:38.714955+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_NVDA_2026-03-27T13:38:03.620450+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_MRNA_2026-03-27T13:37:52.268924+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_COP_2026-03-27T13:39:02.565081+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_MS_2026-03-27T13:39:25.367322+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_HOOD_2026-03-27T13:38:09.872446+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_HD_2026-03-27T13:37:04.803714+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_JPM_2026-03-27T13:36:23.375857+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_XLP_2026-03-27T13:36:49.362388+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_INTC_2026-03-27T13:38:15.749574+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_LCID_2026-03-27T13:37:04.806312+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_LOW_2026-03-27T13:37:04.806994+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_MA_2026-03-27T13:37:04.807565+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_META_2026-03-27T13:37:04.808116+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_MSFT_2026-03-27T13:37:04.808604+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_XLI_2026-03-27T13:37:05.050548+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_XLF_2026-03-27T13:34:19.395274+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_XLV_2026-03-27T13:35:17.808622+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_IWM_2026-03-27T13:37:04.804359+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    },
    {
      "trade_id": "open_QQQ_2026-03-27T13:37:05.048433+00:00",
      "signal_trace": false,
      "entry_score_total": false,
      "entry_score_components": false,
      "had_joined_trade_intent": true
    }
  ],
  "counts": {
    "signal_trace_ok": 0,
    "entry_score_total_ok": 0,
    "entry_score_components_ok": 0
  }
}
```
