# Alpha 10 — Massive offline review

- **Input:** `C:\Dev\stock-bot\reports\research\alpha10_labeled_cohort.jsonl`  
- **Trades:** 532  
- **Feature columns:** 34 (unassigned to any of 10 groups: 0)  
- **Method:** z-score columns → group mean per `10` families → cluster mean → point-biserial vs `label`.  

## 1) Canonical algorithm buckets (name heuristics)

| ID | Name | Substring keys |
|---:|------|----------------|
| 0 | OFI | `ftd_pressure, ftd, institutional, motif_bonus, motif, ofi, order_flow, orderflow, delta_volume` |
| 1 | GEX | `gex, gamma_exposure, greeks_gamma, dealer_gamma, charm` |
| 2 | VAMP | `freshness, market_tide, vamp, volume_at, vwap_dev, vwap, tide` |
| 3 | HMM | `hmm, regime_id, regime_state, markov, hidden_state, regime, calendar` |
| 4 | ETF | `etf_flow, etf_, sector_etf, sector_alignment, risk_on` |
| 5 | FLOW | `shorts_squeeze, squeeze_score, squeeze, shorts, whale, sweep, urgency, conviction, flow_strength, flow` |
| 6 | DARK | `dark_pool, darkpool, darkpool_bias, dp_, block_net` |
| 7 | IV_SK | `iv_, skew, smile, percentile_iv, iv_rank` |
| 8 | OI | `oi_, open_interest, net_oi` |
| 9 | SENT | `sentiment, sentiment_score, toxicity, x_news, congress_, congress, insider, event, earnings` |

## 2) Top 25 clusters (size 3) by |ρ| (point-biserial)

| Rank | Algorithms | ρ | p-value | |ρ| |
|-----:|------------|--:|--------:|----:|
| 1 | HMM + ETF + SENT | -0.1291 | 0.002863 | 0.1291 |
| 2 | OFI + HMM + SENT | -0.1270 | 0.003347 | 0.1270 |
| 3 | HMM + OI + SENT | -0.1259 | 0.003617 | 0.1259 |
| 4 | HMM + FLOW + OI | -0.1259 | 0.003633 | 0.1259 |
| 5 | OFI + HMM + FLOW | -0.1245 | 0.004013 | 0.1245 |
| 6 | VAMP + HMM + SENT | -0.1240 | 0.004165 | 0.1240 |
| 7 | VAMP + HMM + FLOW | -0.1240 | 0.004188 | 0.1240 |
| 8 | HMM + ETF + FLOW | -0.1233 | 0.004397 | 0.1233 |
| 9 | HMM + FLOW + IV_SK | -0.1227 | 0.004588 | 0.1227 |
| 10 | HMM + DARK + SENT | -0.1225 | 0.004672 | 0.1225 |
| 11 | HMM + FLOW + DARK | -0.1214 | 0.005037 | 0.1214 |
| 12 | HMM + FLOW + SENT | -0.1211 | 0.005141 | 0.1211 |
| 13 | HMM + IV_SK + SENT | -0.1210 | 0.005187 | 0.1210 |
| 14 | GEX + HMM + FLOW | -0.1168 | 0.006979 | 0.1168 |
| 15 | GEX + HMM + SENT | -0.1108 | 0.01051 | 0.1108 |
| 16 | OFI + HMM + OI | -0.1065 | 0.01395 | 0.1065 |
| 17 | VAMP + HMM + OI | -0.1053 | 0.01509 | 0.1053 |
| 18 | HMM + IV_SK + OI | -0.1045 | 0.01591 | 0.1045 |
| 19 | OFI + VAMP + HMM | -0.1041 | 0.01628 | 0.1041 |
| 20 | OFI + HMM + ETF | -0.1041 | 0.01631 | 0.1041 |
| 21 | HMM + ETF + OI | -0.1040 | 0.0164 | 0.1040 |
| 22 | OFI + OI + SENT | -0.1034 | 0.08942 | 0.1034 |
| 23 | OFI + HMM + IV_SK | -0.1033 | 0.0172 | 0.1033 |
| 24 | VAMP + HMM + IV_SK | -0.1024 | 0.01814 | 0.1024 |
| 25 | VAMP + HMM + ETF | -0.1014 | 0.01928 | 0.1014 |

