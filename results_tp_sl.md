# TP/SL grid search — strict cohort MFE/MAE
- **Generated (UTC):** 2026-04-13T19:41:38.040771+00:00
- **Root:** `/root/stock-bot`
- **open_ts_epoch:** `1775581260.0` (STRICT_EPOCH_START default)
- **Strict cohort trade_ids:** 519 | **Joined exit rows:** 518 | **Skipped:** 1
- **Trades with ≥1 1m bar in window:** 518 / 518

## 1) Top 15 TP/SL by profit factor (then total PnL %)
| Rank | TP % | SL % | Win rate | Total PnL % | Profit factor | Wins | Losses |
|-----:|-----:|-----:|---------:|--------------:|--------------:|-----:|-------:|
| 1 | 3.50 | -0.25 | 34.36% | 10.28% | 1.143 | 178 | 340 |
| 2 | 4.00 | -0.25 | 34.36% | 10.27% | 1.143 | 178 | 340 |
| 3 | 4.25 | -0.25 | 34.36% | 9.72% | 1.135 | 178 | 340 |
| 4 | 4.50 | -0.25 | 34.36% | 9.55% | 1.133 | 178 | 340 |
| 5 | 4.75 | -0.25 | 34.36% | 9.55% | 1.133 | 178 | 340 |
| 6 | 5.00 | -0.25 | 34.36% | 9.55% | 1.133 | 178 | 340 |
| 7 | 3.75 | -0.25 | 34.36% | 9.52% | 1.132 | 178 | 340 |
| 8 | 3.25 | -0.25 | 34.36% | 9.28% | 1.129 | 178 | 340 |
| 9 | 3.00 | -0.25 | 34.36% | 8.56% | 1.119 | 178 | 340 |
| 10 | 2.25 | -0.25 | 34.36% | 7.45% | 1.104 | 178 | 340 |
| 11 | 2.75 | -0.25 | 34.36% | 7.31% | 1.101 | 178 | 340 |
| 12 | 2.50 | -0.25 | 34.36% | 6.06% | 1.084 | 178 | 340 |
| 13 | 2.00 | -0.25 | 34.36% | 5.47% | 1.076 | 178 | 340 |
| 14 | 1.75 | -0.25 | 34.36% | 3.32% | 1.046 | 178 | 340 |
| 15 | 3.50 | -0.50 | 40.93% | 2.16% | 1.022 | 212 | 306 |

## 2) MAE “statistical dead zone” (winners, 1m bars)
- Among **225** trades with **actual PnL % > 0** and non-empty bars: **5th percentile of MAE%** = **-0.512%**.
- Interpretation (approx): **~95%** of winning trades had MAE **no worse (lower or equal adverse excursion)** than about **-0.512%** (MAE is typically ≤ 0 for longs; for shorts the sign convention matches `_mfe_mae_from_bars`).

## 3) MFE “exhaustion” (all trades with bars)
- **95th percentile of MFE%** across trades with bars: **1.483%** (~**5%** of trades exceeded this favorable excursion).

## 4) Raw cohort summary (actual exit)
- Mean actual PnL %: **-0.047%** | Median: **-0.039%** | Win rate (actual): **43.44%**

## 5) Method notes
- **Bars:** Alpaca `1Min` between entry/exit (±2m pad), one merged fetch per symbol.
- **Same-minute TP+SL:** SL assumed first (conservative).
- **No fills:** If Alpaca returns no bars, counterfactual falls back to **actual** exit return only.