## 2) Top 25 clusters (size 4) by |ρ| (point-biserial)

| Rank | Algorithms | ρ | p-value | |ρ| |
|-----:|------------|--:|--------:|----:|
| 1 | OFI + HMM + ETF + SENT | -0.1270 | 0.003333 | 0.1270 |
| 2 | OFI + HMM + FLOW + OI | -0.1264 | 0.003496 | 0.1264 |
| 3 | OFI + HMM + OI + SENT | -0.1264 | 0.003498 | 0.1264 |
| 4 | VAMP + HMM + FLOW + OI | -0.1256 | 0.003699 | 0.1256 |
| 5 | HMM + ETF + FLOW + OI | -0.1251 | 0.003853 | 0.1251 |
| 6 | HMM + ETF + OI + SENT | -0.1249 | 0.003901 | 0.1249 |
| 7 | HMM + FLOW + IV_SK + OI | -0.1247 | 0.003963 | 0.1247 |
| 8 | OFI + VAMP + HMM + FLOW | -0.1247 | 0.003972 | 0.1247 |
| 9 | OFI + VAMP + HMM + SENT | -0.1245 | 0.004039 | 0.1245 |
| 10 | OFI + HMM + ETF + FLOW | -0.1240 | 0.004179 | 0.1240 |
| 11 | VAMP + HMM + OI + SENT | -0.1238 | 0.004254 | 0.1238 |
| 12 | OFI + HMM + FLOW + IV_SK | -0.1237 | 0.004261 | 0.1237 |
| 13 | HMM + ETF + FLOW + SENT | -0.1235 | 0.004332 | 0.1235 |
| 14 | VAMP + HMM + ETF + SENT | -0.1233 | 0.004387 | 0.1233 |
| 15 | VAMP + HMM + FLOW + IV_SK | -0.1232 | 0.00442 | 0.1232 |
| 16 | VAMP + HMM + ETF + FLOW | -0.1232 | 0.004423 | 0.1232 |
| 17 | HMM + FLOW + OI + SENT | -0.1231 | 0.004469 | 0.1231 |
| 18 | HMM + FLOW + DARK + OI | -0.1230 | 0.004486 | 0.1230 |
| 19 | HMM + ETF + DARK + SENT | -0.1227 | 0.004583 | 0.1227 |
| 20 | OFI + HMM + FLOW + DARK | -0.1222 | 0.004756 | 0.1222 |
| 21 | HMM + FLOW + DARK + SENT | -0.1220 | 0.004843 | 0.1220 |
| 22 | OFI + HMM + IV_SK + SENT | -0.1219 | 0.004866 | 0.1219 |
| 23 | OFI + HMM + FLOW + SENT | -0.1217 | 0.00495 | 0.1217 |
| 24 | HMM + ETF + FLOW + IV_SK | -0.1216 | 0.004992 | 0.1216 |
| 25 | HMM + IV_SK + OI + SENT | -0.1215 | 0.005018 | 0.1215 |

## 3) Coverage — finite rows per algorithm aggregate

| Algorithm | finite % |
|-----------|--------:|
| OFI | 10.9% |
| GEX | 10.9% |
| VAMP | 10.9% |
| HMM | 100.0% |
| ETF | 100.0% |
| FLOW | 100.0% |
| DARK | 100.0% |
| IV_SK | 10.9% |
| OI | 10.9% |
| SENT | 50.9% |

## 4) Interpretation (Quant / SRE)

- **Heuristic buckets** map many similarly named columns; refine mappings before production ML.
- **Point-biserial** is a linear screen; interactions and nonlinearity are not modeled here.
- **Look-ahead:** features are entry-time snapshots + `entry_uw` where present — verify no post-entry leakage for your modeling policy.
