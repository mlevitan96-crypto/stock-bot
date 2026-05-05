# SHADOW vs LIVE Deep Dive — 2026-05-01

## Data source & build metadata
- Generated at (UTC): **2026-05-01T21:31:00.963090+00:00**
- Host: **ubuntu-s-1vcpu-2gb-nyc3-01-alpaca**
- Platform: **Linux-6.8.0-107-generic-x86_64-with-glibc2.39**
- Repo root: `/root/stock-bot`
- Mode: **single**

### Missing inputs (best-effort; report still generated)
- logs/shadow_trades.jsonl (not applicable: shadow removed)
- telemetry/2026-05-01/ (missing)

## SHADOW INTEGRITY AUDIT
| check | count |
| --- | --- |

- Notes:
  - price_bounds_source: `shadow_events (current_price/entry_price/exit_price)`
  - market_hours: `America/New_York regular session 09:30–16:00 (best-effort)`
  - issues_capped: `False`

### Sample issues (capped)
- None detected.

## 1. TOP-LINE SUMMARY
| Metric | LIVE | SHADOW | DELTA (SHADOW-LIVE) |
| --- | --- | --- | --- |
| Total trades (all) | 650 | 0 | -650 |
| Total trades (closed) | 366 | 0 | -366 |
| PnL realized (USD) | -71.57 | 0.00 | 71.57 |
| PnL unrealized (USD) | 0.00 | 0.00 | 0.00 |
| PnL total (USD) | -71.57 | 0.00 | 71.57 |
| Win rate (closed) | 35.25% | 0.00% | -35.25% |
| Expectancy (USD/trade, closed) | -0.1955 | 0.0000 | 0.1955 |
| Avg time-in-trade (min, closed) | 41.65 | n/a | n/a |
| Long/short mix (all) | {'long': 647, 'short': 3} | {} | n/a |

### Exit reason distribution (closed trades)
- LIVE:
  - `{'stale_alpha_cutoff(1059min,0.00%)': 1, 'underwater_time_decay_stop': 6, 'stale_alpha_cutoff(1048min,0.00%)': 2, 'stale_alpha_cutoff(1048min,0.03%)': 1, 'stale_alpha_cutoff(1075min,0.00%)': 1, 'stale_alpha_cutoff(1068min,0.00%)': 1, 'dynamic_atr_trailing_stop': 249, 'trail_stop(-0.0%)': 3, 'signal_decay(0.85)': 1, 'displaced_by_XLK|delta=0.87|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_MSFT|delta=-0.366|age_s=0.0|thesis=displacement_delta_too_small': 2, 'displaced_by_WMT|delta=-0.844|age_s=0.0|thesis=displacement_delta_too_small': 2, 'trail_stop+drawdown(3.8%)': 1, 'displaced_by_PLTR|delta=1.687|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_AMD|delta=1.647|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_INTC|delta=1.637|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_COIN|delta=1.205|age_s=0.0|thesis=displacement_min_hold': 2, 'displaced_by_AMZN|delta=1.1|age_s=0.0|thesis=displacement_min_hold': 2, 'displaced_by_AMD|delta=1.754|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'signal_decay(0.78)': 3, 'displaced_by_AMZN|delta=1.648|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_IWM|delta=1.523|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_COP|delta=0.911|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_V|delta=-0.654|age_s=0.0|thesis=displacement_delta_too_small': 2, 'signal_decay(0.94)': 6, 'signal_decay(0.91)': 2, 'signal_decay(0.90)': 1, 'signal_decay(0.88)': 1, 'displaced_by_NVDA|delta=2.277|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_AMD|delta=1.485|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_AAPL|delta=1.149|age_s=0.0|thesis=displacement_min_hold': 2, 'displaced_by_META|delta=1.033|age_s=0.0|thesis=displacement_min_hold': 2, 'signal_decay(0.93)': 4, 'signal_decay(0.84)': 2, 'displaced_by_V|delta=-0.913|age_s=0.0|thesis=displacement_delta_too_small': 2, 'signal_decay(0.81)': 1, 'signal_decay(0.63)': 1, 'displaced_by_BA|delta=1.203|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'signal_decay(0.83)': 1, 'signal_decay(0.69)': 2, 'signal_decay(0.64)': 1, 'signal_decay(0.66)': 2, 'displaced_by_WMT|delta=1.064|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_F|delta=1.4824|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_JNJ|delta=-0.451|age_s=0.0|thesis=displacement_delta_too_small': 2, 'displaced_by_NVDA|delta=2.4202|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_NIO|delta=1.4138|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_F|delta=1.3606|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_DIA|delta=1.3336|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_MA|delta=1.0962|age_s=0.0|thesis=displacement_min_hold': 2, 'signal_decay(0.70)': 6, 'signal_decay(0.71)': 1, 'signal_decay(0.68)': 2, 'signal_decay(0.67)': 2, 'signal_decay(0.75)': 1, 'signal_decay(0.77)': 1, 'displaced_by_GOOGL|delta=2.0046|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_SLB|delta=1.9258|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_WMT|delta=1.8304|age_s=0.0|thesis=displacement_no_thesis_domin/ace': 2}`
- SHADOW:
  - `{}`

## SHADOW PERFORMANCE (MULTI-DAY)
| metric | value |
| --- | --- |
| Total shadow trades (all) | 0 |
| Total shadow trades (closed) | 0 |
| Shadow realized pnl (USD) | 0.00 |
| Shadow expectancy (USD/trade, closed) | 0.0000 |
| Shadow win rate (closed) | 0.00% |
| Shadow long/short mix (all) | {} |

### Shadow PnL by symbol (closed trades)
| symbol | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- |

### Shadow PnL by sector (closed trades)
| sector | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- |

### Shadow PnL by regime (closed trades)
| regime | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- |

### Shadow PnL by long vs short (closed trades)
| side | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- |

### Shadow PnL by exit_reason (closed trades)
| exit_reason | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- |


### Top 20 shadow winners (full detail; closed trades)
| trade_id | symbol | side | entry_ts | exit_ts | entry_price | exit_price | qty | pnl_usd | exit_reason | signals | sector | regime | tmin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

### Top 20 shadow losers (full detail; closed trades)
| trade_id | symbol | side | entry_ts | exit_ts | entry_price | exit_price | qty | pnl_usd | exit_reason | signals | sector | regime | tmin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |


## 2. PER-SYMBOL PERFORMANCE
| symbol | live_pnl_usd | shadow_pnl_usd | delta_pnl_usd | live_trade_count | shadow_trade_count | live long/short | shadow long/short | shadow expectancy | exit reasons (shadow) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BLK | -20.03 | 0.00 | 20.03 | 23 | 0 | {'long': 23} | {} | 0.0000 | {} |
| RIVN | -19.28 | 0.00 | 19.28 | 16 | 0 | {'long': 16} | {} | 0.0000 | {} |
| COST | -8.22 | 0.00 | 8.22 | 9 | 0 | {'long': 9} | {} | 0.0000 | {} |
| META | -8.03 | 0.00 | 8.03 | 17 | 0 | {'long': 17} | {} | 0.0000 | {} |
| MRNA | -7.24 | 0.00 | 7.24 | 21 | 0 | {'long': 21} | {} | 0.0000 | {} |
| CAT | -7.04 | 0.00 | 7.04 | 2 | 0 | {'long': 2} | {} | 0.0000 | {} |
| GS | -4.99 | 0.00 | 4.99 | 19 | 0 | {'long': 19} | {} | 0.0000 | {} |
| TGT | -4.50 | 0.00 | 4.50 | 27 | 0 | {'long': 27} | {} | 0.0000 | {} |
| COIN | -4.20 | 0.00 | 4.20 | 13 | 0 | {'long': 13} | {} | 0.0000 | {} |
| LOW | -3.80 | 0.00 | 3.80 | 4 | 0 | {'long': 4} | {} | 0.0000 | {} |
| NVDA | -3.80 | 0.00 | 3.80 | 2 | 0 | {'long': 2} | {} | 0.0000 | {} |
| XLI | -3.44 | 0.00 | 3.44 | 23 | 0 | {'long': 23} | {} | 0.0000 | {} |
| XOM | -3.34 | 0.00 | 3.34 | 29 | 0 | {'long': 29} | {} | 0.0000 | {} |
| AAPL | -2.69 | 0.00 | 2.69 | 15 | 0 | {'long': 15} | {} | 0.0000 | {} |
| SLB | -2.48 | 0.00 | 2.48 | 18 | 0 | {'long': 18} | {} | 0.0000 | {} |
| HD | -2.28 | 0.00 | 2.28 | 6 | 0 | {'long': 6} | {} | 0.0000 | {} |
| AMD | -2.22 | 0.00 | 2.22 | 8 | 0 | {'long': 8} | {} | 0.0000 | {} |
| BA | -2.20 | 0.00 | 2.20 | 1 | 0 | {'long': 1} | {} | 0.0000 | {} |
| XLP | -2.06 | 0.00 | 2.06 | 29 | 0 | {'long': 29} | {} | 0.0000 | {} |
| AMZN | -1.55 | 0.00 | 1.55 | 15 | 0 | {'long': 15} | {} | 0.0000 | {} |
| WMT | -1.18 | 0.00 | 1.18 | 8 | 0 | {'long': 8} | {} | 0.0000 | {} |
| UNH | -1.07 | 0.00 | 1.07 | 10 | 0 | {'long': 10} | {} | 0.0000 | {} |
| XLF | -0.71 | 0.00 | 0.71 | 26 | 0 | {'long': 26} | {} | 0.0000 | {} |
| JPM | -0.55 | 0.00 | 0.55 | 17 | 0 | {'long': 17} | {} | 0.0000 | {} |
| JNJ | -0.51 | 0.00 | 0.51 | 18 | 0 | {'long': 18} | {} | 0.0000 | {} |
| MS | -0.35 | 0.00 | 0.35 | 16 | 0 | {'long': 16} | {} | 0.0000 | {} |
| NFLX | -0.30 | 0.00 | 0.30 | 7 | 0 | {'long': 7} | {} | 0.0000 | {} |
| XLV | -0.04 | 0.00 | 0.04 | 24 | 0 | {'long': 24} | {} | 0.0000 | {} |
| COP | 0.00 | 0.00 | 0.00 | 2 | 0 | {'long': 2} | {} | 0.0000 | {} |
| WFC | 0.09 | 0.00 | -0.09 | 17 | 0 | {'long': 17} | {} | 0.0000 | {} |
| XLK | 0.39 | 0.00 | -0.39 | 20 | 0 | {'long': 20} | {} | 0.0000 | {} |
| QQQ | 0.49 | 0.00 | -0.49 | 23 | 0 | {'long': 23} | {} | 0.0000 | {} |
| PFE | 0.51 | 0.00 | -0.51 | 17 | 0 | {'long': 17} | {} | 0.0000 | {} |
| BAC | 0.58 | 0.00 | -0.58 | 8 | 0 | {'long': 8} | {} | 0.0000 | {} |
| HOOD | 0.93 | 0.00 | -0.93 | 14 | 0 | {'long': 14} | {} | 0.0000 | {} |
| V | 1.54 | 0.00 | -1.54 | 8 | 0 | {'long': 8} | {} | 0.0000 | {} |
| IWM | 2.01 | 0.00 | -2.01 | 15 | 0 | {'long': 15} | {} | 0.0000 | {} |
| MSFT | 2.92 | 0.00 | -2.92 | 10 | 0 | {'long': 10} | {} | 0.0000 | {} |
| SOFI | 3.54 | 0.00 | -3.54 | 16 | 0 | {'long': 16} | {} | 0.0000 | {} |
| SPY | 5.12 | 0.00 | -5.12 | 16 | 0 | {'long': 13, 'short': 3} | {} | 0.0000 | {} |
| INTC | 6.22 | 0.00 | -6.22 | 12 | 0 | {'long': 12} | {} | 0.0000 | {} |
| PLTR | 6.37 | 0.00 | -6.37 | 15 | 0 | {'long': 15} | {} | 0.0000 | {} |
| TSLA | 7.30 | 0.00 | -7.30 | 15 | 0 | {'long': 15} | {} | 0.0000 | {} |
| LCID | 8.52 | 0.00 | -8.52 | 19 | 0 | {'long': 19} | {} | 0.0000 | {} |

### Per-symbol detail (all symbols traded today)
<details><summary><b>BLK</b> — delta_pnl_usd=20.03 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -20.03 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 20.03 |
| live_trade_count | 23 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 23} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -1.6694 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'stale_alpha_cutoff(1059min,0.00%)': 1, 'dynamic_atr_trailing_stop': 10, 'signal_decay(0.67)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9476 | n/a | -0.9476 |
| market_tide | 0.2526 | n/a | -0.2526 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>RIVN</b> — delta_pnl_usd=19.28 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -19.28 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 19.28 |
| live_trade_count | 16 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 16} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -1.9284 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'trail_stop(-0.0%)': 1, 'signal_decay(0.91)': 1, 'dynamic_atr_trailing_stop': 7, 'signal_decay(0.70)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9775 | n/a | -0.9775 |
| market_tide | 0.2525 | n/a | -0.2525 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>COST</b> — delta_pnl_usd=8.22 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -8.22 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 8.22 |
| live_trade_count | 9 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 9} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -1.6440 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 3, 'displaced_by_NVDA\|delta=2.277\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.6111 | n/a | -2.6111 |
| freshness_factor | 0.8237 | n/a | -0.8237 |
| market_tide | 0.2579 | n/a | -0.2579 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>META</b> — delta_pnl_usd=8.03 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -8.03 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 8.03 |
| live_trade_count | 17 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 17} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.8922 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_V\|delta=-0.654\|age_s=0.0\|thesis=displacement_delta_too_small': 2, 'signal_decay(0.94)': 1, 'dynamic_atr_trailing_stop': 5, 'signal_decay(0.66)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5769 | n/a | -2.5769 |
| freshness_factor | 0.9725 | n/a | -0.9725 |
| market_tide | 0.2525 | n/a | -0.2525 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| iv_rank | -0.0600 | n/a | 0.0600 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>MRNA</b> — delta_pnl_usd=7.24 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -7.24 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 7.24 |
| live_trade_count | 21 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 21} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.5169 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'trail_stop(-0.0%)': 1, 'dynamic_atr_trailing_stop': 9, 'displaced_by_WMT\|delta=1.064\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_JNJ\|delta=-0.451\|age_s=0.0\|thesis=displacement_delta_too_small': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9713 | n/a | -0.9713 |
| market_tide | 0.2524 | n/a | -0.2524 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| oi_change | 0.1200 | n/a | -0.1200 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>CAT</b> — delta_pnl_usd=7.04 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -7.04 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 7.04 |
| live_trade_count | 2 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 2} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -7.0400 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'underwater_time_decay_stop': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9430 | n/a | -0.9430 |
| market_tide | 0.2760 | n/a | -0.2760 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0610 | n/a | -0.0610 |
| greeks_gamma | 0.0600 | n/a | -0.0600 |
| iv_rank | -0.0600 | n/a | 0.0600 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>GS</b> — delta_pnl_usd=4.99 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -4.99 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 4.99 |
| live_trade_count | 19 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 19} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.4990 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'stale_alpha_cutoff(1075min,0.00%)': 1, 'signal_decay(0.88)': 1, 'dynamic_atr_trailing_stop': 7, 'signal_decay(0.67)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9685 | n/a | -0.9685 |
| market_tide | 0.2539 | n/a | -0.2539 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0466 | n/a | -0.0466 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| oi_change | 0.0210 | n/a | -0.0210 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| squeeze_score | 0.0131 | n/a | -0.0131 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>TGT</b> — delta_pnl_usd=4.50 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -4.50 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 4.50 |
| live_trade_count | 27 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 27} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.3462 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'underwater_time_decay_stop': 1, 'signal_decay(0.93)': 1, 'signal_decay(0.81)': 1, 'dynamic_atr_trailing_stop': 10} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9669 | n/a | -0.9669 |
| market_tide | 0.2534 | n/a | -0.2534 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0509 | n/a | -0.0509 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| oi_change | 0.0210 | n/a | -0.0210 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| squeeze_score | 0.0127 | n/a | -0.0127 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>COIN</b> — delta_pnl_usd=4.20 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -4.20 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 4.20 |
| live_trade_count | 13 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 13} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.4667 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'stale_alpha_cutoff(1068min,0.00%)': 1, 'dynamic_atr_trailing_stop': 8} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9750 | n/a | -0.9750 |
| market_tide | 0.2524 | n/a | -0.2524 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| oi_change | 0.1200 | n/a | -0.1200 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>LOW</b> — delta_pnl_usd=3.80 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -3.80 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 3.80 |
| live_trade_count | 4 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 4} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -1.9000 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9645 | n/a | -0.9645 |
| market_tide | 0.2640 | n/a | -0.2640 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| iv_rank | -0.1200 | n/a | 0.1200 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0360 | n/a | -0.0360 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| oi_change | 0.0210 | n/a | -0.0210 |
| squeeze_score | 0.0210 | n/a | -0.0210 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>NVDA</b> — delta_pnl_usd=3.80 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -3.80 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 3.80 |
| live_trade_count | 2 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 2} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -1.9000 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_WMT\|delta=-0.844\|age_s=0.0\|thesis=displacement_delta_too_small': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | [] |
| signals used (shadow) | [] |

</details>

<details><summary><b>XLI</b> — delta_pnl_usd=3.44 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -3.44 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 3.44 |
| live_trade_count | 23 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 23} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.2867 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 10, 'displaced_by_IWM\|delta=1.523\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.9048 | n/a | -2.9048 |
| freshness_factor | 0.8749 | n/a | -0.8749 |
| market_tide | 0.2547 | n/a | -0.2547 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>XOM</b> — delta_pnl_usd=3.34 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -3.34 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 3.34 |
| live_trade_count | 29 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 29} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.2227 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'trail_stop(-0.0%)': 1, 'signal_decay(0.78)': 1, 'displaced_by_META\|delta=1.033\|age_s=0.0\|thesis=displacement_min_hold': 2, 'dynamic_atr_trailing_stop': 8, 'signal_decay(0.66)': 1, 'displaced_by_F\|delta=1.4824\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9683 | n/a | -0.9683 |
| market_tide | 0.2541 | n/a | -0.2541 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| oi_change | 0.1154 | n/a | -0.1154 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| iv_rank | -0.0644 | n/a | 0.0644 |
| greeks_gamma | 0.0533 | n/a | -0.0533 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| squeeze_score | 0.0133 | n/a | -0.0133 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>AAPL</b> — delta_pnl_usd=2.69 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -2.69 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 2.69 |
| live_trade_count | 15 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 15} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.3843 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 5, 'signal_decay(0.94)': 1, 'signal_decay(0.70)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.8750 | n/a | -2.8750 |
| freshness_factor | 0.9787 | n/a | -0.9787 |
| market_tide | 0.2526 | n/a | -0.2526 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>SLB</b> — delta_pnl_usd=2.48 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -2.48 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 2.48 |
| live_trade_count | 18 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 18} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.2066 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 10, 'displaced_by_NIO\|delta=1.4138\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9692 | n/a | -0.9692 |
| market_tide | 0.2523 | n/a | -0.2523 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| oi_change | 0.1198 | n/a | -0.1198 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>HD</b> — delta_pnl_usd=2.28 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -2.28 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 2.28 |
| live_trade_count | 6 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 6} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.7600 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 3} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.8333 | n/a | -2.8333 |
| freshness_factor | 0.9220 | n/a | -0.9220 |
| market_tide | 0.2600 | n/a | -0.2600 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>AMD</b> — delta_pnl_usd=2.22 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -2.22 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 2.22 |
| live_trade_count | 8 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 8} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.3171 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'underwater_time_decay_stop': 1, 'displaced_by_V\|delta=-0.913\|age_s=0.0\|thesis=displacement_delta_too_small': 2, 'dynamic_atr_trailing_stop': 4} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 3.0000 | n/a | -3.0000 |
| freshness_factor | 0.9760 | n/a | -0.9760 |
| market_tide | 0.2530 | n/a | -0.2530 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| iv_rank | -0.1200 | n/a | 0.1200 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>BA</b> — delta_pnl_usd=2.20 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -2.20 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 2.20 |
| live_trade_count | 1 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 1} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -2.2000 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | [] |
| signals used (shadow) | [] |

</details>

<details><summary><b>XLP</b> — delta_pnl_usd=2.06 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -2.06 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 2.06 |
| live_trade_count | 29 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 29} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.1469 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_COIN\|delta=1.205\|age_s=0.0\|thesis=displacement_min_hold': 2, 'dynamic_atr_trailing_stop': 12} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.9038 | n/a | -2.9038 |
| freshness_factor | 0.8583 | n/a | -0.8583 |
| market_tide | 0.2525 | n/a | -0.2525 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>AMZN</b> — delta_pnl_usd=1.55 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -1.55 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 1.55 |
| live_trade_count | 15 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 15} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.2214 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 5, 'signal_decay(0.91)': 1, 'signal_decay(0.75)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.6786 | n/a | -2.6786 |
| freshness_factor | 0.9661 | n/a | -0.9661 |
| market_tide | 0.2544 | n/a | -0.2544 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0531 | n/a | -0.0531 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| squeeze_score | 0.0133 | n/a | -0.0133 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>WMT</b> — delta_pnl_usd=1.18 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -1.18 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 1.18 |
| live_trade_count | 8 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 8} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.2950 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 4} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9672 | n/a | -0.9672 |
| market_tide | 0.2585 | n/a | -0.2585 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| oi_change | 0.1197 | n/a | -0.1197 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0660 | n/a | -0.0660 |
| iv_rank | -0.0600 | n/a | 0.0600 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| squeeze_score | 0.0165 | n/a | -0.0165 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>UNH</b> — delta_pnl_usd=1.07 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -1.07 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 1.07 |
| live_trade_count | 10 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 10} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.1529 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 4, 'signal_decay(0.84)': 1, 'signal_decay(0.64)': 1, 'signal_decay(0.68)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9700 | n/a | -0.9700 |
| market_tide | 0.2523 | n/a | -0.2523 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| iv_rank | 0.1200 | n/a | -0.1200 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0610 | n/a | -0.0610 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>XLF</b> — delta_pnl_usd=0.71 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -0.71 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 0.71 |
| live_trade_count | 26 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 26} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.0548 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 9, 'displaced_by_COP\|delta=0.911\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_SLB\|delta=1.9258\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.8800 | n/a | -2.8800 |
| freshness_factor | 0.8594 | n/a | -0.8594 |
| market_tide | 0.2544 | n/a | -0.2544 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>JPM</b> — delta_pnl_usd=0.55 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -0.55 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 0.55 |
| live_trade_count | 17 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 17} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.0550 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'underwater_time_decay_stop': 1, 'signal_decay(0.78)': 1, 'displaced_by_AAPL\|delta=1.149\|age_s=0.0\|thesis=displacement_min_hold': 2, 'dynamic_atr_trailing_stop': 6} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9596 | n/a | -0.9596 |
| market_tide | 0.2541 | n/a | -0.2541 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0528 | n/a | -0.0528 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| oi_change | 0.0237 | n/a | -0.0237 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| squeeze_score | 0.0132 | n/a | -0.0132 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>JNJ</b> — delta_pnl_usd=0.51 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -0.51 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 0.51 |
| live_trade_count | 18 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 18} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.0510 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_PLTR\|delta=1.687\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_AMD\|delta=1.754\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2, 'dynamic_atr_trailing_stop': 6} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.9062 | n/a | -2.9062 |
| freshness_factor | 0.8886 | n/a | -0.8886 |
| market_tide | 0.2566 | n/a | -0.2566 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>MS</b> — delta_pnl_usd=0.35 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -0.35 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 0.35 |
| live_trade_count | 16 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 16} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.0316 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'stale_alpha_cutoff(1048min,0.00%)': 1, 'dynamic_atr_trailing_stop': 7, 'signal_decay(0.94)': 1, 'signal_decay(0.78)': 1, 'signal_decay(0.77)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9519 | n/a | -0.9519 |
| market_tide | 0.2526 | n/a | -0.2526 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| oi_change | 0.0210 | n/a | -0.0210 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>NFLX</b> — delta_pnl_usd=0.30 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -0.30 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 0.30 |
| live_trade_count | 7 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 7} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.0750 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'underwater_time_decay_stop': 1, 'dynamic_atr_trailing_stop': 3} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9443 | n/a | -0.9443 |
| market_tide | 0.2530 | n/a | -0.2530 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| iv_rank | 0.1200 | n/a | -0.1200 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>XLV</b> — delta_pnl_usd=0.04 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | -0.04 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 0.04 |
| live_trade_count | 24 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 24} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | -0.0033 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_AMZN\|delta=1.1\|age_s=0.0\|thesis=displacement_min_hold': 2, 'dynamic_atr_trailing_stop': 10} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.8810 | n/a | -2.8810 |
| freshness_factor | 0.8939 | n/a | -0.8939 |
| market_tide | 0.2559 | n/a | -0.2559 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>COP</b> — delta_pnl_usd=0.00 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 0.00 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | 0.00 |
| live_trade_count | 2 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 2} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.0000 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_MA\|delta=1.0962\|age_s=0.0\|thesis=displacement_min_hold': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | [] |
| signals used (shadow) | [] |

</details>

<details><summary><b>WFC</b> — delta_pnl_usd=-0.09 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 0.09 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -0.09 |
| live_trade_count | 17 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 17} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.0113 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 7, 'signal_decay(0.70)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9508 | n/a | -0.9508 |
| market_tide | 0.2526 | n/a | -0.2526 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0610 | n/a | -0.0610 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>XLK</b> — delta_pnl_usd=-0.39 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 0.39 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -0.39 |
| live_trade_count | 20 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 20} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.0390 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 8, 'displaced_by_DIA\|delta=1.3336\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9726 | n/a | -0.9726 |
| market_tide | 0.2525 | n/a | -0.2525 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| oi_change | 0.0210 | n/a | -0.0210 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>QQQ</b> — delta_pnl_usd=-0.49 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 0.49 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -0.49 |
| live_trade_count | 23 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 23} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.0408 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'signal_decay(0.85)': 1, 'displaced_by_XLK\|delta=0.87\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2, 'dynamic_atr_trailing_stop': 7, 'displaced_by_WMT\|delta=1.8304\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.8500 | n/a | -2.8500 |
| freshness_factor | 0.8734 | n/a | -0.8734 |
| market_tide | 0.2549 | n/a | -0.2549 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>PFE</b> — delta_pnl_usd=-0.51 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 0.51 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -0.51 |
| live_trade_count | 17 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 17} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.0392 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_AMD\|delta=1.647\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2, 'displaced_by_AMZN\|delta=1.648\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2, 'dynamic_atr_trailing_stop': 7, 'displaced_by_BA\|delta=1.203\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 3.0000 | n/a | -3.0000 |
| freshness_factor | 0.8641 | n/a | -0.8641 |
| market_tide | 0.2522 | n/a | -0.2522 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0300 | n/a | -0.0300 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>BAC</b> — delta_pnl_usd=-0.58 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 0.58 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -0.58 |
| live_trade_count | 8 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 8} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.1450 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 2, 'signal_decay(0.93)': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9587 | n/a | -0.9587 |
| market_tide | 0.2585 | n/a | -0.2585 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| oi_change | 0.1197 | n/a | -0.1197 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0660 | n/a | -0.0660 |
| iv_rank | 0.0600 | n/a | -0.0600 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| squeeze_score | 0.0165 | n/a | -0.0165 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>HOOD</b> — delta_pnl_usd=-0.93 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 0.93 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -0.93 |
| live_trade_count | 14 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 14} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.1163 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 7, 'signal_decay(0.70)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9617 | n/a | -0.9617 |
| market_tide | 0.2524 | n/a | -0.2524 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>V</b> — delta_pnl_usd=-1.54 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 1.54 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -1.54 |
| live_trade_count | 8 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 8} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.7700 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_AMD\|delta=1.485\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9490 | n/a | -0.9490 |
| market_tide | 0.2524 | n/a | -0.2524 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| oi_change | 0.0210 | n/a | -0.0210 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>IWM</b> — delta_pnl_usd=-2.01 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 2.01 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -2.01 |
| live_trade_count | 15 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 15} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.2513 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'underwater_time_decay_stop': 1, 'dynamic_atr_trailing_stop': 5, 'displaced_by_F\|delta=1.3606\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5714 | n/a | -2.5714 |
| freshness_factor | 0.9675 | n/a | -0.9675 |
| market_tide | 0.2541 | n/a | -0.2541 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| squeeze_score | 0.0133 | n/a | -0.0133 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>MSFT</b> — delta_pnl_usd=-2.92 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 2.92 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -2.92 |
| live_trade_count | 10 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 10} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.4171 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'dynamic_atr_trailing_stop': 5, 'displaced_by_NVDA\|delta=2.4202\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.7000 | n/a | -2.7000 |
| freshness_factor | 0.9810 | n/a | -0.9810 |
| market_tide | 0.2524 | n/a | -0.2524 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| iv_rank | -0.1200 | n/a | 0.1200 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>SOFI</b> — delta_pnl_usd=-3.54 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 3.54 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -3.54 |
| live_trade_count | 16 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 16} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.3218 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_MSFT\|delta=-0.366\|age_s=0.0\|thesis=displacement_delta_too_small': 2, 'signal_decay(0.93)': 1, 'signal_decay(0.94)': 1, 'dynamic_atr_trailing_stop': 6, 'signal_decay(0.69)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9870 | n/a | -0.9870 |
| market_tide | 0.2526 | n/a | -0.2526 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0624 | n/a | -0.0624 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>SPY</b> — delta_pnl_usd=-5.12 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 5.12 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -5.12 |
| live_trade_count | 16 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 13, 'short': 3} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.5689 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'displaced_by_INTC\|delta=1.637\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2, 'dynamic_atr_trailing_stop': 4, 'signal_decay(0.63)': 1, 'displaced_by_GOOGL\|delta=2.0046\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace': 2} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.9000 | n/a | -2.9000 |
| freshness_factor | 0.9062 | n/a | -0.9062 |
| event | 0.2040 | n/a | -0.2040 |
| market_tide | 0.1951 | n/a | -0.1951 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| toxicity_correlation_penalty | -0.1300 | n/a | 0.1300 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0636 | n/a | -0.0636 |
| oi_change | 0.0420 | n/a | -0.0420 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| squeeze_score | 0.0264 | n/a | -0.0264 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| greeks_gamma | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>INTC</b> — delta_pnl_usd=-6.22 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 6.22 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -6.22 |
| live_trade_count | 12 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 12} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.7775 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'trail_stop+drawdown(3.8%)': 1, 'dynamic_atr_trailing_stop': 4, 'signal_decay(0.83)': 1, 'signal_decay(0.69)': 1, 'signal_decay(0.71)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.6250 | n/a | -2.6250 |
| freshness_factor | 0.9805 | n/a | -0.9805 |
| market_tide | 0.2522 | n/a | -0.2522 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| iv_rank | -0.1200 | n/a | 0.1200 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>PLTR</b> — delta_pnl_usd=-6.37 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 6.37 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -6.37 |
| live_trade_count | 15 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 15} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.7082 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'stale_alpha_cutoff(1048min,0.03%)': 1, 'signal_decay(0.84)': 1, 'dynamic_atr_trailing_stop': 6, 'signal_decay(0.70)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.6364 | n/a | -2.6364 |
| freshness_factor | 0.9854 | n/a | -0.9854 |
| market_tide | 0.2525 | n/a | -0.2525 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| iv_rank | 0.0180 | n/a | -0.0180 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>TSLA</b> — delta_pnl_usd=-7.30 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 7.30 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -7.30 |
| live_trade_count | 15 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 15} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.7300 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'stale_alpha_cutoff(1048min,0.00%)': 1, 'signal_decay(0.94)': 2, 'dynamic_atr_trailing_stop': 6, 'signal_decay(0.70)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.9000 | n/a | -2.9000 |
| freshness_factor | 0.9878 | n/a | -0.9878 |
| market_tide | 0.2524 | n/a | -0.2524 |
| oi_change | 0.2100 | n/a | -0.2100 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| iv_rank | 0.1200 | n/a | -0.1200 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| greeks_gamma | 0.0480 | n/a | -0.0480 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

<details><summary><b>LCID</b> — delta_pnl_usd=-8.52 shadow_exp=0.0000</summary>

| field | value |
| --- | --- |
| live_pnl_usd | 8.52 |
| shadow_pnl_usd | 0.00 |
| delta_pnl_usd | -8.52 |
| live_trade_count | 19 |
| shadow_trade_count | 0 |
| long/short mix (live) | {'long': 19} |
| long/short mix (shadow) | {} |
| expectancy (live, closed) | 0.9467 |
| expectancy (shadow, closed) | 0.0000 |
| exit reasons (live) | {'signal_decay(0.90)': 1, 'dynamic_atr_trailing_stop': 7, 'signal_decay(0.68)': 1} |
| exit reasons (shadow) | {} |
| signals used (live) | ['calendar', 'congress', 'dark_pool', 'etf_flow', 'event', 'flow', 'freshness_factor', 'ftd_pressure', 'greeks_gamma', 'insider', 'institutional', 'iv_rank', 'iv_skew', 'market_tide', 'motif_bonus', 'oi_change', 'regime', 'shorts_squeeze', 'smile', 'squeeze_score'] |
| signals used (shadow) | [] |

#### feature_snapshot averages (top deltas)
| feature | live_mean | shadow_mean | delta(shadow-live) |
| --- | --- | --- | --- |
| flow | 2.5000 | n/a | -2.5000 |
| freshness_factor | 0.9707 | n/a | -0.9707 |
| market_tide | 0.2526 | n/a | -0.2526 |
| event | 0.2040 | n/a | -0.2040 |
| toxicity_penalty | -0.1620 | n/a | 0.1620 |
| oi_change | 0.1199 | n/a | -0.1199 |
| insider | 0.0750 | n/a | -0.0750 |
| iv_skew | 0.0700 | n/a | -0.0700 |
| iv_rank | -0.0600 | n/a | 0.0600 |
| greeks_gamma | 0.0560 | n/a | -0.0560 |
| ftd_pressure | 0.0360 | n/a | -0.0360 |
| dark_pool | 0.0230 | n/a | -0.0230 |
| etf_flow | 0.0120 | n/a | -0.0120 |
| squeeze_score | 0.0120 | n/a | -0.0120 |
| regime | 0.0080 | n/a | -0.0080 |
| smile | 0.0040 | n/a | -0.0040 |
| calendar | 0.0000 | n/a | 0.0000 |
| congress | 0.0000 | n/a | 0.0000 |
| institutional | 0.0000 | n/a | 0.0000 |
| motif_bonus | 0.0000 | n/a | 0.0000 |
| shorts_squeeze | 0.0000 | n/a | 0.0000 |
| toxicity_correlation_penalty | 0.0000 | n/a | 0.0000 |
| whale | 0.0000 | n/a | 0.0000 |

</details>

## 3. PER-SIGNAL PERFORMANCE (LIVE VS SHADOW)
| signal | live expectancy | shadow expectancy | live win_rate | shadow win_rate | trade_count_live(closed) | trade_count_shadow(closed) | delta expectancy | regime breakdown (live) | regime breakdown (shadow) | sector breakdown (live) | sector breakdown (shadow) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| (no_signals) | -0.2051 | 0.0000 | 47.54% | 0.00% | 122 | 0 | 0.2051 | {'NEUTRAL': 13, 'unknown': 109} | {} | {'UNKNOWN': 122} | {} |
| calendar | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| congress | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| dark_pool | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| etf_flow | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| event | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| flow | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| freshness_factor | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| ftd_pressure | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| greeks_gamma | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| insider | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| institutional | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| iv_rank | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| iv_skew | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| market_tide | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| motif_bonus | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| oi_change | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| regime | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| shorts_squeeze | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| smile | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| squeeze_score | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| toxicity_correlation_penalty | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| toxicity_penalty | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |
| whale | -0.1908 | 0.0000 | 29.10% | 0.00% | 244 | 0 | 0.1908 | {'mixed': 206, 'NEUTRAL': 38} | {} | {'UNKNOWN': 244} | {} |


## 4. FEATURE EV CURVES (LIVE VS SHADOW)
| feature | n_live | n_shadow | drift_PSI | missing_rate | feature_stability_score | live EV curve | shadow EV curve |
| --- | --- | --- | --- | --- | --- | --- | --- |
| flow | 244 | 0 | n/a | 18.77% | 81.2 | bins=1 | bins=0 |
| dark_pool | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| insider | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| iv_skew | 244 | 0 | n/a | 18.77% | 81.2 | bins=1 | bins=0 |
| smile | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| whale | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| event | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| motif_bonus | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| toxicity_penalty | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| regime | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| congress | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| shorts_squeeze | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| institutional | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| market_tide | 244 | 0 | n/a | 18.77% | 81.2 | bins=3 | bins=0 |
| calendar | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| greeks_gamma | 244 | 0 | n/a | 18.77% | 81.2 | bins=2 | bins=0 |
| ftd_pressure | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| iv_rank | 244 | 0 | n/a | 18.77% | 81.2 | bins=3 | bins=0 |
| oi_change | 244 | 0 | n/a | 18.77% | 81.2 | bins=4 | bins=0 |
| etf_flow | 244 | 0 | n/a | 18.77% | 81.2 | bins=0 | bins=0 |
| squeeze_score | 244 | 0 | n/a | 18.77% | 81.2 | bins=1 | bins=0 |
| freshness_factor | 244 | 0 | n/a | 18.77% | 81.2 | bins=10 | bins=0 |
| toxicity_correlation_penalty | 244 | 0 | n/a | 18.77% | 81.2 | bins=1 | bins=0 |

### Replacement telemetry anomalies
- replacement_anomaly_detected (telemetry): **None**
### Non-numeric feature keys observed in `feature_snapshot` (not eligible for EV curves)
- none detected

### Full EV curves (all numeric features; collapsed)
<details><summary><b>flow</b> — drift_PSI=n/a stability=81.2</summary>

#### LIVE EV curve (binned)
| x_lo | x_hi | count | avg_pnl_usd |
| --- | --- | --- | --- |
| 2.5 | 3.0 | 244 | -0.1908 |

- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>dark_pool</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>insider</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>iv_skew</b> — drift_PSI=n/a stability=81.2</summary>

#### LIVE EV curve (binned)
| x_lo | x_hi | count | avg_pnl_usd |
| --- | --- | --- | --- |
| 0.038 | 0.07 | 244 | -0.1908 |

- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>smile</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>whale</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>event</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>motif_bonus</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>toxicity_penalty</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>regime</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>congress</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>shorts_squeeze</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>institutional</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>market_tide</b> — drift_PSI=n/a stability=81.2</summary>

#### LIVE EV curve (binned)
| x_lo | x_hi | count | avg_pnl_usd |
| --- | --- | --- | --- |
| -0.059 | 0.252 | 110 | 0.0149 |
| 0.252 | 0.253 | 114 | -0.3780 |
| 0.253 | 0.276 | 20 | -0.2545 |

- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>calendar</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>greeks_gamma</b> — drift_PSI=n/a stability=81.2</summary>

#### LIVE EV curve (binned)
| x_lo | x_hi | count | avg_pnl_usd |
| --- | --- | --- | --- |
| 0.0 | 0.048 | 236 | -0.1601 |
| 0.048 | 0.12 | 8 | -1.0937 |

- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>ftd_pressure</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>iv_rank</b> — drift_PSI=n/a stability=81.2</summary>

#### LIVE EV curve (binned)
| x_lo | x_hi | count | avg_pnl_usd |
| --- | --- | --- | --- |
| -0.12 | -0.06 | 41 | -0.2124 |
| -0.06 | 0.018 | 188 | -0.2186 |
| 0.018 | 0.12 | 15 | 0.2173 |

- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>oi_change</b> — drift_PSI=n/a stability=81.2</summary>

#### LIVE EV curve (binned)
| x_lo | x_hi | count | avg_pnl_usd |
| --- | --- | --- | --- |
| 0.021 | 0.042 | 130 | -0.3712 |
| 0.042 | 0.119 | 21 | -0.5414 |
| 0.119 | 0.12 | 35 | -0.0687 |
| 0.12 | 0.21 | 58 | 0.2671 |

- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>etf_flow</b> — drift_PSI=n/a stability=81.2</summary>

- LIVE EV curve: insufficient_data
- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>squeeze_score</b> — drift_PSI=n/a stability=81.2</summary>

#### LIVE EV curve (binned)
| x_lo | x_hi | count | avg_pnl_usd |
| --- | --- | --- | --- |
| 0.012 | 0.03 | 244 | -0.1908 |

- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>freshness_factor</b> — drift_PSI=n/a stability=81.2</summary>

#### LIVE EV curve (binned)
| x_lo | x_hi | count | avg_pnl_usd |
| --- | --- | --- | --- |
| 0.729 | 0.818 | 25 | -0.4196 |
| 0.818 | 0.905 | 25 | -0.2281 |
| 0.905 | 0.935 | 24 | -0.5196 |
| 0.935 | 0.946 | 26 | -0.3212 |
| 0.946 | 0.963 | 24 | -0.1282 |
| 0.963 | 0.97 | 24 | 0.0546 |
| 0.97 | 0.976 | 29 | -0.1852 |
| 0.976 | 0.982 | 18 | -0.3578 |
| 0.982 | 0.987 | 25 | -0.3442 |
| 0.987 | 0.998 | 24 | 0.5271 |

- SHADOW EV curve: insufficient_data
</details>

<details><summary><b>toxicity_correlation_penalty</b> — drift_PSI=n/a stability=81.2</summary>

#### LIVE EV curve (binned)
| x_lo | x_hi | count | avg_pnl_usd |
| --- | --- | --- | --- |
| -0.65 | 0.0 | 244 | -0.1908 |

- SHADOW EV curve: insufficient_data
</details>


## SHADOW FEATURE & SIGNAL KNOB AUDIT
### Feature knob audit (shadow-only)
| feature | n | monotonicity | slope | psi(first_vs_last_day) | missing_rate | flags |
| --- | --- | --- | --- | --- | --- | --- |


### Feature EV curves (shadow-only; collapsed)
### Signal family audit (shadow-only)
| signal | closed_n | pnl_usd | expectancy_usd | win_rate | regime_breakdown | sector_breakdown | advisory_note |
| --- | --- | --- | --- | --- | --- | --- | --- |


## SHADOW LONG/SHORT ENGINE AUDIT
### Long vs short (shadow, closed trades)
| side | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- |

### Long vs short by sector (shadow, closed trades)
| sector | side | n | pnl_usd | expectancy_usd |
| --- | --- | --- | --- | --- |

### Long vs short by regime (shadow, closed trades)
| regime | side | n | pnl_usd | expectancy_usd |
| --- | --- | --- | --- | --- |


### Symbols where long works but short fails (shadow, closed trades)
| symbol | long_n | long_exp | short_n | short_exp | long_pnl | short_pnl |
| --- | --- | --- | --- | --- | --- | --- |

### Symbols where short works but long fails (shadow, closed trades)
| symbol | long_n | long_exp | short_n | short_exp | long_pnl | short_pnl |
| --- | --- | --- | --- | --- | --- | --- |


## 5. REGIME & SECTOR ANALYSIS
### Regime timeline for the day (telemetry)
- (missing `telemetry/<date>/computed/regime_timeline.json`)

### Shadow vs live performance by regime (closed trades)
| regime | n_live | live pnl | live exp | n_shadow | shadow pnl | shadow exp |
| --- | --- | --- | --- | --- | --- | --- |
| NEUTRAL | 51 | 38.43 | 0.7535 | 0 | 0.00 | 0.0000 |
| mixed | 206 | -85.48 | -0.4150 | 0 | 0.00 | 0.0000 |
| unknown | 109 | -24.51 | -0.2248 | 0 | 0.00 | 0.0000 |


### Shadow vs live performance by sector (closed trades)
| sector | n_live | live pnl | live exp | n_shadow | shadow pnl | shadow exp |
| --- | --- | --- | --- | --- | --- | --- |
| UNKNOWN | 366 | -71.57 | -0.1955 | 0 | 0.00 | 0.0000 |


### Sector posture correctness / Regime alignment correctness / Volatility & trend buckets
- Best-effort only: shown when the required posture/bucket fields exist in `regime_snapshot` or telemetry state.

## 6. EXIT INTELLIGENCE ANALYSIS
### Exit reason performance (live vs shadow)
| exit_reason | n_live | live pnl | live exp | n_shadow | shadow pnl | shadow exp |
| --- | --- | --- | --- | --- | --- | --- |
| displaced_by_AAPL\|delta=1.149\|age_s=0.0\|thesis=displacement_min_hold | 2 | 0.34 | 0.1700 | 0 | n/a | n/a |
| displaced_by_AMD\|delta=1.485\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 1.54 | 0.7700 | 0 | n/a | n/a |
| displaced_by_AMD\|delta=1.647\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 0.18 | 0.0900 | 0 | n/a | n/a |
| displaced_by_AMD\|delta=1.754\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | -0.14 | -0.0700 | 0 | n/a | n/a |
| displaced_by_AMZN\|delta=1.1\|age_s=0.0\|thesis=displacement_min_hold | 2 | 0.78 | 0.3900 | 0 | n/a | n/a |
| displaced_by_AMZN\|delta=1.648\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 0.32 | 0.1600 | 0 | n/a | n/a |
| displaced_by_BA\|delta=1.203\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 0.40 | 0.2000 | 0 | n/a | n/a |
| displaced_by_COIN\|delta=1.205\|age_s=0.0\|thesis=displacement_min_hold | 2 | -0.30 | -0.1500 | 0 | n/a | n/a |
| displaced_by_COP\|delta=0.911\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 0.20 | 0.1000 | 0 | n/a | n/a |
| displaced_by_DIA\|delta=1.3336\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 1.62 | 0.8100 | 0 | n/a | n/a |
| displaced_by_F\|delta=1.3606\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 2.44 | 1.2200 | 0 | n/a | n/a |
| displaced_by_F\|delta=1.4824\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | -0.44 | -0.2200 | 0 | n/a | n/a |
| displaced_by_GOOGL\|delta=2.0046\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 0.30 | 0.1500 | 0 | n/a | n/a |
| displaced_by_INTC\|delta=1.637\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 5.02 | 2.5100 | 0 | n/a | n/a |
| displaced_by_IWM\|delta=1.523\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | -0.88 | -0.4400 | 0 | n/a | n/a |
| displaced_by_JNJ\|delta=-0.451\|age_s=0.0\|thesis=displacement_delta_too_small | 2 | 0.00 | 0.0000 | 0 | n/a | n/a |
| displaced_by_MA\|delta=1.0962\|age_s=0.0\|thesis=displacement_min_hold | 2 | 0.00 | 0.0000 | 0 | n/a | n/a |
| displaced_by_META\|delta=1.033\|age_s=0.0\|thesis=displacement_min_hold | 2 | -0.60 | -0.3000 | 0 | n/a | n/a |
| displaced_by_MSFT\|delta=-0.366\|age_s=0.0\|thesis=displacement_delta_too_small | 2 | 0.00 | 0.0000 | 0 | n/a | n/a |
| displaced_by_NIO\|delta=1.4138\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 0.84 | 0.4200 | 0 | n/a | n/a |
| displaced_by_NVDA\|delta=2.277\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | -2.26 | -1.1300 | 0 | n/a | n/a |
| displaced_by_NVDA\|delta=2.4202\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 0.66 | 0.3300 | 0 | n/a | n/a |
| displaced_by_PLTR\|delta=1.687\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 1.84 | 0.9200 | 0 | n/a | n/a |
| displaced_by_SLB\|delta=1.9258\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | -0.18 | -0.0900 | 0 | n/a | n/a |
| displaced_by_V\|delta=-0.654\|age_s=0.0\|thesis=displacement_delta_too_small | 2 | -6.64 | -3.3200 | 0 | n/a | n/a |
| displaced_by_V\|delta=-0.913\|age_s=0.0\|thesis=displacement_delta_too_small | 2 | -3.56 | -1.7800 | 0 | n/a | n/a |
| displaced_by_WMT\|delta=-0.844\|age_s=0.0\|thesis=displacement_delta_too_small | 2 | -3.80 | -1.9000 | 0 | n/a | n/a |
| displaced_by_WMT\|delta=1.064\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | -2.08 | -1.0400 | 0 | n/a | n/a |
| displaced_by_WMT\|delta=1.8304\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | -0.80 | -0.4000 | 0 | n/a | n/a |
| displaced_by_XLK\|delta=0.87\|age_s=0.0\|thesis=displacement_no_thesis_domin/ace | 2 | 0.08 | 0.0400 | 0 | n/a | n/a |
| dynamic_atr_trailing_stop | 249 | -96.41 | -0.3872 | 0 | n/a | n/a |
| signal_decay(0.63) | 1 | 1.04 | 1.0400 | 0 | n/a | n/a |
| signal_decay(0.64) | 1 | 0.62 | 0.6200 | 0 | n/a | n/a |
| signal_decay(0.66) | 2 | -0.44 | -0.2200 | 0 | n/a | n/a |
| signal_decay(0.67) | 2 | 1.07 | 0.5350 | 0 | n/a | n/a |
| signal_decay(0.68) | 2 | -0.04 | -0.0200 | 0 | n/a | n/a |
| signal_decay(0.69) | 2 | 1.16 | 0.5800 | 0 | n/a | n/a |
| signal_decay(0.70) | 6 | 6.43 | 1.0717 | 0 | n/a | n/a |
| signal_decay(0.71) | 1 | 2.56 | 2.5600 | 0 | n/a | n/a |
| signal_decay(0.75) | 1 | -0.54 | -0.5400 | 0 | n/a | n/a |
| signal_decay(0.77) | 1 | 0.18 | 0.1800 | 0 | n/a | n/a |
| signal_decay(0.78) | 3 | 1.93 | 0.6433 | 0 | n/a | n/a |
| signal_decay(0.81) | 1 | 0.42 | 0.4200 | 0 | n/a | n/a |
| signal_decay(0.83) | 1 | 0.66 | 0.6600 | 0 | n/a | n/a |
| signal_decay(0.84) | 2 | 2.39 | 1.1950 | 0 | n/a | n/a |
| signal_decay(0.85) | 1 | 3.22 | 3.2200 | 0 | n/a | n/a |
| signal_decay(0.88) | 1 | -0.54 | -0.5400 | 0 | n/a | n/a |
| signal_decay(0.90) | 1 | 7.36 | 7.3600 | 0 | n/a | n/a |
| signal_decay(0.91) | 2 | 4.95 | 2.4750 | 0 | n/a | n/a |
| signal_decay(0.93) | 4 | 0.44 | 0.1100 | 0 | n/a | n/a |
| signal_decay(0.94) | 6 | 10.28 | 1.7133 | 0 | n/a | n/a |
| stale_alpha_cutoff(1048min,0.00%) | 2 | 1.32 | 0.6610 | 0 | n/a | n/a |
| stale_alpha_cutoff(1048min,0.03%) | 1 | 6.53 | 6.5337 | 0 | n/a | n/a |
| stale_alpha_cutoff(1059min,0.00%) | 1 | 4.62 | 4.6167 | 0 | n/a | n/a |
| stale_alpha_cutoff(1068min,0.00%) | 1 | -1.38 | -1.3800 | 0 | n/a | n/a |
| stale_alpha_cutoff(1075min,0.00%) | 1 | 1.77 | 1.7700 | 0 | n/a | n/a |
| trail_stop(-0.0%) | 3 | -20.78 | -6.9253 | 0 | n/a | n/a |
| trail_stop+drawdown(3.8%) | 1 | 3.19 | 3.1900 | 0 | n/a | n/a |
| underwater_time_decay_stop | 6 | -8.46 | -1.4100 | 0 | n/a | n/a |


### Stop vs profit behavior (closed trades)
- LIVE:
| bucket | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- |
| other | 107 | 50.89 | 0.4756 | 63.55% |
| stop | 259 | -122.46 | -0.4728 | 23.55% |

- SHADOW:
| bucket | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- |


### Time-in-trade distribution (minutes, closed trades)
- LIVE: `{'n': 366, 'min': 0.0, 'p25': 4.22925405, 'p50': 9.098655883333333, 'p75': 21.242774716666666, 'max': 1077.9394216333333, 'mean': 41.645157545628415, 'median': 9.150758783333334}`
- SHADOW: `{'n': 0}`

### Exit score distribution (shadow only; exit_attribution)
- v2_exit_score stats: `{'n': 336, 'min': 0.0, 'p25': 0.0, 'p50': 0.0, 'p75': 0.0, 'max': 0.25, 'mean': 0.01273096392857143, 'median': 0.0}`

### Exit completeness & anomalies
- (missing `telemetry/<date>/computed/exit_intel_completeness.json`)

## 7. PARITY ANALYSIS (LIVE VS SHADOW)
- (missing `telemetry/<date>/computed/shadow_vs_live_parity.json`)

### Parity anomalies
- (missing `telemetry/<date>/computed/entry_parity_details.json`)

## 8. UW INTEL & EQUALIZER KNOB ANALYSIS
- UW intel snapshots found (telemetry state): **0**

- (No `uw_*` numeric features found in trade feature snapshots.)

## 9. LONG/SHORT CORRECTNESS AUDIT
### Long vs short performance (closed trades)
- LIVE:
| side | n | win_rate | pnl_realized_usd | expectancy_usd |
| --- | --- | --- | --- | --- |
| long | 364 | 34.89% | -71.87 | -0.1974 |
| short | 2 | 100.00% | 0.30 | 0.1500 |

- SHADOW:
| side | n | win_rate | pnl_realized_usd | expectancy_usd |
| --- | --- | --- | --- | --- |


### Sector-specific long/short correctness (shadow, closed trades)
| sector | side | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- | --- |


### Regime-specific long/short correctness (shadow, closed trades)
| regime | side | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- | --- |


### Symbol-level long/short correctness (shadow, closed trades)
| symbol | side | n | pnl_usd | expectancy_usd | win_rate |
| --- | --- | --- | --- | --- | --- |


## 10. SHADOW PROMOTION READINESS SCORE
| component | points | why |
| --- | --- | --- |
| shadow_outperforming_live | 20.0 | shadow pnl > live pnl by 71.57 |
| parity_stability | 5.0 | parity not available |
| exit_intelligence_stability | 5.0 | exit_intel_completeness telemetry missing |
| feature_stability | 12.0 | avg_feature_stability(top20)=81.2 |
| signal_stability | 5.0 | insufficient per-signal samples |
| regime_stability | 5.0 | regime_timeline unavailable |
| no_anomalies_in_telemetry | 8.0 | missing_inputs=2 |

| readiness_score (0-100) | recommendation |
| --- | --- |
| 60.0 | investigate |


## 11. FULL RAW APPENDIX
### All shadow events (raw, from `logs/shadow_trades.jsonl` for date)
```
[]
```

### All shadow trades (cleaned)
```
[]
```

### All live trades (cleaned)
```
[
  {
    "_exit_attrib": {
      "_day": "2026-05-01",
      "_enriched_at": "2026-05-01T13:33:46.295980+00:00",
      "attribution_components": [
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_flow_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_darkpool_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_sentiment_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.00644,
          "signal_id": "exit_score_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_regime_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_sector_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_vol_expansion",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_thesis_invalidated",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_earnings_risk",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_overnight_flow_risk",
          "source": "exit"
        }
      ],
      "attribution_schema_version": "1.0.0",
      "canonical_trade_id": "BLK|LONG|1777578590",
      "composite_at_entry": 4.015,
      "composite_at_exit": 3.831,
      "composite_components_at_entry": {},
      "composite_components_at_exit": {},
      "composite_version": "v2",
      "decision_id": "dec_BLK_2026-05-01T13-33-45.8730",
      "direction": "unknown",
      "direction_intel_embed": {
        "canonical_direction_components": [
          "premarket_direction",
          "postmarket_direction",
          "overnight_direction",
          "futures_direction",
          "volatility_direction",
          "breadth_direction",
          "sector_direction",
          "etf_flow_direction",
          "macro_direction",
          "uw_direction"
        ],
        "direction_intel_components_exit": {
          "breadth_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 1.0
          },
          "etf_flow_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "futures_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "macro_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "overnight_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "postmarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "premarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "sector_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "uw_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "volatility_direction": {
            "contribution_to_direction_score": -1.0,
            "normalized_value": -1.0,
            "raw_value": "low"
          }
        },
        "intel_deltas": {
          "breadth_adv_dec_delta": 0.0,
          "futures_direction_delta": 0.001642006048054566,
          "macro_risk_entry": false,
          "macro_risk_exit": false,
          "overnight_volatility_delta": 0.0,
          "sector_strength_delta": 0.0,
          "vol_regime_entry": "mid",
          "vol_regime_exit": "low"
        },
        "intel_snapshot_entry": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "down",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": -0.001642006048054566
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": -0.001642006048054566,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": -0.16420060480545662,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": -0.0007691379622368204,
              "risk_on_off": "neutral",
              "spy_overnight_ret": -0.0025148741338723115,
              "stale_1m": true,
              "volatility_regime": "mid",
              "vxx_vxz_ratio": 0.5131745172351562
            },
            "posture": "long",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 1.0,
            "regime_label": "bull",
            "regime_source": "structural_regime:RISK_ON",
            "structural_confidence": 1.0,
            "structural_regime": "RISK_ON",
            "ts": "2026-04-30T16:11:49.674674+00:00"
          },
          "sector_intel": {
            "sector": "UNKNOWN",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-04-30T16:16:33.934410+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 34.122,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "mid"
          }
        },
        "intel_snapshot_exit": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "flat",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": 0.0
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": 0.0,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": 0.0,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": 0.0,
              "risk_on_off": "neutral",
              "spy_overnight_ret": 0.0,
              "stale_1m": true,
              "volatility_regime": "low",
              "vxx_vxz_ratio": 0.0
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-05-01T13:31:02.428661+00:00"
          },
          "sector_intel": {
            "sector": "UNKNOWN",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-05-01T13:33:46.150474+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 10.0,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "low"
          }
        }
      },
      "entry_exit_deltas": {
        "delta_composite": -0.184,
        "delta_dark_pool_notional": 0.0,
        "delta_flow_conviction": 0.0,
        "delta_gamma": 0.0,
        "delta_iv_rank": 0.0,
        "delta_regime": 1,
        "delta_sector_strength": 0,
        "delta_sentiment": 0,
        "delta_squeeze_score": 0.0,
        "delta_vol": 0.0
      },
      "entry_order_id": "UNRESOLVED_ENTRY_OID:BLK|LONG|1777578590",
      "entry_price": 1062.633333,
      "entry_regime": "unknown",
      "entry_sector_profile": {
        "sector": "UNKNOWN"
      },
      "entry_timestamp": "2026-04-30T19:49:50.793629+00:00",
      "entry_ts": "2026-04-30T19:49:50.793629+00:00",
      "entry_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "exit_components_granular": {
        "exit_dark_pool_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_flow_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_gamma_collapse": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_insider_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_microstructure_noise": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_regime_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_score_deterioration": {
          "contribution_to_exit_score": 0.00644,
          "normalized_value": 0.023,
          "raw_value": 0.023
        },
        "exit_sector_rotation": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_sentiment_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_time_decay": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_volatility_spike": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        }
      },
      "exit_order_id": "110ba80c-8cb4-468a-bf57-bca505662fc8",
      "exit_price": 1067.25,
      "exit_quality_metrics": {
        "exit_efficiency": {
          "left_money": false,
          "saved_loss": true
        },
        "mae": null,
        "mfe": 4.366667,
        "post_exit_excursion": null,
        "profit_giveback": 0.0,
        "realized_pnl_price": 4.616667,
        "time_in_trade_sec": 63835.08
      },
      "exit_reason": "stale_alpha_cutoff(1059min,0.00%)",
      "exit_reason_code": "hold",
      "exit_regime": "NEUTRAL",
      "exit_regime_context": {},
      "exit_regime_decision": "normal",
      "exit_regime_reason": "",
      "exit_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      },
      "exit_ts": "2026-05-01T13:33:45.873049+00:00",
      "exit_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "fees_usd": 0.0,
      "mode": "UNKNOWN",
      "order_id": "110ba80c-8cb4-468a-bf57-bca505662fc8",
      "pnl": 4.62,
      "pnl_pct": 0.434455,
      "position_side": "long",
      "qty": 1.0,
      "regime_label": "NEUTRAL",
      "relative_strength_deterioration": 0.0,
      "replacement_candidate": null,
      "replacement_reasoning": null,
      "score_deterioration": 0.18399999999999972,
      "side": "buy",
      "strategy": "UNKNOWN",
      "symbol": "BLK",
      "time_in_trade_minutes": 1063.9179903333334,
      "timestamp": "2026-05-01T13:33:45.873049+00:00",
      "trade_id": "open_BLK_2026-04-30T19:49:50.793629+00:00",
      "trade_key": "BLK|LONG|1777578590",
      "v2_exit_components": {
        "darkpool_deterioration": 0.0,
        "earnings_risk": 0.0,
        "flow_deterioration": 0.0,
        "overnight_flow_risk": 0.0,
        "regime_shift": 0.0,
        "score_deterioration": 0.023,
        "sector_shift": 0.0,
        "sentiment_deterioration": 0.0,
        "thesis_invalidated": 0.0,
        "vol_expansion": 0.0
      },
      "v2_exit_score": 0.006439999999999991,
      "variant_id": "B2_live_paper"
    },
    "composite_at_entry": 4.015,
    "composite_at_exit": 3.831,
    "composite_version": "v2",
    "entry_day": "2026-04-30",
    "entry_exit_deltas": {
      "delta_composite": -0.184,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 0,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_price": 1062.633333,
    "entry_ts": "2026-04-30T19:49:50.793629+00:00",
    "entry_v2_score": 4.015,
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.00644,
        "normalized_value": 0.023,
        "raw_value": 0.023
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_day": "2026-05-01",
    "exit_price": 1067.25,
    "exit_reason": "stale_alpha_cutoff(1059min,0.00%)",
    "exit_ts": "2026-05-01T13:33:45.873049+00:00",
    "exit_v2_score": 3.831,
    "feature_snapshot": {},
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": 4.616667000000007,
    "qty": 1.0,
    "realized_pnl_usd": 4.616667000000007,
    "regime": "NEUTRAL",
    "regime_snapshot": {
      "regime": "NEUTRAL"
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [],
    "size": 1.0,
    "source": "live",
    "symbol": "BLK",
    "time_in_trade_minutes": 1063.9179903333334,
    "timestamp": "2026-05-01T13:33:46.295636+00:00",
    "trade_id": "live:BLK:2026-04-30T19:49:50.793629+00:00",
    "unrealized_pnl_usd": null,
    "v2_exit_reason": "hold",
    "v2_exit_score": 0.006439999999999991
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 264.83,
    "entry_ts": "2026-05-01T13:34:23.162497+00:00",
    "entry_v2_score": 3.812,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.12,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.21,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.943,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.12,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.21,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.812,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 1.600063,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.268373,
        "spy_overnight_ret": 0.0,
        "trade_count": 109,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.1,
          "earnings_weight": 1.0,
          "flow_weight": 1.2,
          "short_interest_weight": 0.8
        },
        "sector": "TECH",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "AMZN",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:34:23.164770+00:00",
    "trade_id": "live:AMZN:2026-05-01T13:34:23.162497+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.812
  },
  {
    "_exit_attrib": {
      "_day": "2026-05-01",
      "_enriched_at": "2026-05-01T13:34:34.303625+00:00",
      "attribution_components": null,
      "attribution_schema_version": "1.0.0",
      "canonical_trade_id": "JPM|LONG|1777578869",
      "composite_at_entry": 3.96,
      "composite_at_exit": 0.0,
      "composite_components_at_entry": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.986,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.12,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.061,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "composite_components_at_exit": {},
      "composite_version": "v2",
      "decision_id": "dec_JPM_2026-05-01T13-34-34.1834",
      "direction": "bullish",
      "direction_intel_embed": {
        "canonical_direction_components": [
          "premarket_direction",
          "postmarket_direction",
          "overnight_direction",
          "futures_direction",
          "volatility_direction",
          "breadth_direction",
          "sector_direction",
          "etf_flow_direction",
          "macro_direction",
          "uw_direction"
        ],
        "direction_intel_components_exit": {
          "breadth_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 1.0
          },
          "etf_flow_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "futures_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "macro_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "overnight_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "postmarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "premarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "sector_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "uw_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "volatility_direction": {
            "contribution_to_direction_score": -1.0,
            "normalized_value": -1.0,
            "raw_value": "low"
          }
        },
        "intel_deltas": {
          "breadth_adv_dec_delta": 0.0,
          "futures_direction_delta": 0.008942063866983794,
          "macro_risk_entry": false,
          "macro_risk_exit": false,
          "overnight_volatility_delta": 0.0,
          "sector_strength_delta": 0.0,
          "vol_regime_entry": "mid",
          "vol_regime_exit": "low"
        },
        "intel_snapshot_entry": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "down",
            "NQ_direction": "down",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": -0.008942063866983794
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": -0.008942063866983794,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": -0.8942063866983794,
            "premarket_sentiment": "bearish",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "down",
              "qqq_overnight_ret": -0.008766811782834253,
              "risk_on_off": "neutral",
              "spy_overnight_ret": -0.009117315951133334,
              "stale_1m": true,
              "volatility_regime": "mid",
              "vxx_vxz_ratio": 0.5107985480943739
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-04-30T19:50:20.280442+00:00"
          },
          "sector_intel": {
            "sector": "FINANCIALS",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-04-30T19:54:29.604931+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 33.774,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "mid"
          }
        },
        "intel_snapshot_exit": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "flat",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": 0.0
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": 0.0,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": 0.0,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": 0.0,
              "risk_on_off": "neutral",
              "spy_overnight_ret": 0.0,
              "stale_1m": true,
              "volatility_regime": "low",
              "vxx_vxz_ratio": 0.0
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-05-01T13:31:02.428661+00:00"
          },
          "sector_intel": {
            "sector": "FINANCIALS",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-05-01T13:34:34.184250+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 10.0,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "low"
          }
        }
      },
      "entry_exit_deltas": {
        "delta_composite": -3.96,
        "delta_dark_pool_notional": 0.0,
        "delta_flow_conviction": -1.0,
        "delta_gamma": 0.0,
        "delta_iv_rank": 0.0,
        "delta_regime": 1,
        "delta_sector_strength": 1,
        "delta_sentiment": 1,
        "delta_squeeze_score": 0.0,
        "delta_vol": 0.0
      },
      "entry_order_id": "a31f1b51-5ed9-4abe-a627-8ee863ded8d4",
      "entry_price": 313.53,
      "entry_regime": "NEUTRAL",
      "entry_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 0.9,
          "flow_weight": 1.0,
          "short_interest_weight": 0.9
        },
        "sector": "FINANCIALS",
        "version": "2026-01-20_sector_profiles_v1"
      },
      "entry_timestamp": "2026-04-30T19:54:29.015419+00:00",
      "entry_ts": "2026-04-30T19:54:29.015419+00:00",
      "entry_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "exit_components_granular": {
        "exit_dark_pool_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_flow_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_gamma_collapse": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_insider_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_microstructure_noise": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_regime_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_score_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_sector_rotation": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_sentiment_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_time_decay": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_volatility_spike": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        }
      },
      "exit_order_id": "28490a4e-c381-4aad-a181-3e0cba72fc88",
      "exit_price": 312.9,
      "exit_quality_metrics": {
        "exit_efficiency": {
          "left_money": false,
          "saved_loss": false
        },
        "mae": null,
        "mfe": 0.0,
        "post_exit_excursion": null,
        "profit_giveback": null,
        "realized_pnl_price": -0.63,
        "time_in_trade_sec": 63605.17
      },
      "exit_reason": "underwater_time_decay_stop",
      "exit_reason_code": "other",
      "exit_regime": "mixed",
      "exit_regime_context": {
        "max_minutes": 60.0,
        "pnl_pct": -0.00041
      },
      "exit_regime_decision": "normal",
      "exit_regime_reason": "underwater_time_decay_stop",
      "exit_sector_profile": {
        "sector": "UNKNOWN"
      },
      "exit_ts": "2026-05-01T13:34:34.183410+00:00",
      "exit_uw": {},
      "fees_usd": 0.0,
      "mode": "UNKNOWN",
      "order_id": "28490a4e-c381-4aad-a181-3e0cba72fc88",
      "pnl": -0.63,
      "pnl_pct": -0.200938,
      "position_side": "long",
      "qty": 1.0,
      "regime_label": "MIXED",
      "relative_strength_deterioration": 0.0,
      "replacement_candidate": null,
      "replacement_reasoning": null,
      "score_deterioration": 0.0,
      "side": "buy",
      "strategy": "UNKNOWN",
      "symbol": "JPM",
      "time_in_trade_minutes": 1060.0861331833335,
      "timestamp": "2026-05-01T13:34:34.183410+00:00",
      "trade_id": "open_JPM_2026-04-30T19:54:29.015419+00:00",
      "trade_key": "JPM|LONG|1777578869",
      "v2_exit_components": {},
      "v2_exit_score": 0.0,
      "variant_id": "paper_aggressive"
    },
    "composite_at_entry": 3.96,
    "composite_at_exit": 0.0,
    "composite_version": "v2",
    "entry_day": "2026-04-30",
    "entry_exit_deltas": {
      "delta_composite": -3.96,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_price": 313.53,
    "entry_ts": "2026-04-30T19:54:29.015419+00:00",
    "entry_v2_score": 3.96,
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_day": "2026-05-01",
    "exit_price": 312.9,
    "exit_reason": "underwater_time_decay_stop",
    "exit_ts": "2026-05-01T13:34:34.183410+00:00",
    "exit_v2_score": 0.0,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.986,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.12,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.061,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": -0.6299999999999955,
    "qty": 1.0,
    "realized_pnl_usd": -0.6299999999999955,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed"
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "JPM",
    "time_in_trade_minutes": 1060.0861331833335,
    "timestamp": "2026-05-01T13:34:34.303428+00:00",
    "trade_id": "live:JPM:2026-04-30T19:54:29.015419+00:00",
    "unrealized_pnl_usd": null,
    "v2_exit_reason": "",
    "v2_exit_score": 0.0
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 897.88,
    "entry_ts": "2026-05-01T13:34:41.027446+00:00",
    "entry_v2_score": 3.783,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.06,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": -0.06,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.061,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.943,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.06,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": -0.06,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.061,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.783,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 1.950185,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.369936,
        "spy_overnight_ret": 0.0,
        "trade_count": 102,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "CAT",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:34:41.029397+00:00",
    "trade_id": "live:CAT:2026-05-01T13:34:41.027446+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.783
  },
  {
    "_exit_attrib": {
      "_day": "2026-05-01",
      "_enriched_at": "2026-05-01T13:35:05.230816+00:00",
      "attribution_components": null,
      "attribution_schema_version": "1.0.0",
      "canonical_trade_id": "TGT|LONG|1777578979",
      "composite_at_entry": 3.929,
      "composite_at_exit": 0.0,
      "composite_components_at_entry": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.971,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.12,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.021,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "composite_components_at_exit": {},
      "composite_version": "v2",
      "decision_id": "dec_TGT_2026-05-01T13-35-05.0947",
      "direction": "bullish",
      "direction_intel_embed": {
        "canonical_direction_components": [
          "premarket_direction",
          "postmarket_direction",
          "overnight_direction",
          "futures_direction",
          "volatility_direction",
          "breadth_direction",
          "sector_direction",
          "etf_flow_direction",
          "macro_direction",
          "uw_direction"
        ],
        "direction_intel_components_exit": {
          "breadth_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 1.0
          },
          "etf_flow_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "futures_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "macro_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "overnight_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "postmarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "premarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "sector_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "uw_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "volatility_direction": {
            "contribution_to_direction_score": -1.0,
            "normalized_value": -1.0,
            "raw_value": "low"
          }
        },
        "intel_deltas": {
          "breadth_adv_dec_delta": 0.0,
          "futures_direction_delta": 0.008942063866983794,
          "macro_risk_entry": false,
          "macro_risk_exit": false,
          "overnight_volatility_delta": 0.0,
          "sector_strength_delta": 0.0,
          "vol_regime_entry": "mid",
          "vol_regime_exit": "low"
        },
        "intel_snapshot_entry": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "down",
            "NQ_direction": "down",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": -0.008942063866983794
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": -0.008942063866983794,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": -0.8942063866983794,
            "premarket_sentiment": "bearish",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "down",
              "qqq_overnight_ret": -0.008766811782834253,
              "risk_on_off": "neutral",
              "spy_overnight_ret": -0.009117315951133334,
              "stale_1m": true,
              "volatility_regime": "mid",
              "vxx_vxz_ratio": 0.5107985480943739
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-04-30T19:50:20.280442+00:00"
          },
          "sector_intel": {
            "sector": "UNKNOWN",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-04-30T19:56:21.503934+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 33.774,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "mid"
          }
        },
        "intel_snapshot_exit": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "flat",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": 0.0
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": 0.0,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": 0.0,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": 0.0,
              "risk_on_off": "neutral",
              "spy_overnight_ret": 0.0,
              "stale_1m": true,
              "volatility_regime": "low",
              "vxx_vxz_ratio": 0.0
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-05-01T13:31:02.428661+00:00"
          },
          "sector_intel": {
            "sector": "UNKNOWN",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-05-01T13:35:05.095647+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 10.0,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "low"
          }
        }
      },
      "entry_exit_deltas": {
        "delta_composite": -3.929,
        "delta_dark_pool_notional": 0.0,
        "delta_flow_conviction": -1.0,
        "delta_gamma": 0.0,
        "delta_iv_rank": 0.0,
        "delta_regime": 1,
        "delta_sector_strength": 0,
        "delta_sentiment": 1,
        "delta_squeeze_score": 0.0,
        "delta_vol": 0.0
      },
      "entry_order_id": "dc2731bd-e462-418a-a95c-a08514beb205",
      "entry_price": 129.48,
      "entry_regime": "NEUTRAL",
      "entry_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      },
      "entry_timestamp": "2026-04-30T19:56:19.608582+00:00",
      "entry_ts": "2026-04-30T19:56:19.608582+00:00",
      "entry_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "exit_components_granular": {
        "exit_dark_pool_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_flow_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_gamma_collapse": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_insider_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_microstructure_noise": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_regime_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_score_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_sector_rotation": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_sentiment_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_time_decay": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_volatility_spike": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        }
      },
      "exit_order_id": "7f29828a-15d5-4a99-9ff5-ad7cc9910b8e",
      "exit_price": 129.57,
      "exit_quality_metrics": {
        "exit_efficiency": {
          "left_money": false,
          "saved_loss": true
        },
        "mae": null,
        "mfe": 0.0,
        "post_exit_excursion": null,
        "profit_giveback": null,
        "realized_pnl_price": 0.09,
        "time_in_trade_sec": 63525.49
      },
      "exit_reason": "underwater_time_decay_stop",
      "exit_reason_code": "other",
      "exit_regime": "mixed",
      "exit_regime_context": {
        "max_minutes": 60.0,
        "pnl_pct": -0.00278
      },
      "exit_regime_decision": "normal",
      "exit_regime_reason": "underwater_time_decay_stop",
      "exit_sector_profile": {
        "sector": "UNKNOWN"
      },
      "exit_ts": "2026-05-01T13:35:05.094777+00:00",
      "exit_uw": {},
      "fees_usd": 0.0,
      "mode": "UNKNOWN",
      "order_id": "7f29828a-15d5-4a99-9ff5-ad7cc9910b8e",
      "pnl": 0.27,
      "pnl_pct": 0.069509,
      "position_side": "long",
      "qty": 3.0,
      "regime_label": "MIXED",
      "relative_strength_deterioration": 0.0,
      "replacement_candidate": null,
      "replacement_reasoning": null,
      "score_deterioration": 0.0,
      "side": "buy",
      "strategy": "UNKNOWN",
      "symbol": "TGT",
      "time_in_trade_minutes": 1058.75810325,
      "timestamp": "2026-05-01T13:35:05.094777+00:00",
      "trade_id": "open_TGT_2026-04-30T19:56:19.608582+00:00",
      "trade_key": "TGT|LONG|1777578979",
      "v2_exit_components": {},
      "v2_exit_score": 0.0,
      "variant_id": "paper_aggressive"
    },
    "composite_at_entry": 3.929,
    "composite_at_exit": 0.0,
    "composite_version": "v2",
    "entry_day": "2026-04-30",
    "entry_exit_deltas": {
      "delta_composite": -3.929,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 0,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_price": 129.48,
    "entry_ts": "2026-04-30T19:56:19.608582+00:00",
    "entry_v2_score": 3.929,
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_day": "2026-05-01",
    "exit_price": 129.57,
    "exit_reason": "underwater_time_decay_stop",
    "exit_ts": "2026-05-01T13:35:05.094777+00:00",
    "exit_v2_score": 0.0,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.971,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.12,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.021,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": 0.27000000000001023,
    "qty": 3.0,
    "realized_pnl_usd": 0.27000000000001023,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed"
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 3.0,
    "source": "live",
    "symbol": "TGT",
    "time_in_trade_minutes": 1058.75810325,
    "timestamp": "2026-05-01T13:35:05.230616+00:00",
    "trade_id": "live:TGT:2026-04-30T19:56:19.608582+00:00",
    "unrealized_pnl_usd": null,
    "v2_exit_reason": "",
    "v2_exit_score": 0.0
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 53.6175,
    "entry_ts": "2026-05-01T13:35:06.378757+00:00",
    "entry_v2_score": 3.691,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.12,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.06,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.119,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.943,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.12,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.06,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.119,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.691,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 1.289655,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.287443,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 0.9,
          "flow_weight": 1.0,
          "short_interest_weight": 0.9
        },
        "sector": "FINANCIALS",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 4.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 4.0,
    "source": "live",
    "symbol": "BAC",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:35:06.380636+00:00",
    "trade_id": "live:BAC:2026-05-01T13:35:06.378757+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.691
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 153.4,
    "entry_ts": "2026-05-01T13:35:24.660712+00:00",
    "entry_v2_score": 3.679,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.942,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.12,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": -0.12,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.061,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.942,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.12,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": -0.12,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.061,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.679,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 0.063857,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.2839,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 0.9,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "ENERGY",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "XOM",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:35:24.662693+00:00",
    "trade_id": "live:XOM:2026-05-01T13:35:24.660712+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.679
  },
  {
    "_exit_attrib": {
      "_day": "2026-05-01",
      "_enriched_at": "2026-05-01T13:35:35.965657+00:00",
      "attribution_components": [
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_flow_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_darkpool_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_sentiment_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.033376,
          "signal_id": "exit_score_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_regime_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.05,
          "signal_id": "exit_sector_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_vol_expansion",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_thesis_invalidated",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_earnings_risk",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_overnight_flow_risk",
          "source": "exit"
        }
      ],
      "attribution_schema_version": "1.0.0",
      "canonical_trade_id": "TSLA|LONG|1777579245",
      "composite_at_entry": 5.028,
      "composite_at_exit": 4.074,
      "composite_components_at_entry": {},
      "composite_components_at_exit": {},
      "composite_version": "v2",
      "decision_id": "dec_TSLA_2026-05-01T13-35-35.5766",
      "direction": "unknown",
      "direction_intel_embed": {
        "canonical_direction_components": [
          "premarket_direction",
          "postmarket_direction",
          "overnight_direction",
          "futures_direction",
          "volatility_direction",
          "breadth_direction",
          "sector_direction",
          "etf_flow_direction",
          "macro_direction",
          "uw_direction"
        ],
        "direction_intel_components_exit": {
          "breadth_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 1.0
          },
          "etf_flow_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "futures_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "macro_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "overnight_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "postmarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "premarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "sector_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "uw_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "volatility_direction": {
            "contribution_to_direction_score": -1.0,
            "normalized_value": -1.0,
            "raw_value": "low"
          }
        },
        "intel_deltas": {
          "breadth_adv_dec_delta": 0.0,
          "futures_direction_delta": 0.001642006048054566,
          "macro_risk_entry": false,
          "macro_risk_exit": false,
          "overnight_volatility_delta": 0.0,
          "sector_strength_delta": 0.0,
          "vol_regime_entry": "mid",
          "vol_regime_exit": "low"
        },
        "intel_snapshot_entry": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "down",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": -0.001642006048054566
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": -0.001642006048054566,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": -0.16420060480545662,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": -0.0007691379622368204,
              "risk_on_off": "neutral",
              "spy_overnight_ret": -0.0025148741338723115,
              "stale_1m": true,
              "volatility_regime": "mid",
              "vxx_vxz_ratio": 0.5131745172351562
            },
            "posture": "long",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 1.0,
            "regime_label": "bull",
            "regime_source": "structural_regime:RISK_ON",
            "structural_confidence": 1.0,
            "structural_regime": "RISK_ON",
            "ts": "2026-04-30T16:11:49.674674+00:00"
          },
          "sector_intel": {
            "sector": "TECH",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-04-30T16:12:24.155771+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 34.122,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "mid"
          }
        },
        "intel_snapshot_exit": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "flat",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": 0.0
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": 0.0,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": 0.0,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": 0.0,
              "risk_on_off": "neutral",
              "spy_overnight_ret": 0.0,
              "stale_1m": true,
              "volatility_regime": "low",
              "vxx_vxz_ratio": 0.0
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-05-01T13:31:02.428661+00:00"
          },
          "sector_intel": {
            "sector": "TECH",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-05-01T13:35:35.831940+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 10.0,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "low"
          }
        }
      },
      "entry_exit_deltas": {
        "delta_composite": -0.954,
        "delta_dark_pool_notional": 0.0,
        "delta_flow_conviction": 0.0,
        "delta_gamma": 0.0,
        "delta_iv_rank": 0.0,
        "delta_regime": 1,
        "delta_sector_strength": 1,
        "delta_sentiment": 0,
        "delta_squeeze_score": 0.0,
        "delta_vol": 0.0
      },
      "entry_order_id": "UNRESOLVED_ENTRY_OID:TSLA|LONG|1777579245",
      "entry_price": 381.68,
      "entry_regime": "unknown",
      "entry_sector_profile": {
        "sector": "UNKNOWN"
      },
      "entry_timestamp": "2026-04-30T20:00:45.829762+00:00",
      "entry_ts": "2026-04-30T20:00:45.829762+00:00",
      "entry_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "exit_components_granular": {
        "exit_dark_pool_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_flow_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_gamma_collapse": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_insider_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_microstructure_noise": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_regime_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_score_deterioration": {
          "contribution_to_exit_score": 0.033376,
          "normalized_value": 0.1192,
          "raw_value": 0.1192
        },
        "exit_sector_rotation": {
          "contribution_to_exit_score": 0.05,
          "normalized_value": 1.0,
          "raw_value": 1.0
        },
        "exit_sentiment_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_time_decay": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_volatility_spike": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        }
      },
      "exit_order_id": "1d32238d-bf1f-480f-af73-a5bc5dc0743a",
      "exit_price": 382.45,
      "exit_quality_metrics": {
        "exit_efficiency": {
          "left_money": false,
          "saved_loss": true
        },
        "mae": null,
        "mfe": 1.08,
        "post_exit_excursion": null,
        "profit_giveback": 0.287037,
        "realized_pnl_price": 0.77,
        "time_in_trade_sec": 63289.75
      },
      "exit_reason": "stale_alpha_cutoff(1048min,0.00%)",
      "exit_reason_code": "hold",
      "exit_regime": "NEUTRAL",
      "exit_regime_context": {},
      "exit_regime_decision": "normal",
      "exit_regime_reason": "",
      "exit_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.1,
          "earnings_weight": 1.0,
          "flow_weight": 1.2,
          "short_interest_weight": 0.8
        },
        "sector": "TECH",
        "version": "2026-01-20_sector_profiles_v1"
      },
      "exit_ts": "2026-05-01T13:35:35.576616+00:00",
      "exit_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "fees_usd": 0.0,
      "mode": "UNKNOWN",
      "order_id": "1d32238d-bf1f-480f-af73-a5bc5dc0743a",
      "pnl": 0.77,
      "pnl_pct": 0.20174,
      "position_side": "long",
      "qty": 1.0,
      "regime_label": "NEUTRAL",
      "relative_strength_deterioration": 0.0,
      "replacement_candidate": null,
      "replacement_reasoning": null,
      "score_deterioration": 0.9539999999999997,
      "side": "buy",
      "strategy": "UNKNOWN",
      "symbol": "TSLA",
      "time_in_trade_minutes": 1054.8291142333333,
      "timestamp": "2026-05-01T13:35:35.576616+00:00",
      "trade_id": "open_TSLA_2026-04-30T20:00:45.829762+00:00",
      "trade_key": "TSLA|LONG|1777579245",
      "v2_exit_components": {
        "darkpool_deterioration": 0.0,
        "earnings_risk": 0.0,
        "flow_deterioration": 0.0,
        "overnight_flow_risk": 0.0,
        "regime_shift": 0.0,
        "score_deterioration": 0.1192,
        "sector_shift": 1.0,
        "sentiment_deterioration": 0.0,
        "thesis_invalidated": 0.0,
        "vol_expansion": 0.0
      },
      "v2_exit_score": 0.08338999999999999,
      "variant_id": "B2_live_paper"
    },
    "composite_at_entry": 5.028,
    "composite_at_exit": 4.074,
    "composite_version": "v2",
    "entry_day": "2026-04-30",
    "entry_exit_deltas": {
      "delta_composite": -0.954,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_price": 381.68,
    "entry_ts": "2026-04-30T20:00:45.829762+00:00",
    "entry_v2_score": 5.028,
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.033376,
        "normalized_value": 0.1192,
        "raw_value": 0.1192
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.05,
        "normalized_value": 1.0,
        "raw_value": 1.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_day": "2026-05-01",
    "exit_price": 382.45,
    "exit_reason": "stale_alpha_cutoff(1048min,0.00%)",
    "exit_ts": "2026-05-01T13:35:35.576616+00:00",
    "exit_v2_score": 4.074,
    "feature_snapshot": {},
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": 0.7699999999999818,
    "qty": 1.0,
    "realized_pnl_usd": 0.7699999999999818,
    "regime": "NEUTRAL",
    "regime_snapshot": {
      "regime": "NEUTRAL"
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [],
    "size": 1.0,
    "source": "live",
    "symbol": "TSLA",
    "time_in_trade_minutes": 1054.8291142333333,
    "timestamp": "2026-05-01T13:35:35.965483+00:00",
    "trade_id": "live:TSLA:2026-04-30T20:00:45.829762+00:00",
    "unrealized_pnl_usd": null,
    "v2_exit_reason": "hold",
    "v2_exit_score": 0.08338999999999999
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 671.64,
    "entry_ts": "2026-05-01T13:35:37.930120+00:00",
    "entry_v2_score": 3.663,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.943,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.0,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.042,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.663,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 1.370577,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.164755,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.1,
          "earnings_weight": 1.0,
          "flow_weight": 1.2,
          "short_interest_weight": 0.8
        },
        "sector": "TECH",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "QQQ",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:35:37.932467+00:00",
    "trade_id": "live:QQQ:2026-05-01T13:35:37.930120+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.663
  },
  {
    "_exit_attrib": {
      "_day": "2026-05-01",
      "_enriched_at": "2026-05-01T13:36:08.109291+00:00",
      "attribution_components": [
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_flow_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_darkpool_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_sentiment_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.01274,
          "signal_id": "exit_score_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_regime_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.05,
          "signal_id": "exit_sector_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.02591,
          "signal_id": "exit_vol_expansion",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_thesis_invalidated",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_earnings_risk",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_overnight_flow_risk",
          "source": "exit"
        }
      ],
      "attribution_schema_version": "1.0.0",
      "canonical_trade_id": "MS|LONG|1777579245",
      "composite_at_entry": 4.354,
      "composite_at_exit": 3.99,
      "composite_components_at_entry": {},
      "composite_components_at_exit": {},
      "composite_version": "v2",
      "decision_id": "dec_MS_2026-05-01T13-36-07.7576",
      "direction": "unknown",
      "direction_intel_embed": {
        "canonical_direction_components": [
          "premarket_direction",
          "postmarket_direction",
          "overnight_direction",
          "futures_direction",
          "volatility_direction",
          "breadth_direction",
          "sector_direction",
          "etf_flow_direction",
          "macro_direction",
          "uw_direction"
        ],
        "direction_intel_components_exit": {
          "breadth_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 1.0
          },
          "etf_flow_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "futures_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "macro_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "overnight_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "postmarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "premarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "sector_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "uw_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "volatility_direction": {
            "contribution_to_direction_score": -1.0,
            "normalized_value": -1.0,
            "raw_value": "low"
          }
        },
        "intel_deltas": {
          "breadth_adv_dec_delta": 0.0,
          "futures_direction_delta": 0.001642006048054566,
          "macro_risk_entry": false,
          "macro_risk_exit": false,
          "overnight_volatility_delta": 0.0,
          "sector_strength_delta": 0.0,
          "vol_regime_entry": "mid",
          "vol_regime_exit": "low"
        },
        "intel_snapshot_entry": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "down",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": -0.001642006048054566
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": -0.001642006048054566,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": -0.16420060480545662,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": -0.0007691379622368204,
              "risk_on_off": "neutral",
              "spy_overnight_ret": -0.0025148741338723115,
              "stale_1m": true,
              "volatility_regime": "mid",
              "vxx_vxz_ratio": 0.5131745172351562
            },
            "posture": "long",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 1.0,
            "regime_label": "bull",
            "regime_source": "structural_regime:RISK_ON",
            "structural_confidence": 1.0,
            "structural_regime": "RISK_ON",
            "ts": "2026-04-30T16:11:49.674674+00:00"
          },
          "sector_intel": {
            "sector": "FINANCIALS",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-04-30T16:13:51.218308+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 34.122,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "mid"
          }
        },
        "intel_snapshot_exit": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "flat",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": 0.0
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": 0.0,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": 0.0,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": 0.0,
              "risk_on_off": "neutral",
              "spy_overnight_ret": 0.0,
              "stale_1m": true,
              "volatility_regime": "low",
              "vxx_vxz_ratio": 0.0
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-05-01T13:31:02.428661+00:00"
          },
          "sector_intel": {
            "sector": "FINANCIALS",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-05-01T13:36:07.983984+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 10.0,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "low"
          }
        }
      },
      "entry_exit_deltas": {
        "delta_composite": -0.364,
        "delta_dark_pool_notional": 0.0,
        "delta_flow_conviction": 0.0,
        "delta_gamma": 0.0,
        "delta_iv_rank": 0.0,
        "delta_regime": 1,
        "delta_sector_strength": 1,
        "delta_sentiment": 0,
        "delta_squeeze_score": 0.0,
        "delta_vol": 0.0
      },
      "entry_order_id": "UNRESOLVED_ENTRY_OID:MS|LONG|1777579245",
      "entry_price": 189.838,
      "entry_regime": "unknown",
      "entry_sector_profile": {
        "sector": "UNKNOWN"
      },
      "entry_timestamp": "2026-04-30T20:00:45.830826+00:00",
      "entry_ts": "2026-04-30T20:00:45.830826+00:00",
      "entry_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "exit_components_granular": {
        "exit_dark_pool_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_flow_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_gamma_collapse": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_insider_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_microstructure_noise": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_regime_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_score_deterioration": {
          "contribution_to_exit_score": 0.01274,
          "normalized_value": 0.0455,
          "raw_value": 0.0455
        },
        "exit_sector_rotation": {
          "contribution_to_exit_score": 0.05,
          "normalized_value": 1.0,
          "raw_value": 1.0
        },
        "exit_sentiment_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_time_decay": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_volatility_spike": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.05182,
          "raw_value": 0.0
        }
      },
      "exit_order_id": "f5a3c47b-9355-4cd0-8f91-d9c27f123c96",
      "exit_price": 190.39,
      "exit_quality_metrics": {
        "exit_efficiency": {
          "left_money": false,
          "saved_loss": true
        },
        "mae": null,
        "mfe": 0.572,
        "post_exit_excursion": null,
        "profit_giveback": 0.034965,
        "realized_pnl_price": 0.552,
        "time_in_trade_sec": 63321.93
      },
      "exit_reason": "stale_alpha_cutoff(1048min,0.00%)",
      "exit_reason_code": "hold",
      "exit_regime": "NEUTRAL",
      "exit_regime_context": {},
      "exit_regime_decision": "normal",
      "exit_regime_reason": "",
      "exit_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 0.9,
          "flow_weight": 1.0,
          "short_interest_weight": 0.9
        },
        "sector": "FINANCIALS",
        "version": "2026-01-20_sector_profiles_v1"
      },
      "exit_ts": "2026-05-01T13:36:07.757632+00:00",
      "exit_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "fees_usd": 0.0,
      "mode": "UNKNOWN",
      "order_id": "f5a3c47b-9355-4cd0-8f91-d9c27f123c96",
      "pnl": 0.55,
      "pnl_pct": 0.290774,
      "position_side": "long",
      "qty": 1.0,
      "regime_label": "NEUTRAL",
      "relative_strength_deterioration": 0.0,
      "replacement_candidate": null,
      "replacement_reasoning": null,
      "score_deterioration": 0.3639999999999999,
      "side": "buy",
      "strategy": "UNKNOWN",
      "symbol": "MS",
      "time_in_trade_minutes": 1055.3654467666668,
      "timestamp": "2026-05-01T13:36:07.757632+00:00",
      "trade_id": "open_MS_2026-04-30T20:00:45.830826+00:00",
      "trade_key": "MS|LONG|1777579245",
      "v2_exit_components": {
        "darkpool_deterioration": 0.0,
        "earnings_risk": 0.0,
        "flow_deterioration": 0.0,
        "overnight_flow_risk": 0.0,
        "regime_shift": 0.0,
        "score_deterioration": 0.0455,
        "sector_shift": 1.0,
        "sentiment_deterioration": 0.0,
        "thesis_invalidated": 0.0,
        "vol_expansion": 0.2591
      },
      "v2_exit_score": 0.08864720000000002,
      "variant_id": "B2_live_paper"
    },
    "composite_at_entry": 4.354,
    "composite_at_exit": 3.99,
    "composite_version": "v2",
    "entry_day": "2026-04-30",
    "entry_exit_deltas": {
      "delta_composite": -0.364,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_price": 189.838,
    "entry_ts": "2026-04-30T20:00:45.830826+00:00",
    "entry_v2_score": 4.354,
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.01274,
        "normalized_value": 0.0455,
        "raw_value": 0.0455
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.05,
        "normalized_value": 1.0,
        "raw_value": 1.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.05182,
        "raw_value": 0.0
      }
    },
    "exit_day": "2026-05-01",
    "exit_price": 190.39,
    "exit_reason": "stale_alpha_cutoff(1048min,0.00%)",
    "exit_ts": "2026-05-01T13:36:07.757632+00:00",
    "exit_v2_score": 3.99,
    "feature_snapshot": {},
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": 0.5519999999999925,
    "qty": 1.0,
    "realized_pnl_usd": 0.5519999999999925,
    "regime": "NEUTRAL",
    "regime_snapshot": {
      "regime": "NEUTRAL"
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [],
    "size": 1.0,
    "source": "live",
    "symbol": "MS",
    "time_in_trade_minutes": 1055.3654467666668,
    "timestamp": "2026-05-01T13:36:08.109088+00:00",
    "trade_id": "live:MS:2026-04-30T20:00:45.830826+00:00",
    "unrealized_pnl_usd": null,
    "v2_exit_reason": "hold",
    "v2_exit_score": 0.08864720000000002
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 328.73,
    "entry_ts": "2026-05-01T13:36:18.486550+00:00",
    "entry_v2_score": 3.581,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.943,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.0,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.042,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.581,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 0.191316,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.224885,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "HD",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:36:18.488492+00:00",
    "trade_id": "live:HD:2026-05-01T13:36:18.486550+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.581
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 1020.08,
    "entry_ts": "2026-05-01T13:36:36.661461+00:00",
    "entry_v2_score": 3.577,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.943,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.0,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.042,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.577,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": -0.416261,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.223233,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "COST",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:36:36.663453+00:00",
    "trade_id": "live:COST:2026-05-01T13:36:36.661461+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.577
  },
  {
    "_exit_attrib": {
      "_day": "2026-05-01",
      "_enriched_at": "2026-05-01T13:36:38.041215+00:00",
      "attribution_components": [
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_flow_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_darkpool_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_sentiment_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.01302,
          "signal_id": "exit_score_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_regime_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.05,
          "signal_id": "exit_sector_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.04114,
          "signal_id": "exit_vol_expansion",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_thesis_invalidated",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_earnings_risk",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_overnight_flow_risk",
          "source": "exit"
        }
      ],
      "attribution_schema_version": "1.0.0",
      "canonical_trade_id": "PLTR|LONG|1777579245",
      "composite_at_entry": 4.508,
      "composite_at_exit": 4.136,
      "composite_components_at_entry": {},
      "composite_components_at_exit": {},
      "composite_version": "v2",
      "decision_id": "dec_PLTR_2026-05-01T13-36-37.5280",
      "direction": "unknown",
      "direction_intel_embed": {
        "canonical_direction_components": [
          "premarket_direction",
          "postmarket_direction",
          "overnight_direction",
          "futures_direction",
          "volatility_direction",
          "breadth_direction",
          "sector_direction",
          "etf_flow_direction",
          "macro_direction",
          "uw_direction"
        ],
        "direction_intel_components_exit": {
          "breadth_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 1.0
          },
          "etf_flow_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "futures_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "macro_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "overnight_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "postmarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "premarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "sector_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "uw_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "volatility_direction": {
            "contribution_to_direction_score": -1.0,
            "normalized_value": -1.0,
            "raw_value": "low"
          }
        },
        "intel_deltas": {
          "breadth_adv_dec_delta": 0.0,
          "futures_direction_delta": 0.001642006048054566,
          "macro_risk_entry": false,
          "macro_risk_exit": false,
          "overnight_volatility_delta": 0.0,
          "sector_strength_delta": 0.0,
          "vol_regime_entry": "mid",
          "vol_regime_exit": "low"
        },
        "intel_snapshot_entry": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "down",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": -0.001642006048054566
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": -0.001642006048054566,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": -0.16420060480545662,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": -0.0007691379622368204,
              "risk_on_off": "neutral",
              "spy_overnight_ret": -0.0025148741338723115,
              "stale_1m": true,
              "volatility_regime": "mid",
              "vxx_vxz_ratio": 0.5131745172351562
            },
            "posture": "long",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 1.0,
            "regime_label": "bull",
            "regime_source": "structural_regime:RISK_ON",
            "structural_confidence": 1.0,
            "structural_regime": "RISK_ON",
            "ts": "2026-04-30T16:11:49.674674+00:00"
          },
          "sector_intel": {
            "sector": "TECH",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-04-30T16:14:06.801863+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 34.122,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "mid"
          }
        },
        "intel_snapshot_exit": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "flat",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": 0.0
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": 0.0,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": 0.0,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": 0.0,
              "risk_on_off": "neutral",
              "spy_overnight_ret": 0.0,
              "stale_1m": true,
              "volatility_regime": "low",
              "vxx_vxz_ratio": 0.0
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-05-01T13:31:02.428661+00:00"
          },
          "sector_intel": {
            "sector": "TECH",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-05-01T13:36:37.873863+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 10.0,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "low"
          }
        }
      },
      "entry_exit_deltas": {
        "delta_composite": -0.372,
        "delta_dark_pool_notional": 0.0,
        "delta_flow_conviction": 0.0,
        "delta_gamma": 0.0,
        "delta_iv_rank": 0.0,
        "delta_regime": 1,
        "delta_sector_strength": 1,
        "delta_sentiment": 0,
        "delta_squeeze_score": 0.0,
        "delta_vol": 0.0
      },
      "entry_order_id": "UNRESOLVED_ENTRY_OID:PLTR|LONG|1777579245",
      "entry_price": 139.21625,
      "entry_regime": "unknown",
      "entry_sector_profile": {
        "sector": "UNKNOWN"
      },
      "entry_timestamp": "2026-04-30T20:00:45.831729+00:00",
      "entry_ts": "2026-04-30T20:00:45.831729+00:00",
      "entry_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "exit_components_granular": {
        "exit_dark_pool_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_flow_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_gamma_collapse": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_insider_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_microstructure_noise": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_regime_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_score_deterioration": {
          "contribution_to_exit_score": 0.01302,
          "normalized_value": 0.0465,
          "raw_value": 0.0465
        },
        "exit_sector_rotation": {
          "contribution_to_exit_score": 0.05,
          "normalized_value": 1.0,
          "raw_value": 1.0
        },
        "exit_sentiment_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_time_decay": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_volatility_spike": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.08228,
          "raw_value": 0.0
        }
      },
      "exit_order_id": "49bf995d-c7c3-40f7-a15f-41c3db9a6a51",
      "exit_price": 145.75,
      "exit_quality_metrics": {
        "exit_efficiency": {
          "left_money": false,
          "saved_loss": true
        },
        "mae": null,
        "mfe": 3.84375,
        "post_exit_excursion": null,
        "profit_giveback": 0.0,
        "realized_pnl_price": 6.53375,
        "time_in_trade_sec": 63351.7
      },
      "exit_reason": "stale_alpha_cutoff(1048min,0.03%)",
      "exit_reason_code": "hold",
      "exit_regime": "NEUTRAL",
      "exit_regime_context": {},
      "exit_regime_decision": "normal",
      "exit_regime_reason": "",
      "exit_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.1,
          "earnings_weight": 1.0,
          "flow_weight": 1.2,
          "short_interest_weight": 0.8
        },
        "sector": "TECH",
        "version": "2026-01-20_sector_profiles_v1"
      },
      "exit_ts": "2026-05-01T13:36:37.528097+00:00",
      "exit_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "fees_usd": 0.0,
      "mode": "UNKNOWN",
      "order_id": "49bf995d-c7c3-40f7-a15f-41c3db9a6a51",
      "pnl": 6.53,
      "pnl_pct": 4.693238,
      "position_side": "long",
      "qty": 1.0,
      "regime_label": "NEUTRAL",
      "relative_strength_deterioration": 0.0,
      "replacement_candidate": null,
      "replacement_reasoning": null,
      "score_deterioration": 0.3719999999999999,
      "side": "buy",
      "strategy": "UNKNOWN",
      "symbol": "PLTR",
      "time_in_trade_minutes": 1055.8616061333332,
      "timestamp": "2026-05-01T13:36:37.528097+00:00",
      "trade_id": "open_PLTR_2026-04-30T20:00:45.831729+00:00",
      "trade_key": "PLTR|LONG|1777579245",
      "v2_exit_components": {
        "darkpool_deterioration": 0.0,
        "earnings_risk": 0.0,
        "flow_deterioration": 0.0,
        "overnight_flow_risk": 0.0,
        "regime_shift": 0.0,
        "score_deterioration": 0.0465,
        "sector_shift": 1.0,
        "sentiment_deterioration": 0.0,
        "thesis_invalidated": 0.0,
        "vol_expansion": 0.4114
      },
      "v2_exit_score": 0.104162,
      "variant_id": "B2_live_paper"
    },
    "composite_at_entry": 4.508,
    "composite_at_exit": 4.136,
    "composite_version": "v2",
    "entry_day": "2026-04-30",
    "entry_exit_deltas": {
      "delta_composite": -0.372,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_price": 139.21625,
    "entry_ts": "2026-04-30T20:00:45.831729+00:00",
    "entry_v2_score": 4.508,
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.01302,
        "normalized_value": 0.0465,
        "raw_value": 0.0465
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.05,
        "normalized_value": 1.0,
        "raw_value": 1.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.08228,
        "raw_value": 0.0
      }
    },
    "exit_day": "2026-05-01",
    "exit_price": 145.75,
    "exit_reason": "stale_alpha_cutoff(1048min,0.03%)",
    "exit_ts": "2026-05-01T13:36:37.528097+00:00",
    "exit_v2_score": 4.136,
    "feature_snapshot": {},
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": 6.533749999999998,
    "qty": 1.0,
    "realized_pnl_usd": 6.533749999999998,
    "regime": "NEUTRAL",
    "regime_snapshot": {
      "regime": "NEUTRAL"
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [],
    "size": 1.0,
    "source": "live",
    "symbol": "PLTR",
    "time_in_trade_minutes": 1055.8616061333332,
    "timestamp": "2026-05-01T13:36:38.041006+00:00",
    "trade_id": "live:PLTR:2026-04-30T20:00:45.831729+00:00",
    "unrealized_pnl_usd": null,
    "v2_exit_reason": "hold",
    "v2_exit_score": 0.104162
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 52.35,
    "entry_ts": "2026-05-01T13:37:03.143744+00:00",
    "entry_v2_score": 3.5639999999999996,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.943,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.0,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.042,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.5639999999999996,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 1.093369,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.199404,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 0.9,
          "flow_weight": 1.0,
          "short_interest_weight": 0.9
        },
        "sector": "FINANCIALS",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "XLF",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:37:03.145734+00:00",
    "trade_id": "live:XLF:2026-05-01T13:37:03.143744+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.5639999999999996
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 239.43,
    "entry_ts": "2026-05-01T13:37:22.776249+00:00",
    "entry_v2_score": 3.5559999999999996,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.942,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.024,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": -0.12,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.021,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.942,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.024,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": -0.12,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.021,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.5559999999999996,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": -0.039889,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.286887,
        "spy_overnight_ret": 0.0,
        "trade_count": 101,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "LOW",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:37:22.778188+00:00",
    "trade_id": "live:LOW:2026-05-01T13:37:22.776249+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.5559999999999996
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 174.72,
    "entry_ts": "2026-05-01T13:37:41.972413+00:00",
    "entry_v2_score": 3.5389999999999997,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.943,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.0,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.042,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.5389999999999997,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 0.837733,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.160951,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 2.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 2.0,
    "source": "live",
    "symbol": "XLI",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:37:41.974436+00:00",
    "trade_id": "live:XLI:2026-05-01T13:37:41.972413+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.5389999999999997
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 146.11,
    "entry_ts": "2026-05-01T13:37:52.497948+00:00",
    "entry_v2_score": 3.538,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.943,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.0,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.042,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.538,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 0.17062,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.142542,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 2.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 2.0,
    "source": "live",
    "symbol": "XLV",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:37:52.500011+00:00",
    "trade_id": "live:XLV:2026-05-01T13:37:52.497948+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.538
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 228.53,
    "entry_ts": "2026-05-01T13:38:16.374222+00:00",
    "entry_v2_score": 3.538,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.942,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.942,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.0,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.042,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.538,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": -0.395913,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.17134,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "JNJ",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:38:16.376623+00:00",
    "trade_id": "live:JNJ:2026-05-01T13:38:16.374222+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.538
  },
  {
    "_exit_attrib": {
      "_day": "2026-05-01",
      "_enriched_at": "2026-05-01T13:38:25.536178+00:00",
      "attribution_components": null,
      "attribution_schema_version": "1.0.0",
      "canonical_trade_id": "AMD|LONG|1777578028",
      "composite_at_entry": 4.441,
      "composite_at_exit": 0.0,
      "composite_components_at_entry": {},
      "composite_components_at_exit": {},
      "composite_version": "v2",
      "decision_id": "dec_AMD_2026-05-01T13-38-25.2199",
      "direction": "unknown",
      "direction_intel_embed": {
        "canonical_direction_components": [
          "premarket_direction",
          "postmarket_direction",
          "overnight_direction",
          "futures_direction",
          "volatility_direction",
          "breadth_direction",
          "sector_direction",
          "etf_flow_direction",
          "macro_direction",
          "uw_direction"
        ],
        "direction_intel_components_exit": {
          "breadth_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 1.0
          },
          "etf_flow_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "futures_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "macro_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "overnight_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "postmarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "premarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "sector_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "uw_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "volatility_direction": {
            "contribution_to_direction_score": -1.0,
            "normalized_value": -1.0,
            "raw_value": "low"
          }
        },
        "intel_deltas": {
          "breadth_adv_dec_delta": 0.0,
          "futures_direction_delta": 0.001642006048054566,
          "macro_risk_entry": false,
          "macro_risk_exit": false,
          "overnight_volatility_delta": 0.0,
          "sector_strength_delta": 0.0,
          "vol_regime_entry": "mid",
          "vol_regime_exit": "low"
        },
        "intel_snapshot_entry": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "down",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": -0.001642006048054566
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": -0.001642006048054566,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": -0.16420060480545662,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": -0.0007691379622368204,
              "risk_on_off": "neutral",
              "spy_overnight_ret": -0.0025148741338723115,
              "stale_1m": true,
              "volatility_regime": "mid",
              "vxx_vxz_ratio": 0.5131745172351562
            },
            "posture": "long",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 1.0,
            "regime_label": "bull",
            "regime_source": "structural_regime:RISK_ON",
            "structural_confidence": 1.0,
            "structural_regime": "RISK_ON",
            "ts": "2026-04-30T16:11:49.674674+00:00"
          },
          "sector_intel": {
            "sector": "TECH",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-04-30T16:12:40.196803+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 34.122,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "mid"
          }
        },
        "intel_snapshot_exit": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "flat",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": 0.0
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": 0.0,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": 0.0,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": 0.0,
              "risk_on_off": "neutral",
              "spy_overnight_ret": 0.0,
              "stale_1m": true,
              "volatility_regime": "low",
              "vxx_vxz_ratio": 0.0
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-05-01T13:31:02.428661+00:00"
          },
          "sector_intel": {
            "sector": "TECH",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-05-01T13:38:25.389733+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 10.0,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "low"
          }
        }
      },
      "entry_exit_deltas": {
        "delta_composite": -4.441,
        "delta_dark_pool_notional": 0.0,
        "delta_flow_conviction": -1.0,
        "delta_gamma": 0.0,
        "delta_iv_rank": 0.0,
        "delta_regime": 0,
        "delta_sector_strength": 0,
        "delta_sentiment": 1,
        "delta_squeeze_score": 0.0,
        "delta_vol": 0.0
      },
      "entry_order_id": "UNRESOLVED_ENTRY_OID:AMD|LONG|1777578028",
      "entry_price": 355.64,
      "entry_regime": "unknown",
      "entry_sector_profile": {
        "sector": "UNKNOWN"
      },
      "entry_timestamp": "2026-04-30T19:40:28.854691+00:00",
      "entry_ts": "2026-04-30T19:40:28.854691+00:00",
      "entry_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "exit_components_granular": {
        "exit_dark_pool_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_flow_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_gamma_collapse": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_insider_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_microstructure_noise": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_regime_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_score_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_sector_rotation": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_sentiment_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_time_decay": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_volatility_spike": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        }
      },
      "exit_order_id": "41173c06-63b0-4d56-8882-c1238061e66f",
      "exit_price": 355.08,
      "exit_quality_metrics": {
        "exit_efficiency": {
          "left_money": false,
          "saved_loss": false
        },
        "mae": null,
        "mfe": 0.0,
        "post_exit_excursion": null,
        "profit_giveback": null,
        "realized_pnl_price": -0.56,
        "time_in_trade_sec": 64676.37
      },
      "exit_reason": "underwater_time_decay_stop",
      "exit_reason_code": "other",
      "exit_regime": "unknown",
      "exit_regime_context": {
        "max_minutes": 60.0,
        "pnl_pct": -0.00252
      },
      "exit_regime_decision": "normal",
      "exit_regime_reason": "underwater_time_decay_stop",
      "exit_sector_profile": {
        "sector": "UNKNOWN"
      },
      "exit_ts": "2026-05-01T13:38:25.219989+00:00",
      "exit_uw": {},
      "fees_usd": 0.0,
      "mode": "UNKNOWN",
      "order_id": "41173c06-63b0-4d56-8882-c1238061e66f",
      "pnl": -0.56,
      "pnl_pct": -0.157463,
      "position_side": "long",
      "qty": 1.0,
      "regime_label": "UNKNOWN",
      "relative_strength_deterioration": 0.0,
      "replacement_candidate": null,
      "replacement_reasoning": null,
      "score_deterioration": 0.0,
      "side": "buy",
      "strategy": "UNKNOWN",
      "symbol": "AMD",
      "time_in_trade_minutes": 1077.9394216333333,
      "timestamp": "2026-05-01T13:38:25.219989+00:00",
      "trade_id": "open_AMD_2026-04-30T19:40:28.854691+00:00",
      "trade_key": "AMD|LONG|1777578028",
      "v2_exit_components": {},
      "v2_exit_score": 0.0,
      "variant_id": "B2_live_paper"
    },
    "composite_at_entry": 4.441,
    "composite_at_exit": 0.0,
    "composite_version": "v2",
    "entry_day": "2026-04-30",
    "entry_exit_deltas": {
      "delta_composite": -4.441,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 0,
      "delta_sector_strength": 0,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_price": 355.64,
    "entry_ts": "2026-04-30T19:40:28.854691+00:00",
    "entry_v2_score": 4.441,
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_day": "2026-05-01",
    "exit_price": 355.08,
    "exit_reason": "underwater_time_decay_stop",
    "exit_ts": "2026-05-01T13:38:25.219989+00:00",
    "exit_v2_score": 0.0,
    "feature_snapshot": {},
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": -0.5600000000000023,
    "qty": 1.0,
    "realized_pnl_usd": -0.5600000000000023,
    "regime": "unknown",
    "regime_snapshot": {
      "regime": "unknown"
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [],
    "size": 1.0,
    "source": "live",
    "symbol": "AMD",
    "time_in_trade_minutes": 1077.9394216333333,
    "timestamp": "2026-05-01T13:38:25.535969+00:00",
    "trade_id": "live:AMD:2026-04-30T19:40:28.854691+00:00",
    "unrealized_pnl_usd": null,
    "v2_exit_reason": "",
    "v2_exit_score": 0.0
  },
  {
    "composite_version": "v2",
    "entry_day": "2026-05-01",
    "entry_price": 722.18,
    "entry_ts": "2026-05-01T13:38:30.858478+00:00",
    "entry_v2_score": 3.537,
    "exit_day": null,
    "exit_price": null,
    "exit_reason": null,
    "exit_ts": null,
    "feature_snapshot": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.942,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "intel_snapshot": {
      "components": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.942,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.0,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.042,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "score": 3.537,
      "uw_intel_version": "2026-01-20_uw_v1",
      "v2_inputs": {
        "beta_vs_spy": 1.0,
        "direction": "bullish",
        "futures_direction": "flat",
        "market_trend": "",
        "posture": "neutral",
        "posture_confidence": 0.0,
        "qqq_overnight_ret": 0.0,
        "realized_vol_20d": 0.116934,
        "spy_overnight_ret": 0.0,
        "trade_count": 100,
        "uw_conviction": 1.0,
        "volatility_regime": "mid",
        "weights_version": "2026-01-20_wt1"
      },
      "v2_uw_inputs": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "v2_uw_regime_profile": {
        "alignment": 0.25,
        "regime_label": "NEUTRAL",
        "version": "2026-01-20_regime_v1"
      },
      "v2_uw_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 1.0,
          "flow_weight": 1.0,
          "short_interest_weight": 1.0
        },
        "sector": "UNKNOWN",
        "version": "2026-01-20_sector_profiles_v1"
      }
    },
    "is_live": true,
    "is_shadow": false,
    "pnl_total_usd": null,
    "qty": 1.0,
    "realized_pnl_usd": null,
    "regime": "mixed",
    "regime_snapshot": {
      "regime": "mixed",
      "sector_posture": null,
      "trend_bucket": null,
      "volatility_bucket": null
    },
    "sector": "UNKNOWN",
    "side": "long",
    "signals": [
      "calendar",
      "congress",
      "dark_pool",
      "etf_flow",
      "event",
      "flow",
      "freshness_factor",
      "ftd_pressure",
      "greeks_gamma",
      "insider",
      "institutional",
      "iv_rank",
      "iv_skew",
      "market_tide",
      "motif_bonus",
      "oi_change",
      "regime",
      "shorts_squeeze",
      "smile",
      "squeeze_score",
      "toxicity_correlation_penalty",
      "toxicity_penalty",
      "whale"
    ],
    "size": 1.0,
    "source": "live",
    "symbol": "SPY",
    "time_in_trade_minutes": null,
    "timestamp": "2026-05-01T13:38:30.860515+00:00",
    "trade_id": "live:SPY:2026-05-01T13:38:30.858478+00:00",
    "unrealized_pnl_usd": null,
    "v2_score": 3.537
  },
  {
    "_exit_attrib": {
      "_day": "2026-05-01",
      "_enriched_at": "2026-05-01T13:38:32.091241+00:00",
      "attribution_components": [
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_flow_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_darkpool_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_sentiment_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.012628,
          "signal_id": "exit_score_deterioration",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_regime_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_sector_shift",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.01669,
          "signal_id": "exit_vol_expansion",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_thesis_invalidated",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_earnings_risk",
          "source": "exit"
        },
        {
          "contribution_to_score": 0.0,
          "signal_id": "exit_overnight_flow_risk",
          "source": "exit"
        }
      ],
      "attribution_schema_version": "1.0.0",
      "canonical_trade_id": "GS|LONG|1777578183",
      "composite_at_entry": 4.273,
      "composite_at_exit": 3.912,
      "composite_components_at_entry": {
        "calendar": 0.0,
        "congress": 0.0,
        "dark_pool": 0.023,
        "etf_flow": 0.012,
        "event": 0.204,
        "flow": 2.5,
        "freshness_factor": 0.987,
        "ftd_pressure": 0.036,
        "greeks_gamma": 0.024,
        "insider": 0.075,
        "institutional": 0.0,
        "iv_rank": 0.018,
        "iv_skew": 0.07,
        "market_tide": 0.276,
        "motif_bonus": 0.0,
        "oi_change": 0.021,
        "regime": 0.008,
        "shorts_squeeze": 0.0,
        "smile": 0.004,
        "squeeze_score": 0.03,
        "toxicity_correlation_penalty": 0.0,
        "toxicity_penalty": -0.162,
        "whale": 0.0
      },
      "composite_components_at_exit": {},
      "composite_version": "v2",
      "decision_id": "dec_GS_2026-05-01T13-38-31.9462",
      "direction": "bullish",
      "direction_intel_embed": {
        "canonical_direction_components": [
          "premarket_direction",
          "postmarket_direction",
          "overnight_direction",
          "futures_direction",
          "volatility_direction",
          "breadth_direction",
          "sector_direction",
          "etf_flow_direction",
          "macro_direction",
          "uw_direction"
        ],
        "direction_intel_components_exit": {
          "breadth_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 1.0
          },
          "etf_flow_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "futures_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "macro_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "overnight_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "postmarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "premarket_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "sector_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": 0.0
          },
          "uw_direction": {
            "contribution_to_direction_score": 0.0,
            "normalized_value": 0.0,
            "raw_value": "neutral"
          },
          "volatility_direction": {
            "contribution_to_direction_score": -1.0,
            "normalized_value": -1.0,
            "raw_value": "low"
          }
        },
        "intel_deltas": {
          "breadth_adv_dec_delta": 0.0,
          "futures_direction_delta": 0.008511533671702702,
          "macro_risk_entry": false,
          "macro_risk_exit": false,
          "overnight_volatility_delta": 0.0,
          "sector_strength_delta": 0.0,
          "vol_regime_entry": "mid",
          "vol_regime_exit": "low"
        },
        "intel_snapshot_entry": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "down",
            "NQ_direction": "down",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": -0.008511533671702702
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": -0.008511533671702702,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": -0.8511533671702702,
            "premarket_sentiment": "bearish",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "down",
              "qqq_overnight_ret": -0.008381100618106036,
              "risk_on_off": "neutral",
              "spy_overnight_ret": -0.008641966725299367,
              "stale_1m": true,
              "volatility_regime": "mid",
              "vxx_vxz_ratio": 0.5116173534216736
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-04-30T19:40:48.571024+00:00"
          },
          "sector_intel": {
            "sector": "FINANCIALS",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-04-30T19:43:04.046563+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 33.821999999999996,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "mid"
          }
        },
        "intel_snapshot_exit": {
          "breadth_intel": {
            "adv_dec_ratio": 1.0,
            "index_breadth": {},
            "new_highs_lows": 0.0,
            "sector_breadth": {},
            "up_vol_down_vol_ratio": 1.0
          },
          "etf_flow_intel": {
            "IWM_flow": 0.0,
            "QQQ_flow": 0.0,
            "SPY_flow": 0.0,
            "sector_ETF_flows": {}
          },
          "futures_intel": {
            "ES_direction": "flat",
            "NQ_direction": "flat",
            "RTY_direction": "flat",
            "VX_direction": "flat",
            "futures_basis": 0.0,
            "futures_trend_strength": 0.0
          },
          "macro_intel": {
            "macro_events_today": [],
            "macro_risk_flag": false,
            "macro_sentiment_score": 0.0
          },
          "overnight_intel": {
            "overnight_dark_pool_imbalance": 0.0,
            "overnight_flow": 0.0,
            "overnight_return": 0.0,
            "overnight_volatility": 0.0
          },
          "postmarket_intel": {
            "after_hours_volume_ratio": 1.0,
            "earnings_reaction_flag": false,
            "postmarket_gap_pct": 0.0,
            "postmarket_sentiment": "neutral"
          },
          "premarket_intel": {
            "premarket_flow": 0.0,
            "premarket_gap_pct": 0.0,
            "premarket_sentiment": "neutral",
            "premarket_volatility": 0.0,
            "premarket_volume_ratio": 1.0
          },
          "regime_posture": {
            "market_context": {
              "market_trend": "flat",
              "qqq_overnight_ret": 0.0,
              "risk_on_off": "neutral",
              "spy_overnight_ret": 0.0,
              "stale_1m": true,
              "volatility_regime": "low",
              "vxx_vxz_ratio": 0.0
            },
            "posture": "neutral",
            "posture_flags": {
              "allow_new_longs": true,
              "prefer_shorts": false,
              "tighten_long_exits": false
            },
            "regime_confidence": 0.45,
            "regime_label": "chop",
            "regime_source": "default_chop",
            "structural_confidence": 0.5,
            "structural_regime": "NEUTRAL",
            "ts": "2026-05-01T13:31:02.428661+00:00"
          },
          "sector_intel": {
            "sector": "FINANCIALS",
            "sector_ETF_flow": 0.0,
            "sector_momentum": 0.0,
            "sector_strength_rank": 0,
            "sector_volatility": 0.0
          },
          "timestamp": "2026-05-01T13:38:31.947078+00:00",
          "uw_intel": {
            "uw_overnight_sentiment": "neutral",
            "uw_premarket_sentiment": "neutral",
            "uw_preopen_dark_pool": 0.0,
            "uw_preopen_flow": 0.0
          },
          "volatility_intel": {
            "VIX_change": 0.0,
            "VIX_level": 10.0,
            "VVIX_level": 0.0,
            "realized_vol_1d": 0.0,
            "realized_vol_20d": 0.2,
            "realized_vol_5d": 0.0,
            "vol_regime": "low"
          }
        }
      },
      "entry_exit_deltas": {
        "delta_composite": -0.361,
        "delta_dark_pool_notional": 0.0,
        "delta_flow_conviction": 0.0,
        "delta_gamma": 0.0,
        "delta_iv_rank": 0.0,
        "delta_regime": 0,
        "delta_sector_strength": 0,
        "delta_sentiment": 0,
        "delta_squeeze_score": 0.0,
        "delta_vol": 0.0
      },
      "entry_order_id": "b73a9726-b047-49ab-a3cb-a1c3fc8dad1e",
      "entry_price": 919.23,
      "entry_regime": "NEUTRAL",
      "entry_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 0.9,
          "flow_weight": 1.0,
          "short_interest_weight": 0.9
        },
        "sector": "FINANCIALS",
        "version": "2026-01-20_sector_profiles_v1"
      },
      "entry_timestamp": "2026-04-30T19:43:03.382692+00:00",
      "entry_ts": "2026-04-30T19:43:03.382692+00:00",
      "entry_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "exit_components_granular": {
        "exit_dark_pool_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_flow_deterioration": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_gamma_collapse": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_insider_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_microstructure_noise": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_regime_shift": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_score_deterioration": {
          "contribution_to_exit_score": 0.012628,
          "normalized_value": 0.0451,
          "raw_value": 0.0451
        },
        "exit_sector_rotation": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_sentiment_reversal": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_time_decay": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "exit_volatility_spike": {
          "contribution_to_exit_score": 0.0,
          "normalized_value": 0.03338,
          "raw_value": 0.0
        }
      },
      "exit_order_id": "6e7c880f-107a-44b6-a4ae-1a81c40d3c8f",
      "exit_price": 921.0,
      "exit_quality_metrics": {
        "exit_efficiency": {
          "left_money": true,
          "saved_loss": true
        },
        "mae": null,
        "mfe": 3.72,
        "post_exit_excursion": null,
        "profit_giveback": 0.524194,
        "realized_pnl_price": 1.77,
        "time_in_trade_sec": 64528.56
      },
      "exit_reason": "stale_alpha_cutoff(1075min,0.00%)",
      "exit_reason_code": "hold",
      "exit_regime": "NEUTRAL",
      "exit_regime_context": {},
      "exit_regime_decision": "normal",
      "exit_regime_reason": "",
      "exit_sector_profile": {
        "multipliers": {
          "darkpool_weight": 1.0,
          "earnings_weight": 0.9,
          "flow_weight": 1.0,
          "short_interest_weight": 0.9
        },
        "sector": "FINANCIALS",
        "version": "2026-01-20_sector_profiles_v1"
      },
      "exit_ts": "2026-05-01T13:38:31.946213+00:00",
      "exit_uw": {
        "darkpool_bias": 0.0,
        "earnings_proximity": 999,
        "flow_strength": 1.0,
        "regime_alignment": 0.25,
        "sector_alignment": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "uw_intel_source": "premarket_postmarket",
        "uw_intel_version": "2026-01-20_uw_v1"
      },
      "fees_usd": 0.0,
      "mode": "UNKNOWN",
      "order_id": "6e7c880f-107a-44b6-a4ae-1a81c40d3c8f",
      "pnl": 1.77,
      "pnl_pct": 0.192552,
      "position_side": "long",
      "qty": 1.0,
      "regime_label": "NEUTRAL",
      "relative_strength_deterioration": 0.0,
      "replacement_candidate": null,
      "replacement_reasoning": null,
      "score_deterioration": 0.36099999999999977,
      "side": "buy",
      "strategy": "UNKNOWN",
      "symbol": "GS",
      "time_in_trade_minutes": 1075.4760586833333,
      "timestamp": "2026-05-01T13:38:31.946213+00:00",
      "trade_id": "open_GS_2026-04-30T19:43:03.382692+00:00",
      "trade_key": "GS|LONG|1777578183",
      "v2_exit_components": {
        "darkpool_deterioration": 0.0,
        "earnings_risk": 0.0,
        "flow_deterioration": 0.0,
        "overnight_flow_risk": 0.0,
        "regime_shift": 0.0,
        "score_deterioration": 0.0451,
        "sector_shift": 0.0,
        "sentiment_deterioration": 0.0,
        "thesis_invalidated": 0.0,
        "vol_expansion": 0.1669
      },
      "v2_exit_score": 0.029321799999999995,
      "variant_id": "paper_aggressive"
    },
    "composite_at_entry": 4.273,
    "composite_at_exit": 3.912,
    "composite_version": "v2",
    "entry_day": "2026-04-30",
    "entry_exit_deltas": {
      "delta_composite": -0.361,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
   
```

### All feature snapshots (per-symbol averages; live vs shadow)
```
[
  {
    "symbol": "BLK",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9475999999999999,
        "feature": "freshness_factor",
        "live_mean": 0.9475999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.25260000000000005,
        "feature": "market_tide",
        "live_mean": 0.25260000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.2040000000000001,
        "feature": "event",
        "live_mean": 0.2040000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.048000000000000015,
        "feature": "greeks_gamma",
        "live_mean": 0.048000000000000015,
        "shadow_mean": null
      },
      {
        "delta": -0.04200000000000001,
        "feature": "oi_change",
        "live_mean": 0.04200000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.036000000000000004,
        "feature": "ftd_pressure",
        "live_mean": 0.036000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.018000000000000002,
        "feature": "iv_rank",
        "live_mean": 0.018000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "squeeze_score",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "RIVN",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9775454545454544,
        "feature": "freshness_factor",
        "live_mean": 0.9775454545454544,
        "shadow_mean": null
      },
      {
        "delta": -0.2524545454545454,
        "feature": "market_tide",
        "live_mean": 0.2524545454545454,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000001,
        "feature": "event",
        "live_mean": 0.20400000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000002,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.017999999999999995,
        "feature": "iv_rank",
        "live_mean": 0.017999999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000002,
        "feature": "regime",
        "live_mean": 0.008000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000001,
        "feature": "smile",
        "live_mean": 0.004000000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "COST",
    "top_feature_mean_deltas": [
      {
        "delta": -2.611111111111111,
        "feature": "flow",
        "live_mean": 2.611111111111111,
        "shadow_mean": null
      },
      {
        "delta": -0.8236666666666665,
        "feature": "freshness_factor",
        "live_mean": 0.8236666666666665,
        "shadow_mean": null
      },
      {
        "delta": -0.25788888888888895,
        "feature": "market_tide",
        "live_mean": 0.25788888888888895,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.041999999999999996,
        "feature": "oi_change",
        "live_mean": 0.041999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.030000000000000002,
        "feature": "squeeze_score",
        "live_mean": 0.030000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "META",
    "top_feature_mean_deltas": [
      {
        "delta": -2.576923076923077,
        "feature": "flow",
        "live_mean": 2.576923076923077,
        "shadow_mean": null
      },
      {
        "delta": -0.9724615384615386,
        "feature": "freshness_factor",
        "live_mean": 0.9724615384615386,
        "shadow_mean": null
      },
      {
        "delta": -0.2525384615384615,
        "feature": "market_tide",
        "live_mean": 0.2525384615384615,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000004,
        "feature": "event",
        "live_mean": 0.20400000000000004,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": 0.06000000000000002,
        "feature": "iv_rank",
        "live_mean": -0.06000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.048,
        "feature": "greeks_gamma",
        "live_mean": 0.048,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.023,
        "feature": "dark_pool",
        "live_mean": 0.023,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "etf_flow",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "squeeze_score",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "MRNA",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9713333333333333,
        "feature": "freshness_factor",
        "live_mean": 0.9713333333333333,
        "shadow_mean": null
      },
      {
        "delta": -0.2524166666666667,
        "feature": "market_tide",
        "live_mean": 0.2524166666666667,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000004,
        "feature": "event",
        "live_mean": 0.20400000000000004,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.12000000000000004,
        "feature": "oi_change",
        "live_mean": 0.12000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000002,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.017999999999999995,
        "feature": "iv_rank",
        "live_mean": 0.017999999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000002,
        "feature": "regime",
        "live_mean": 0.008000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000001,
        "feature": "smile",
        "live_mean": 0.004000000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "CAT",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.943,
        "feature": "freshness_factor",
        "live_mean": 0.943,
        "shadow_mean": null
      },
      {
        "delta": -0.276,
        "feature": "market_tide",
        "live_mean": 0.276,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.061,
        "feature": "oi_change",
        "live_mean": 0.061,
        "shadow_mean": null
      },
      {
        "delta": -0.06,
        "feature": "greeks_gamma",
        "live_mean": 0.06,
        "shadow_mean": null
      },
      {
        "delta": 0.06,
        "feature": "iv_rank",
        "live_mean": -0.06,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.03,
        "feature": "squeeze_score",
        "live_mean": 0.03,
        "shadow_mean": null
      },
      {
        "delta": -0.023,
        "feature": "dark_pool",
        "live_mean": 0.023,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "etf_flow",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "GS",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9685294117647059,
        "feature": "freshness_factor",
        "live_mean": 0.9685294117647059,
        "shadow_mean": null
      },
      {
        "delta": -0.2539411764705882,
        "feature": "market_tide",
        "live_mean": 0.2539411764705882,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000007,
        "feature": "event",
        "live_mean": 0.20400000000000007,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.04658823529411766,
        "feature": "greeks_gamma",
        "live_mean": 0.04658823529411766,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000003,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.021,
        "feature": "oi_change",
        "live_mean": 0.021,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.013058823529411769,
        "feature": "squeeze_score",
        "live_mean": 0.013058823529411769,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "TGT",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9669199999999999,
        "feature": "freshness_factor",
        "live_mean": 0.9669199999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.25336,
        "feature": "market_tide",
        "live_mean": 0.25336,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000001,
        "feature": "event",
        "live_mean": 0.20400000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999995,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999997,
        "feature": "insider",
        "live_mean": 0.07499999999999997,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000005,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.050880000000000015,
        "feature": "greeks_gamma",
        "live_mean": 0.050880000000000015,
        "shadow_mean": null
      },
      {
        "delta": -0.03600000000000001,
        "feature": "ftd_pressure",
        "live_mean": 0.03600000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.021000000000000005,
        "feature": "oi_change",
        "live_mean": 0.021000000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.018000000000000006,
        "feature": "iv_rank",
        "live_mean": 0.018000000000000006,
        "shadow_mean": null
      },
      {
        "delta": -0.012720000000000004,
        "feature": "squeeze_score",
        "live_mean": 0.012720000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000005,
        "feature": "regime",
        "live_mean": 0.008000000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000003,
        "feature": "smile",
        "live_mean": 0.004000000000000003,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "COIN",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9749999999999999,
        "feature": "freshness_factor",
        "live_mean": 0.9749999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.2524285714285714,
        "feature": "market_tide",
        "live_mean": 0.2524285714285714,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.12,
        "feature": "oi_change",
        "live_mean": 0.12,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "LOW",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9645,
        "feature": "freshness_factor",
        "live_mean": 0.9645,
        "shadow_mean": null
      },
      {
        "delta": -0.264,
        "feature": "market_tide",
        "live_mean": 0.264,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": 0.12,
        "feature": "iv_rank",
        "live_mean": -0.12,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.036000000000000004,
        "feature": "greeks_gamma",
        "live_mean": 0.036000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.023,
        "feature": "dark_pool",
        "live_mean": 0.023,
        "shadow_mean": null
      },
      {
        "delta": -0.021,
        "feature": "oi_change",
        "live_mean": 0.021,
        "shadow_mean": null
      },
      {
        "delta": -0.020999999999999998,
        "feature": "squeeze_score",
        "live_mean": 0.020999999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "etf_flow",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "NVDA",
    "top_feature_mean_deltas": []
  },
  {
    "symbol": "XLI",
    "top_feature_mean_deltas": [
      {
        "delta": -2.9047619047619047,
        "feature": "flow",
        "live_mean": 2.9047619047619047,
        "shadow_mean": null
      },
      {
        "delta": -0.8749047619047617,
        "feature": "freshness_factor",
        "live_mean": 0.8749047619047617,
        "shadow_mean": null
      },
      {
        "delta": -0.2546666666666666,
        "feature": "market_tide",
        "live_mean": 0.2546666666666666,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000007,
        "feature": "event",
        "live_mean": 0.20400000000000007,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.04200000000000001,
        "feature": "oi_change",
        "live_mean": 0.04200000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.036000000000000004,
        "feature": "ftd_pressure",
        "live_mean": 0.036000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.030000000000000016,
        "feature": "squeeze_score",
        "live_mean": 0.030000000000000016,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.018000000000000002,
        "feature": "iv_rank",
        "live_mean": 0.018000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "XOM",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9683333333333333,
        "feature": "freshness_factor",
        "live_mean": 0.9683333333333333,
        "shadow_mean": null
      },
      {
        "delta": -0.254074074074074,
        "feature": "market_tide",
        "live_mean": 0.254074074074074,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999995,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.11540740740740743,
        "feature": "oi_change",
        "live_mean": 0.11540740740740743,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000005,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000005,
        "shadow_mean": null
      },
      {
        "delta": 0.06444444444444448,
        "feature": "iv_rank",
        "live_mean": -0.06444444444444448,
        "shadow_mean": null
      },
      {
        "delta": -0.05333333333333336,
        "feature": "greeks_gamma",
        "live_mean": 0.05333333333333336,
        "shadow_mean": null
      },
      {
        "delta": -0.03600000000000001,
        "feature": "ftd_pressure",
        "live_mean": 0.03600000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.01333333333333334,
        "feature": "squeeze_score",
        "live_mean": 0.01333333333333334,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000005,
        "feature": "regime",
        "live_mean": 0.008000000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000003,
        "feature": "smile",
        "live_mean": 0.004000000000000003,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "AAPL",
    "top_feature_mean_deltas": [
      {
        "delta": -2.875,
        "feature": "flow",
        "live_mean": 2.875,
        "shadow_mean": null
      },
      {
        "delta": -0.9787499999999999,
        "feature": "freshness_factor",
        "live_mean": 0.9787499999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.2525833333333333,
        "feature": "market_tide",
        "live_mean": 0.2525833333333333,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000004,
        "feature": "event",
        "live_mean": 0.20400000000000004,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000002,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.017999999999999995,
        "feature": "iv_rank",
        "live_mean": 0.017999999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000002,
        "feature": "regime",
        "live_mean": 0.008000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000001,
        "feature": "smile",
        "live_mean": 0.004000000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "SLB",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.969153846153846,
        "feature": "freshness_factor",
        "live_mean": 0.969153846153846,
        "shadow_mean": null
      },
      {
        "delta": -0.25230769230769223,
        "feature": "market_tide",
        "live_mean": 0.25230769230769223,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000004,
        "feature": "event",
        "live_mean": 0.20400000000000004,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.11976923076923078,
        "feature": "oi_change",
        "live_mean": 0.11976923076923078,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.048,
        "feature": "greeks_gamma",
        "live_mean": 0.048,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.023,
        "feature": "dark_pool",
        "live_mean": 0.023,
        "shadow_mean": null
      },
      {
        "delta": -0.017999999999999995,
        "feature": "iv_rank",
        "live_mean": 0.017999999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "etf_flow",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "squeeze_score",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "HD",
    "top_feature_mean_deltas": [
      {
        "delta": -2.8333333333333335,
        "feature": "flow",
        "live_mean": 2.8333333333333335,
        "shadow_mean": null
      },
      {
        "delta": -0.922,
        "feature": "freshness_factor",
        "live_mean": 0.922,
        "shadow_mean": null
      },
      {
        "delta": -0.26,
        "feature": "market_tide",
        "live_mean": 0.26,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.042,
        "feature": "oi_change",
        "live_mean": 0.042,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.03,
        "feature": "squeeze_score",
        "live_mean": 0.03,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "AMD",
    "top_feature_mean_deltas": [
      {
        "delta": -3.0,
        "feature": "flow",
        "live_mean": 3.0,
        "shadow_mean": null
      },
      {
        "delta": -0.976,
        "feature": "freshness_factor",
        "live_mean": 0.976,
        "shadow_mean": null
      },
      {
        "delta": -0.253,
        "feature": "market_tide",
        "live_mean": 0.253,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": 0.12,
        "feature": "iv_rank",
        "live_mean": -0.12,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.04800000000000001,
        "feature": "greeks_gamma",
        "live_mean": 0.04800000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000003,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "squeeze_score",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "BA",
    "top_feature_mean_deltas": []
  },
  {
    "symbol": "XLP",
    "top_feature_mean_deltas": [
      {
        "delta": -2.9038461538461537,
        "feature": "flow",
        "live_mean": 2.9038461538461537,
        "shadow_mean": null
      },
      {
        "delta": -0.8583461538461541,
        "feature": "freshness_factor",
        "live_mean": 0.8583461538461541,
        "shadow_mean": null
      },
      {
        "delta": -0.2525384615384615,
        "feature": "market_tide",
        "live_mean": 0.2525384615384615,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000001,
        "feature": "event",
        "live_mean": 0.20400000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999995,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999997,
        "feature": "insider",
        "live_mean": 0.07499999999999997,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000005,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.04200000000000001,
        "feature": "oi_change",
        "live_mean": 0.04200000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.03600000000000001,
        "feature": "ftd_pressure",
        "live_mean": 0.03600000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.03000000000000002,
        "feature": "squeeze_score",
        "live_mean": 0.03000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.018000000000000006,
        "feature": "iv_rank",
        "live_mean": 0.018000000000000006,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000005,
        "feature": "regime",
        "live_mean": 0.008000000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000003,
        "feature": "smile",
        "live_mean": 0.004000000000000003,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "AMZN",
    "top_feature_mean_deltas": [
      {
        "delta": -2.6785714285714284,
        "feature": "flow",
        "live_mean": 2.6785714285714284,
        "shadow_mean": null
      },
      {
        "delta": -0.9660714285714286,
        "feature": "freshness_factor",
        "live_mean": 0.9660714285714286,
        "shadow_mean": null
      },
      {
        "delta": -0.25442857142857145,
        "feature": "market_tide",
        "live_mean": 0.25442857142857145,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000004,
        "feature": "event",
        "live_mean": 0.20400000000000004,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.05314285714285715,
        "feature": "greeks_gamma",
        "live_mean": 0.05314285714285715,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.023,
        "feature": "dark_pool",
        "live_mean": 0.023,
        "shadow_mean": null
      },
      {
        "delta": -0.017999999999999995,
        "feature": "iv_rank",
        "live_mean": 0.017999999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.013285714285714288,
        "feature": "squeeze_score",
        "live_mean": 0.013285714285714288,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "etf_flow",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "WMT",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9672499999999999,
        "feature": "freshness_factor",
        "live_mean": 0.9672499999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.25850000000000006,
        "feature": "market_tide",
        "live_mean": 0.25850000000000006,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.11975,
        "feature": "oi_change",
        "live_mean": 0.11975,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.06599999999999999,
        "feature": "greeks_gamma",
        "live_mean": 0.06599999999999999,
        "shadow_mean": null
      },
      {
        "delta": 0.06,
        "feature": "iv_rank",
        "live_mean": -0.06,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.016499999999999997,
        "feature": "squeeze_score",
        "live_mean": 0.016499999999999997,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "UNH",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9700000000000001,
        "feature": "freshness_factor",
        "live_mean": 0.9700000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.25233333333333335,
        "feature": "market_tide",
        "live_mean": 0.25233333333333335,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.12,
        "feature": "iv_rank",
        "live_mean": 0.12,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.061,
        "feature": "oi_change",
        "live_mean": 0.061,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "XLF",
    "top_feature_mean_deltas": [
      {
        "delta": -2.88,
        "feature": "flow",
        "live_mean": 2.88,
        "shadow_mean": null
      },
      {
        "delta": -0.85944,
        "feature": "freshness_factor",
        "live_mean": 0.85944,
        "shadow_mean": null
      },
      {
        "delta": -0.25436,
        "feature": "market_tide",
        "live_mean": 0.25436,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000001,
        "feature": "event",
        "live_mean": 0.20400000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999995,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999997,
        "feature": "insider",
        "live_mean": 0.07499999999999997,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000005,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.04200000000000001,
        "feature": "oi_change",
        "live_mean": 0.04200000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.03600000000000001,
        "feature": "ftd_pressure",
        "live_mean": 0.03600000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.030000000000000016,
        "feature": "squeeze_score",
        "live_mean": 0.030000000000000016,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.018000000000000006,
        "feature": "iv_rank",
        "live_mean": 0.018000000000000006,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000005,
        "feature": "regime",
        "live_mean": 0.008000000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000003,
        "feature": "smile",
        "live_mean": 0.004000000000000003,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "JPM",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9595999999999998,
        "feature": "freshness_factor",
        "live_mean": 0.9595999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.2540666666666667,
        "feature": "market_tide",
        "live_mean": 0.2540666666666667,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000007,
        "feature": "event",
        "live_mean": 0.20400000000000007,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.05280000000000001,
        "feature": "greeks_gamma",
        "live_mean": 0.05280000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.02366666666666667,
        "feature": "oi_change",
        "live_mean": 0.02366666666666667,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000003,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.013200000000000002,
        "feature": "squeeze_score",
        "live_mean": 0.013200000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "JNJ",
    "top_feature_mean_deltas": [
      {
        "delta": -2.90625,
        "feature": "flow",
        "live_mean": 2.90625,
        "shadow_mean": null
      },
      {
        "delta": -0.8886249999999998,
        "feature": "freshness_factor",
        "live_mean": 0.8886249999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.25662499999999994,
        "feature": "market_tide",
        "live_mean": 0.25662499999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000007,
        "feature": "event",
        "live_mean": 0.20400000000000007,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.042,
        "feature": "oi_change",
        "live_mean": 0.042,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.030000000000000013,
        "feature": "squeeze_score",
        "live_mean": 0.030000000000000013,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000003,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "MS",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9518888888888889,
        "feature": "freshness_factor",
        "live_mean": 0.9518888888888889,
        "shadow_mean": null
      },
      {
        "delta": -0.25255555555555553,
        "feature": "market_tide",
        "live_mean": 0.25255555555555553,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.020999999999999998,
        "feature": "oi_change",
        "live_mean": 0.020999999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "NFLX",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9443333333333334,
        "feature": "freshness_factor",
        "live_mean": 0.9443333333333334,
        "shadow_mean": null
      },
      {
        "delta": -0.25300000000000006,
        "feature": "market_tide",
        "live_mean": 0.25300000000000006,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.12,
        "feature": "iv_rank",
        "live_mean": 0.12,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "XLV",
    "top_feature_mean_deltas": [
      {
        "delta": -2.880952380952381,
        "feature": "flow",
        "live_mean": 2.880952380952381,
        "shadow_mean": null
      },
      {
        "delta": -0.893857142857143,
        "feature": "freshness_factor",
        "live_mean": 0.893857142857143,
        "shadow_mean": null
      },
      {
        "delta": -0.2559047619047619,
        "feature": "market_tide",
        "live_mean": 0.2559047619047619,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000007,
        "feature": "event",
        "live_mean": 0.20400000000000007,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.04200000000000001,
        "feature": "oi_change",
        "live_mean": 0.04200000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.036000000000000004,
        "feature": "ftd_pressure",
        "live_mean": 0.036000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.030000000000000016,
        "feature": "squeeze_score",
        "live_mean": 0.030000000000000016,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.018000000000000002,
        "feature": "iv_rank",
        "live_mean": 0.018000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "COP",
    "top_feature_mean_deltas": []
  },
  {
    "symbol": "WFC",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9508125000000001,
        "feature": "freshness_factor",
        "live_mean": 0.9508125000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.252625,
        "feature": "market_tide",
        "live_mean": 0.252625,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000007,
        "feature": "event",
        "live_mean": 0.20400000000000007,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.06099999999999997,
        "feature": "oi_change",
        "live_mean": 0.06099999999999997,
        "shadow_mean": null
      },
      {
        "delta": -0.04800000000000001,
        "feature": "greeks_gamma",
        "live_mean": 0.04800000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000003,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "squeeze_score",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "XLK",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9726111111111108,
        "feature": "freshness_factor",
        "live_mean": 0.9726111111111108,
        "shadow_mean": null
      },
      {
        "delta": -0.25249999999999995,
        "feature": "market_tide",
        "live_mean": 0.25249999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000007,
        "feature": "event",
        "live_mean": 0.20400000000000007,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.048000000000000015,
        "feature": "greeks_gamma",
        "live_mean": 0.048000000000000015,
        "shadow_mean": null
      },
      {
        "delta": -0.036000000000000004,
        "feature": "ftd_pressure",
        "live_mean": 0.036000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.021000000000000005,
        "feature": "oi_change",
        "live_mean": 0.021000000000000005,
        "shadow_mean": null
      },
      {
        "delta": -0.018000000000000002,
        "feature": "iv_rank",
        "live_mean": 0.018000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "squeeze_score",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "QQQ",
    "top_feature_mean_deltas": [
      {
        "delta": -2.85,
        "feature": "flow",
        "live_mean": 2.85,
        "shadow_mean": null
      },
      {
        "delta": -0.8734499999999998,
        "feature": "freshness_factor",
        "live_mean": 0.8734499999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.25494999999999995,
        "feature": "market_tide",
        "live_mean": 0.25494999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.2040000000000001,
        "feature": "event",
        "live_mean": 0.2040000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.04200000000000001,
        "feature": "oi_change",
        "live_mean": 0.04200000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.036000000000000004,
        "feature": "ftd_pressure",
        "live_mean": 0.036000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.030000000000000016,
        "feature": "squeeze_score",
        "live_mean": 0.030000000000000016,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.018000000000000002,
        "feature": "iv_rank",
        "live_mean": 0.018000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "PFE",
    "top_feature_mean_deltas": [
      {
        "delta": -3.0,
        "feature": "flow",
        "live_mean": 3.0,
        "shadow_mean": null
      },
      {
        "delta": -0.8641249999999999,
        "feature": "freshness_factor",
        "live_mean": 0.8641249999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.25225,
        "feature": "market_tide",
        "live_mean": 0.25225,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.041999999999999996,
        "feature": "oi_change",
        "live_mean": 0.041999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.03,
        "feature": "squeeze_score",
        "live_mean": 0.03,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "BAC",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.95875,
        "feature": "freshness_factor",
        "live_mean": 0.95875,
        "shadow_mean": null
      },
      {
        "delta": -0.25850000000000006,
        "feature": "market_tide",
        "live_mean": 0.25850000000000006,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.11975,
        "feature": "oi_change",
        "live_mean": 0.11975,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.06599999999999999,
        "feature": "greeks_gamma",
        "live_mean": 0.06599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.06,
        "feature": "iv_rank",
        "live_mean": 0.06,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.016499999999999997,
        "feature": "squeeze_score",
        "live_mean": 0.016499999999999997,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "HOOD",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9617272727272727,
        "feature": "freshness_factor",
        "live_mean": 0.9617272727272727,
        "shadow_mean": null
      },
      {
        "delta": -0.25236363636363635,
        "feature": "market_tide",
        "live_mean": 0.25236363636363635,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000001,
        "feature": "event",
        "live_mean": 0.20400000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000002,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.017999999999999995,
        "feature": "iv_rank",
        "live_mean": 0.017999999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000002,
        "feature": "regime",
        "live_mean": 0.008000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000001,
        "feature": "smile",
        "live_mean": 0.004000000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "V",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.949,
        "feature": "freshness_factor",
        "live_mean": 0.949,
        "shadow_mean": null
      },
      {
        "delta": -0.252375,
        "feature": "market_tide",
        "live_mean": 0.252375,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.020999999999999998,
        "feature": "oi_change",
        "live_mean": 0.020999999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "IWM",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5714285714285716,
        "feature": "flow",
        "live_mean": 2.5714285714285716,
        "shadow_mean": null
      },
      {
        "delta": -0.9675,
        "feature": "freshness_factor",
        "live_mean": 0.9675,
        "shadow_mean": null
      },
      {
        "delta": -0.2541428571428571,
        "feature": "market_tide",
        "live_mean": 0.2541428571428571,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000004,
        "feature": "event",
        "live_mean": 0.20400000000000004,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.048,
        "feature": "greeks_gamma",
        "live_mean": 0.048,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.023,
        "feature": "dark_pool",
        "live_mean": 0.023,
        "shadow_mean": null
      },
      {
        "delta": -0.017999999999999995,
        "feature": "iv_rank",
        "live_mean": 0.017999999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.013285714285714288,
        "feature": "squeeze_score",
        "live_mean": 0.013285714285714288,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "etf_flow",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "MSFT",
    "top_feature_mean_deltas": [
      {
        "delta": -2.7,
        "feature": "flow",
        "live_mean": 2.7,
        "shadow_mean": null
      },
      {
        "delta": -0.9810000000000001,
        "feature": "freshness_factor",
        "live_mean": 0.9810000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.2524,
        "feature": "market_tide",
        "live_mean": 0.2524,
        "shadow_mean": null
      },
      {
        "delta": -0.21000000000000002,
        "feature": "oi_change",
        "live_mean": 0.21000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000001,
        "feature": "event",
        "live_mean": 0.20400000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": 0.12,
        "feature": "iv_rank",
        "live_mean": -0.12,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.048,
        "feature": "greeks_gamma",
        "live_mean": 0.048,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.023,
        "feature": "dark_pool",
        "live_mean": 0.023,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "etf_flow",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.012,
        "feature": "squeeze_score",
        "live_mean": 0.012,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "SOFI",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9870000000000001,
        "feature": "freshness_factor",
        "live_mean": 0.9870000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.2526,
        "feature": "market_tide",
        "live_mean": 0.2526,
        "shadow_mean": null
      },
      {
        "delta": -0.21000000000000002,
        "feature": "oi_change",
        "live_mean": 0.21000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000001,
        "feature": "event",
        "live_mean": 0.20400000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000002,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.0624,
        "feature": "greeks_gamma",
        "live_mean": 0.0624,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.017999999999999995,
        "feature": "iv_rank",
        "live_mean": 0.017999999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000002,
        "feature": "regime",
        "live_mean": 0.008000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000001,
        "feature": "smile",
        "live_mean": 0.004000000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "SPY",
    "top_feature_mean_deltas": [
      {
        "delta": -2.9,
        "feature": "flow",
        "live_mean": 2.9,
        "shadow_mean": null
      },
      {
        "delta": -0.9062,
        "feature": "freshness_factor",
        "live_mean": 0.9062,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000007,
        "feature": "event",
        "live_mean": 0.20400000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.19513333333333335,
        "feature": "market_tide",
        "live_mean": 0.19513333333333335,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": 0.13,
        "feature": "toxicity_correlation_penalty",
        "live_mean": -0.13,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.06360000000000003,
        "feature": "iv_skew",
        "live_mean": 0.06360000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.042,
        "feature": "oi_change",
        "live_mean": 0.042,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.02640000000000001,
        "feature": "squeeze_score",
        "live_mean": 0.02640000000000001,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000003,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000003,
        "shadow_mean": null
      },
      {
        "delta": -0.018,
        "feature": "iv_rank",
        "live_mean": 0.018,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000002,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "greeks_gamma",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "INTC",
    "top_feature_mean_deltas": [
      {
        "delta": -2.625,
        "feature": "flow",
        "live_mean": 2.625,
        "shadow_mean": null
      },
      {
        "delta": -0.9805,
        "feature": "freshness_factor",
        "live_mean": 0.9805,
        "shadow_mean": null
      },
      {
        "delta": -0.25225,
        "feature": "market_tide",
        "live_mean": 0.25225,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.204,
        "feature": "event",
        "live_mean": 0.204,
        "shadow_mean": null
      },
      {
        "delta": 0.162,
        "feature": "toxicity_penalty",
        "live_mean": -0.162,
        "shadow_mean": null
      },
      {
        "delta": 0.12,
        "feature": "iv_rank",
        "live_mean": -0.12,
        "shadow_mean": null
      },
      {
        "delta": -0.075,
        "feature": "insider",
        "live_mean": 0.075,
        "shadow_mean": null
      },
      {
        "delta": -0.07,
        "feature": "iv_skew",
        "live_mean": 0.07,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.036,
        "feature": "ftd_pressure",
        "live_mean": 0.036,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008,
        "feature": "regime",
        "live_mean": 0.008,
        "shadow_mean": null
      },
      {
        "delta": -0.004,
        "feature": "smile",
        "live_mean": 0.004,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "PLTR",
    "top_feature_mean_deltas": [
      {
        "delta": -2.6363636363636362,
        "feature": "flow",
        "live_mean": 2.6363636363636362,
        "shadow_mean": null
      },
      {
        "delta": -0.9853636363636362,
        "feature": "freshness_factor",
        "live_mean": 0.9853636363636362,
        "shadow_mean": null
      },
      {
        "delta": -0.2525454545454546,
        "feature": "market_tide",
        "live_mean": 0.2525454545454546,
        "shadow_mean": null
      },
      {
        "delta": -0.21,
        "feature": "oi_change",
        "live_mean": 0.21,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000001,
        "feature": "event",
        "live_mean": 0.20400000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000002,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.017999999999999995,
        "feature": "iv_rank",
        "live_mean": 0.017999999999999995,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000002,
        "feature": "regime",
        "live_mean": 0.008000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000001,
        "feature": "smile",
        "live_mean": 0.004000000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "TSLA",
    "top_feature_mean_deltas": [
      {
        "delta": -2.9,
        "feature": "flow",
        "live_mean": 2.9,
        "shadow_mean": null
      },
      {
        "delta": -0.9878,
        "feature": "freshness_factor",
        "live_mean": 0.9878,
        "shadow_mean": null
      },
      {
        "delta": -0.2524,
        "feature": "market_tide",
        "live_mean": 0.2524,
        "shadow_mean": null
      },
      {
        "delta": -0.21000000000000002,
        "feature": "oi_change",
        "live_mean": 0.21000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000001,
        "feature": "event",
        "live_mean": 0.20400000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.12000000000000002,
        "feature": "iv_rank",
        "live_mean": 0.12000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000002,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.047999999999999994,
        "feature": "greeks_gamma",
        "live_mean": 0.047999999999999994,
        "shadow_mean": null
      },
      {
        "delta": -0.03599999999999999,
        "feature": "ftd_pressure",
        "live_mean": 0.03599999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.022999999999999996,
        "feature": "dark_pool",
        "live_mean": 0.022999999999999996,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "etf_flow",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.011999999999999999,
        "feature": "squeeze_score",
        "live_mean": 0.011999999999999999,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000002,
        "feature": "regime",
        "live_mean": 0.008000000000000002,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000001,
        "feature": "smile",
        "live_mean": 0.004000000000000001,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  },
  {
    "symbol": "LCID",
    "top_feature_mean_deltas": [
      {
        "delta": -2.5,
        "feature": "flow",
        "live_mean": 2.5,
        "shadow_mean": null
      },
      {
        "delta": -0.9707222222222222,
        "feature": "freshness_factor",
        "live_mean": 0.9707222222222222,
        "shadow_mean": null
      },
      {
        "delta": -0.25255555555555553,
        "feature": "market_tide",
        "live_mean": 0.25255555555555553,
        "shadow_mean": null
      },
      {
        "delta": -0.20400000000000007,
        "feature": "event",
        "live_mean": 0.20400000000000007,
        "shadow_mean": null
      },
      {
        "delta": 0.16199999999999998,
        "feature": "toxicity_penalty",
        "live_mean": -0.16199999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.11988888888888893,
        "feature": "oi_change",
        "live_mean": 0.11988888888888893,
        "shadow_mean": null
      },
      {
        "delta": -0.07499999999999998,
        "feature": "insider",
        "live_mean": 0.07499999999999998,
        "shadow_mean": null
      },
      {
        "delta": -0.07000000000000003,
        "feature": "iv_skew",
        "live_mean": 0.07000000000000003,
        "shadow_mean": null
      },
      {
        "delta": 0.060000000000000026,
        "feature": "iv_rank",
        "live_mean": -0.060000000000000026,
        "shadow_mean": null
      },
      {
        "delta": -0.056,
        "feature": "greeks_gamma",
        "live_mean": 0.056,
        "shadow_mean": null
      },
      {
        "delta": -0.036000000000000004,
        "feature": "ftd_pressure",
        "live_mean": 0.036000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.023000000000000007,
        "feature": "dark_pool",
        "live_mean": 0.023000000000000007,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "etf_flow",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.012000000000000004,
        "feature": "squeeze_score",
        "live_mean": 0.012000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.008000000000000004,
        "feature": "regime",
        "live_mean": 0.008000000000000004,
        "shadow_mean": null
      },
      {
        "delta": -0.004000000000000002,
        "feature": "smile",
        "live_mean": 0.004000000000000002,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "calendar",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "congress",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "institutional",
        "live_mean": 0.0,
        "shadow_mean": null
      },
      {
        "delta": 0.0,
        "feature": "motif_bonus",
        "live_mean": 0.0,
        "shadow_mean": null
      }
    ]
  }
]
```

### All signals (distinct, live vs shadow)
```
{
  "live": [
    "calendar",
    "congress",
    "dark_pool",
    "etf_flow",
    "event",
    "flow",
    "freshness_factor",
    "ftd_pressure",
    "greeks_gamma",
    "insider",
    "institutional",
    "iv_rank",
    "iv_skew",
    "market_tide",
    "motif_bonus",
    "oi_change",
    "regime",
    "shorts_squeeze",
    "smile",
    "squeeze_score",
    "toxicity_correlation_penalty",
    "toxicity_penalty",
    "whale"
  ],
  "shadow": []
}
```

### All exit attributions (today)
```
[
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:33:46.295980+00:00",
    "attribution_components": [
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_flow_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_darkpool_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_sentiment_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.00644,
        "signal_id": "exit_score_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_regime_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_sector_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_vol_expansion",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_thesis_invalidated",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_earnings_risk",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_overnight_flow_risk",
        "source": "exit"
      }
    ],
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "BLK|LONG|1777578590",
    "composite_at_entry": 4.015,
    "composite_at_exit": 3.831,
    "composite_components_at_entry": {},
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_BLK_2026-05-01T13-33-45.8730",
    "direction": "unknown",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.001642006048054566,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.001642006048054566
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.001642006048054566,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.16420060480545662,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": -0.0007691379622368204,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.0025148741338723115,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5131745172351562
          },
          "posture": "long",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 1.0,
          "regime_label": "bull",
          "regime_source": "structural_regime:RISK_ON",
          "structural_confidence": 1.0,
          "structural_regime": "RISK_ON",
          "ts": "2026-04-30T16:11:49.674674+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T16:16:33.934410+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 34.122,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:33:46.150474+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -0.184,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 0,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "UNRESOLVED_ENTRY_OID:BLK|LONG|1777578590",
    "entry_price": 1062.633333,
    "entry_regime": "unknown",
    "entry_sector_profile": {
      "sector": "UNKNOWN"
    },
    "entry_timestamp": "2026-04-30T19:49:50.793629+00:00",
    "entry_ts": "2026-04-30T19:49:50.793629+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.00644,
        "normalized_value": 0.023,
        "raw_value": 0.023
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "110ba80c-8cb4-468a-bf57-bca505662fc8",
    "exit_price": 1067.25,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": true
      },
      "mae": null,
      "mfe": 4.366667,
      "post_exit_excursion": null,
      "profit_giveback": 0.0,
      "realized_pnl_price": 4.616667,
      "time_in_trade_sec": 63835.08
    },
    "exit_reason": "stale_alpha_cutoff(1059min,0.00%)",
    "exit_reason_code": "hold",
    "exit_regime": "NEUTRAL",
    "exit_regime_context": {},
    "exit_regime_decision": "normal",
    "exit_regime_reason": "",
    "exit_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 1.0,
        "flow_weight": 1.0,
        "short_interest_weight": 1.0
      },
      "sector": "UNKNOWN",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "exit_ts": "2026-05-01T13:33:45.873049+00:00",
    "exit_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "110ba80c-8cb4-468a-bf57-bca505662fc8",
    "pnl": 4.62,
    "pnl_pct": 0.434455,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "NEUTRAL",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.18399999999999972,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "BLK",
    "time_in_trade_minutes": 1063.9179903333334,
    "timestamp": "2026-05-01T13:33:45.873049+00:00",
    "trade_id": "open_BLK_2026-04-30T19:49:50.793629+00:00",
    "trade_key": "BLK|LONG|1777578590",
    "v2_exit_components": {
      "darkpool_deterioration": 0.0,
      "earnings_risk": 0.0,
      "flow_deterioration": 0.0,
      "overnight_flow_risk": 0.0,
      "regime_shift": 0.0,
      "score_deterioration": 0.023,
      "sector_shift": 0.0,
      "sentiment_deterioration": 0.0,
      "thesis_invalidated": 0.0,
      "vol_expansion": 0.0
    },
    "v2_exit_score": 0.006439999999999991,
    "variant_id": "B2_live_paper"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:34:34.303625+00:00",
    "attribution_components": null,
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "JPM|LONG|1777578869",
    "composite_at_entry": 3.96,
    "composite_at_exit": 0.0,
    "composite_components_at_entry": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.986,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.12,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.061,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_JPM_2026-05-01T13-34-34.1834",
    "direction": "bullish",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.008942063866983794,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "down",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.008942063866983794
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.008942063866983794,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.8942063866983794,
          "premarket_sentiment": "bearish",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "down",
            "qqq_overnight_ret": -0.008766811782834253,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.009117315951133334,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5107985480943739
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-04-30T19:50:20.280442+00:00"
        },
        "sector_intel": {
          "sector": "FINANCIALS",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T19:54:29.604931+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 33.774,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "FINANCIALS",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:34:34.184250+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -3.96,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "a31f1b51-5ed9-4abe-a627-8ee863ded8d4",
    "entry_price": 313.53,
    "entry_regime": "NEUTRAL",
    "entry_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 0.9,
        "flow_weight": 1.0,
        "short_interest_weight": 0.9
      },
      "sector": "FINANCIALS",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "entry_timestamp": "2026-04-30T19:54:29.015419+00:00",
    "entry_ts": "2026-04-30T19:54:29.015419+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "28490a4e-c381-4aad-a181-3e0cba72fc88",
    "exit_price": 312.9,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": false
      },
      "mae": null,
      "mfe": 0.0,
      "post_exit_excursion": null,
      "profit_giveback": null,
      "realized_pnl_price": -0.63,
      "time_in_trade_sec": 63605.17
    },
    "exit_reason": "underwater_time_decay_stop",
    "exit_reason_code": "other",
    "exit_regime": "mixed",
    "exit_regime_context": {
      "max_minutes": 60.0,
      "pnl_pct": -0.00041
    },
    "exit_regime_decision": "normal",
    "exit_regime_reason": "underwater_time_decay_stop",
    "exit_sector_profile": {
      "sector": "UNKNOWN"
    },
    "exit_ts": "2026-05-01T13:34:34.183410+00:00",
    "exit_uw": {},
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "28490a4e-c381-4aad-a181-3e0cba72fc88",
    "pnl": -0.63,
    "pnl_pct": -0.200938,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "MIXED",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.0,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "JPM",
    "time_in_trade_minutes": 1060.0861331833335,
    "timestamp": "2026-05-01T13:34:34.183410+00:00",
    "trade_id": "open_JPM_2026-04-30T19:54:29.015419+00:00",
    "trade_key": "JPM|LONG|1777578869",
    "v2_exit_components": {},
    "v2_exit_score": 0.0,
    "variant_id": "paper_aggressive"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:35:05.230816+00:00",
    "attribution_components": null,
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "TGT|LONG|1777578979",
    "composite_at_entry": 3.929,
    "composite_at_exit": 0.0,
    "composite_components_at_entry": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.971,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.12,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.021,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_TGT_2026-05-01T13-35-05.0947",
    "direction": "bullish",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.008942063866983794,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "down",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.008942063866983794
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.008942063866983794,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.8942063866983794,
          "premarket_sentiment": "bearish",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "down",
            "qqq_overnight_ret": -0.008766811782834253,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.009117315951133334,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5107985480943739
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-04-30T19:50:20.280442+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T19:56:21.503934+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 33.774,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:35:05.095647+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -3.929,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 0,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "dc2731bd-e462-418a-a95c-a08514beb205",
    "entry_price": 129.48,
    "entry_regime": "NEUTRAL",
    "entry_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 1.0,
        "flow_weight": 1.0,
        "short_interest_weight": 1.0
      },
      "sector": "UNKNOWN",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "entry_timestamp": "2026-04-30T19:56:19.608582+00:00",
    "entry_ts": "2026-04-30T19:56:19.608582+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "7f29828a-15d5-4a99-9ff5-ad7cc9910b8e",
    "exit_price": 129.57,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": true
      },
      "mae": null,
      "mfe": 0.0,
      "post_exit_excursion": null,
      "profit_giveback": null,
      "realized_pnl_price": 0.09,
      "time_in_trade_sec": 63525.49
    },
    "exit_reason": "underwater_time_decay_stop",
    "exit_reason_code": "other",
    "exit_regime": "mixed",
    "exit_regime_context": {
      "max_minutes": 60.0,
      "pnl_pct": -0.00278
    },
    "exit_regime_decision": "normal",
    "exit_regime_reason": "underwater_time_decay_stop",
    "exit_sector_profile": {
      "sector": "UNKNOWN"
    },
    "exit_ts": "2026-05-01T13:35:05.094777+00:00",
    "exit_uw": {},
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "7f29828a-15d5-4a99-9ff5-ad7cc9910b8e",
    "pnl": 0.27,
    "pnl_pct": 0.069509,
    "position_side": "long",
    "qty": 3.0,
    "regime_label": "MIXED",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.0,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "TGT",
    "time_in_trade_minutes": 1058.75810325,
    "timestamp": "2026-05-01T13:35:05.094777+00:00",
    "trade_id": "open_TGT_2026-04-30T19:56:19.608582+00:00",
    "trade_key": "TGT|LONG|1777578979",
    "v2_exit_components": {},
    "v2_exit_score": 0.0,
    "variant_id": "paper_aggressive"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:35:35.965657+00:00",
    "attribution_components": [
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_flow_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_darkpool_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_sentiment_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.033376,
        "signal_id": "exit_score_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_regime_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.05,
        "signal_id": "exit_sector_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_vol_expansion",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_thesis_invalidated",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_earnings_risk",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_overnight_flow_risk",
        "source": "exit"
      }
    ],
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "TSLA|LONG|1777579245",
    "composite_at_entry": 5.028,
    "composite_at_exit": 4.074,
    "composite_components_at_entry": {},
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_TSLA_2026-05-01T13-35-35.5766",
    "direction": "unknown",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.001642006048054566,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.001642006048054566
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.001642006048054566,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.16420060480545662,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": -0.0007691379622368204,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.0025148741338723115,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5131745172351562
          },
          "posture": "long",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 1.0,
          "regime_label": "bull",
          "regime_source": "structural_regime:RISK_ON",
          "structural_confidence": 1.0,
          "structural_regime": "RISK_ON",
          "ts": "2026-04-30T16:11:49.674674+00:00"
        },
        "sector_intel": {
          "sector": "TECH",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T16:12:24.155771+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 34.122,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "TECH",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:35:35.831940+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -0.954,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "UNRESOLVED_ENTRY_OID:TSLA|LONG|1777579245",
    "entry_price": 381.68,
    "entry_regime": "unknown",
    "entry_sector_profile": {
      "sector": "UNKNOWN"
    },
    "entry_timestamp": "2026-04-30T20:00:45.829762+00:00",
    "entry_ts": "2026-04-30T20:00:45.829762+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.033376,
        "normalized_value": 0.1192,
        "raw_value": 0.1192
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.05,
        "normalized_value": 1.0,
        "raw_value": 1.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "1d32238d-bf1f-480f-af73-a5bc5dc0743a",
    "exit_price": 382.45,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": true
      },
      "mae": null,
      "mfe": 1.08,
      "post_exit_excursion": null,
      "profit_giveback": 0.287037,
      "realized_pnl_price": 0.77,
      "time_in_trade_sec": 63289.75
    },
    "exit_reason": "stale_alpha_cutoff(1048min,0.00%)",
    "exit_reason_code": "hold",
    "exit_regime": "NEUTRAL",
    "exit_regime_context": {},
    "exit_regime_decision": "normal",
    "exit_regime_reason": "",
    "exit_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.1,
        "earnings_weight": 1.0,
        "flow_weight": 1.2,
        "short_interest_weight": 0.8
      },
      "sector": "TECH",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "exit_ts": "2026-05-01T13:35:35.576616+00:00",
    "exit_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "1d32238d-bf1f-480f-af73-a5bc5dc0743a",
    "pnl": 0.77,
    "pnl_pct": 0.20174,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "NEUTRAL",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.9539999999999997,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "TSLA",
    "time_in_trade_minutes": 1054.8291142333333,
    "timestamp": "2026-05-01T13:35:35.576616+00:00",
    "trade_id": "open_TSLA_2026-04-30T20:00:45.829762+00:00",
    "trade_key": "TSLA|LONG|1777579245",
    "v2_exit_components": {
      "darkpool_deterioration": 0.0,
      "earnings_risk": 0.0,
      "flow_deterioration": 0.0,
      "overnight_flow_risk": 0.0,
      "regime_shift": 0.0,
      "score_deterioration": 0.1192,
      "sector_shift": 1.0,
      "sentiment_deterioration": 0.0,
      "thesis_invalidated": 0.0,
      "vol_expansion": 0.0
    },
    "v2_exit_score": 0.08338999999999999,
    "variant_id": "B2_live_paper"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:36:08.109291+00:00",
    "attribution_components": [
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_flow_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_darkpool_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_sentiment_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.01274,
        "signal_id": "exit_score_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_regime_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.05,
        "signal_id": "exit_sector_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.02591,
        "signal_id": "exit_vol_expansion",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_thesis_invalidated",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_earnings_risk",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_overnight_flow_risk",
        "source": "exit"
      }
    ],
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "MS|LONG|1777579245",
    "composite_at_entry": 4.354,
    "composite_at_exit": 3.99,
    "composite_components_at_entry": {},
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_MS_2026-05-01T13-36-07.7576",
    "direction": "unknown",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.001642006048054566,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.001642006048054566
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.001642006048054566,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.16420060480545662,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": -0.0007691379622368204,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.0025148741338723115,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5131745172351562
          },
          "posture": "long",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 1.0,
          "regime_label": "bull",
          "regime_source": "structural_regime:RISK_ON",
          "structural_confidence": 1.0,
          "structural_regime": "RISK_ON",
          "ts": "2026-04-30T16:11:49.674674+00:00"
        },
        "sector_intel": {
          "sector": "FINANCIALS",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T16:13:51.218308+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 34.122,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "FINANCIALS",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:36:07.983984+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -0.364,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "UNRESOLVED_ENTRY_OID:MS|LONG|1777579245",
    "entry_price": 189.838,
    "entry_regime": "unknown",
    "entry_sector_profile": {
      "sector": "UNKNOWN"
    },
    "entry_timestamp": "2026-04-30T20:00:45.830826+00:00",
    "entry_ts": "2026-04-30T20:00:45.830826+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.01274,
        "normalized_value": 0.0455,
        "raw_value": 0.0455
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.05,
        "normalized_value": 1.0,
        "raw_value": 1.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.05182,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "f5a3c47b-9355-4cd0-8f91-d9c27f123c96",
    "exit_price": 190.39,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": true
      },
      "mae": null,
      "mfe": 0.572,
      "post_exit_excursion": null,
      "profit_giveback": 0.034965,
      "realized_pnl_price": 0.552,
      "time_in_trade_sec": 63321.93
    },
    "exit_reason": "stale_alpha_cutoff(1048min,0.00%)",
    "exit_reason_code": "hold",
    "exit_regime": "NEUTRAL",
    "exit_regime_context": {},
    "exit_regime_decision": "normal",
    "exit_regime_reason": "",
    "exit_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 0.9,
        "flow_weight": 1.0,
        "short_interest_weight": 0.9
      },
      "sector": "FINANCIALS",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "exit_ts": "2026-05-01T13:36:07.757632+00:00",
    "exit_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "f5a3c47b-9355-4cd0-8f91-d9c27f123c96",
    "pnl": 0.55,
    "pnl_pct": 0.290774,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "NEUTRAL",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.3639999999999999,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "MS",
    "time_in_trade_minutes": 1055.3654467666668,
    "timestamp": "2026-05-01T13:36:07.757632+00:00",
    "trade_id": "open_MS_2026-04-30T20:00:45.830826+00:00",
    "trade_key": "MS|LONG|1777579245",
    "v2_exit_components": {
      "darkpool_deterioration": 0.0,
      "earnings_risk": 0.0,
      "flow_deterioration": 0.0,
      "overnight_flow_risk": 0.0,
      "regime_shift": 0.0,
      "score_deterioration": 0.0455,
      "sector_shift": 1.0,
      "sentiment_deterioration": 0.0,
      "thesis_invalidated": 0.0,
      "vol_expansion": 0.2591
    },
    "v2_exit_score": 0.08864720000000002,
    "variant_id": "B2_live_paper"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:36:38.041215+00:00",
    "attribution_components": [
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_flow_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_darkpool_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_sentiment_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.01302,
        "signal_id": "exit_score_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_regime_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.05,
        "signal_id": "exit_sector_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.04114,
        "signal_id": "exit_vol_expansion",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_thesis_invalidated",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_earnings_risk",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_overnight_flow_risk",
        "source": "exit"
      }
    ],
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "PLTR|LONG|1777579245",
    "composite_at_entry": 4.508,
    "composite_at_exit": 4.136,
    "composite_components_at_entry": {},
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_PLTR_2026-05-01T13-36-37.5280",
    "direction": "unknown",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.001642006048054566,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.001642006048054566
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.001642006048054566,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.16420060480545662,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": -0.0007691379622368204,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.0025148741338723115,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5131745172351562
          },
          "posture": "long",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 1.0,
          "regime_label": "bull",
          "regime_source": "structural_regime:RISK_ON",
          "structural_confidence": 1.0,
          "structural_regime": "RISK_ON",
          "ts": "2026-04-30T16:11:49.674674+00:00"
        },
        "sector_intel": {
          "sector": "TECH",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T16:14:06.801863+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 34.122,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "TECH",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:36:37.873863+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -0.372,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "UNRESOLVED_ENTRY_OID:PLTR|LONG|1777579245",
    "entry_price": 139.21625,
    "entry_regime": "unknown",
    "entry_sector_profile": {
      "sector": "UNKNOWN"
    },
    "entry_timestamp": "2026-04-30T20:00:45.831729+00:00",
    "entry_ts": "2026-04-30T20:00:45.831729+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.01302,
        "normalized_value": 0.0465,
        "raw_value": 0.0465
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.05,
        "normalized_value": 1.0,
        "raw_value": 1.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.08228,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "49bf995d-c7c3-40f7-a15f-41c3db9a6a51",
    "exit_price": 145.75,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": true
      },
      "mae": null,
      "mfe": 3.84375,
      "post_exit_excursion": null,
      "profit_giveback": 0.0,
      "realized_pnl_price": 6.53375,
      "time_in_trade_sec": 63351.7
    },
    "exit_reason": "stale_alpha_cutoff(1048min,0.03%)",
    "exit_reason_code": "hold",
    "exit_regime": "NEUTRAL",
    "exit_regime_context": {},
    "exit_regime_decision": "normal",
    "exit_regime_reason": "",
    "exit_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.1,
        "earnings_weight": 1.0,
        "flow_weight": 1.2,
        "short_interest_weight": 0.8
      },
      "sector": "TECH",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "exit_ts": "2026-05-01T13:36:37.528097+00:00",
    "exit_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "49bf995d-c7c3-40f7-a15f-41c3db9a6a51",
    "pnl": 6.53,
    "pnl_pct": 4.693238,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "NEUTRAL",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.3719999999999999,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "PLTR",
    "time_in_trade_minutes": 1055.8616061333332,
    "timestamp": "2026-05-01T13:36:37.528097+00:00",
    "trade_id": "open_PLTR_2026-04-30T20:00:45.831729+00:00",
    "trade_key": "PLTR|LONG|1777579245",
    "v2_exit_components": {
      "darkpool_deterioration": 0.0,
      "earnings_risk": 0.0,
      "flow_deterioration": 0.0,
      "overnight_flow_risk": 0.0,
      "regime_shift": 0.0,
      "score_deterioration": 0.0465,
      "sector_shift": 1.0,
      "sentiment_deterioration": 0.0,
      "thesis_invalidated": 0.0,
      "vol_expansion": 0.4114
    },
    "v2_exit_score": 0.104162,
    "variant_id": "B2_live_paper"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:38:25.536178+00:00",
    "attribution_components": null,
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "AMD|LONG|1777578028",
    "composite_at_entry": 4.441,
    "composite_at_exit": 0.0,
    "composite_components_at_entry": {},
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_AMD_2026-05-01T13-38-25.2199",
    "direction": "unknown",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.001642006048054566,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.001642006048054566
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.001642006048054566,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.16420060480545662,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": -0.0007691379622368204,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.0025148741338723115,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5131745172351562
          },
          "posture": "long",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 1.0,
          "regime_label": "bull",
          "regime_source": "structural_regime:RISK_ON",
          "structural_confidence": 1.0,
          "structural_regime": "RISK_ON",
          "ts": "2026-04-30T16:11:49.674674+00:00"
        },
        "sector_intel": {
          "sector": "TECH",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T16:12:40.196803+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 34.122,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "TECH",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:38:25.389733+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -4.441,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 0,
      "delta_sector_strength": 0,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "UNRESOLVED_ENTRY_OID:AMD|LONG|1777578028",
    "entry_price": 355.64,
    "entry_regime": "unknown",
    "entry_sector_profile": {
      "sector": "UNKNOWN"
    },
    "entry_timestamp": "2026-04-30T19:40:28.854691+00:00",
    "entry_ts": "2026-04-30T19:40:28.854691+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "41173c06-63b0-4d56-8882-c1238061e66f",
    "exit_price": 355.08,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": false
      },
      "mae": null,
      "mfe": 0.0,
      "post_exit_excursion": null,
      "profit_giveback": null,
      "realized_pnl_price": -0.56,
      "time_in_trade_sec": 64676.37
    },
    "exit_reason": "underwater_time_decay_stop",
    "exit_reason_code": "other",
    "exit_regime": "unknown",
    "exit_regime_context": {
      "max_minutes": 60.0,
      "pnl_pct": -0.00252
    },
    "exit_regime_decision": "normal",
    "exit_regime_reason": "underwater_time_decay_stop",
    "exit_sector_profile": {
      "sector": "UNKNOWN"
    },
    "exit_ts": "2026-05-01T13:38:25.219989+00:00",
    "exit_uw": {},
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "41173c06-63b0-4d56-8882-c1238061e66f",
    "pnl": -0.56,
    "pnl_pct": -0.157463,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "UNKNOWN",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.0,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "AMD",
    "time_in_trade_minutes": 1077.9394216333333,
    "timestamp": "2026-05-01T13:38:25.219989+00:00",
    "trade_id": "open_AMD_2026-04-30T19:40:28.854691+00:00",
    "trade_key": "AMD|LONG|1777578028",
    "v2_exit_components": {},
    "v2_exit_score": 0.0,
    "variant_id": "B2_live_paper"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:38:32.091241+00:00",
    "attribution_components": [
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_flow_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_darkpool_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_sentiment_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.012628,
        "signal_id": "exit_score_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_regime_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_sector_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.01669,
        "signal_id": "exit_vol_expansion",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_thesis_invalidated",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_earnings_risk",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_overnight_flow_risk",
        "source": "exit"
      }
    ],
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "GS|LONG|1777578183",
    "composite_at_entry": 4.273,
    "composite_at_exit": 3.912,
    "composite_components_at_entry": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.987,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.024,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.021,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_GS_2026-05-01T13-38-31.9462",
    "direction": "bullish",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.008511533671702702,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "down",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.008511533671702702
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.008511533671702702,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.8511533671702702,
          "premarket_sentiment": "bearish",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "down",
            "qqq_overnight_ret": -0.008381100618106036,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.008641966725299367,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5116173534216736
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-04-30T19:40:48.571024+00:00"
        },
        "sector_intel": {
          "sector": "FINANCIALS",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T19:43:04.046563+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 33.821999999999996,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "FINANCIALS",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:38:31.947078+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -0.361,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 0,
      "delta_sector_strength": 0,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "b73a9726-b047-49ab-a3cb-a1c3fc8dad1e",
    "entry_price": 919.23,
    "entry_regime": "NEUTRAL",
    "entry_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 0.9,
        "flow_weight": 1.0,
        "short_interest_weight": 0.9
      },
      "sector": "FINANCIALS",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "entry_timestamp": "2026-04-30T19:43:03.382692+00:00",
    "entry_ts": "2026-04-30T19:43:03.382692+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.012628,
        "normalized_value": 0.0451,
        "raw_value": 0.0451
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.03338,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "6e7c880f-107a-44b6-a4ae-1a81c40d3c8f",
    "exit_price": 921.0,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": true,
        "saved_loss": true
      },
      "mae": null,
      "mfe": 3.72,
      "post_exit_excursion": null,
      "profit_giveback": 0.524194,
      "realized_pnl_price": 1.77,
      "time_in_trade_sec": 64528.56
    },
    "exit_reason": "stale_alpha_cutoff(1075min,0.00%)",
    "exit_reason_code": "hold",
    "exit_regime": "NEUTRAL",
    "exit_regime_context": {},
    "exit_regime_decision": "normal",
    "exit_regime_reason": "",
    "exit_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 0.9,
        "flow_weight": 1.0,
        "short_interest_weight": 0.9
      },
      "sector": "FINANCIALS",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "exit_ts": "2026-05-01T13:38:31.946213+00:00",
    "exit_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "6e7c880f-107a-44b6-a4ae-1a81c40d3c8f",
    "pnl": 1.77,
    "pnl_pct": 0.192552,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "NEUTRAL",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.36099999999999977,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "GS",
    "time_in_trade_minutes": 1075.4760586833333,
    "timestamp": "2026-05-01T13:38:31.946213+00:00",
    "trade_id": "open_GS_2026-04-30T19:43:03.382692+00:00",
    "trade_key": "GS|LONG|1777578183",
    "v2_exit_components": {
      "darkpool_deterioration": 0.0,
      "earnings_risk": 0.0,
      "flow_deterioration": 0.0,
      "overnight_flow_risk": 0.0,
      "regime_shift": 0.0,
      "score_deterioration": 0.0451,
      "sector_shift": 0.0,
      "sentiment_deterioration": 0.0,
      "thesis_invalidated": 0.0,
      "vol_expansion": 0.1669
    },
    "v2_exit_score": 0.029321799999999995,
    "variant_id": "paper_aggressive"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:38:36.295539+00:00",
    "attribution_components": null,
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "IWM|LONG|1777578525",
    "composite_at_entry": 3.7769999999999997,
    "composite_at_exit": 0.0,
    "composite_components_at_entry": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.924,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.048,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.21,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_IWM_2026-05-01T13-38-36.1326",
    "direction": "bullish",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.008511533671702702,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "down",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.008511533671702702
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.008511533671702702,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.8511533671702702,
          "premarket_sentiment": "bearish",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "down",
            "qqq_overnight_ret": -0.008381100618106036,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.008641966725299367,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5116173534216736
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-04-30T19:40:48.571024+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T19:48:46.580913+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 33.821999999999996,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:38:36.133916+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -3.777,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 0,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "5bec2876-60e6-493b-895b-9ee925834654",
    "entry_price": 277.79,
    "entry_regime": "NEUTRAL",
    "entry_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 1.0,
        "flow_weight": 1.0,
        "short_interest_weight": 1.0
      },
      "sector": "UNKNOWN",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "entry_timestamp": "2026-04-30T19:48:45.153610+00:00",
    "entry_ts": "2026-04-30T19:48:45.153610+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "cc9f2f4b-06e1-4183-bae0-92d2f3d43e06",
    "exit_price": 277.35,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": false
      },
      "mae": null,
      "mfe": 0.0,
      "post_exit_excursion": null,
      "profit_giveback": null,
      "realized_pnl_price": -0.44,
      "time_in_trade_sec": 64190.98
    },
    "exit_reason": "underwater_time_decay_stop",
    "exit_reason_code": "other",
    "exit_regime": "mixed",
    "exit_regime_context": {
      "max_minutes": 60.0,
      "pnl_pct": -0.00054
    },
    "exit_regime_decision": "normal",
    "exit_regime_reason": "underwater_time_decay_stop",
    "exit_sector_profile": {
      "sector": "UNKNOWN"
    },
    "exit_ts": "2026-05-01T13:38:36.132647+00:00",
    "exit_uw": {},
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "cc9f2f4b-06e1-4183-bae0-92d2f3d43e06",
    "pnl": -0.44,
    "pnl_pct": -0.158393,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "MIXED",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.0,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "IWM",
    "time_in_trade_minutes": 1069.8496506166666,
    "timestamp": "2026-05-01T13:38:36.132647+00:00",
    "trade_id": "open_IWM_2026-04-30T19:48:45.153610+00:00",
    "trade_key": "IWM|LONG|1777578525",
    "v2_exit_components": {},
    "v2_exit_score": 0.0,
    "variant_id": "paper_aggressive"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:38:40.942156+00:00",
    "attribution_components": [
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_flow_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_darkpool_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_sentiment_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.013328,
        "signal_id": "exit_score_deterioration",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_regime_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.05,
        "signal_id": "exit_sector_shift",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.1,
        "signal_id": "exit_vol_expansion",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_thesis_invalidated",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_earnings_risk",
        "source": "exit"
      },
      {
        "contribution_to_score": 0.0,
        "signal_id": "exit_overnight_flow_risk",
        "source": "exit"
      }
    ],
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "COIN|LONG|1777578590",
    "composite_at_entry": 4.508,
    "composite_at_exit": 4.127,
    "composite_components_at_entry": {},
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_COIN_2026-05-01T13-38-40.6604",
    "direction": "unknown",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.001642006048054566,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "mid",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.001642006048054566
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.001642006048054566,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.16420060480545662,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": -0.0007691379622368204,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.0025148741338723115,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5131745172351562
          },
          "posture": "long",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 1.0,
          "regime_label": "bull",
          "regime_source": "structural_regime:RISK_ON",
          "structural_confidence": 1.0,
          "structural_regime": "RISK_ON",
          "ts": "2026-04-30T16:11:49.674674+00:00"
        },
        "sector_intel": {
          "sector": "TECH",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-04-30T16:13:20.272932+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 34.122,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "TECH",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:38:40.816358+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -0.381,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": 0.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 0,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "UNRESOLVED_ENTRY_OID:COIN|LONG|1777578590",
    "entry_price": 192.59,
    "entry_regime": "unknown",
    "entry_sector_profile": {
      "sector": "UNKNOWN"
    },
    "entry_timestamp": "2026-04-30T19:49:50.796095+00:00",
    "entry_ts": "2026-04-30T19:49:50.796095+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.013328,
        "normalized_value": 0.0476,
        "raw_value": 0.0476
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.05,
        "normalized_value": 1.0,
        "raw_value": 1.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.2,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "f9dc71a5-7300-4c5c-bc70-136e030bb46f",
    "exit_price": 191.21,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": true,
        "saved_loss": false
      },
      "mae": null,
      "mfe": 0.02,
      "post_exit_excursion": null,
      "profit_giveback": 1.0,
      "realized_pnl_price": -1.38,
      "time_in_trade_sec": 64129.86
    },
    "exit_reason": "stale_alpha_cutoff(1068min,0.00%)",
    "exit_reason_code": "hold",
    "exit_regime": "NEUTRAL",
    "exit_regime_context": {},
    "exit_regime_decision": "normal",
    "exit_regime_reason": "",
    "exit_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.1,
        "earnings_weight": 1.0,
        "flow_weight": 1.2,
        "short_interest_weight": 0.8
      },
      "sector": "TECH",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "exit_ts": "2026-05-01T13:38:40.660439+00:00",
    "exit_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "f9dc71a5-7300-4c5c-bc70-136e030bb46f",
    "pnl": -1.38,
    "pnl_pct": -0.716548,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "NEUTRAL",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.3810000000000002,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "COIN",
    "time_in_trade_minutes": 1068.8310724,
    "timestamp": "2026-05-01T13:38:40.660439+00:00",
    "trade_id": "open_COIN_2026-04-30T19:49:50.796095+00:00",
    "trade_key": "COIN|LONG|1777578590",
    "v2_exit_components": {
      "darkpool_deterioration": 0.0,
      "earnings_risk": 0.0,
      "flow_deterioration": 0.0,
      "overnight_flow_risk": 0.0,
      "regime_shift": 0.0,
      "score_deterioration": 0.0476,
      "sector_shift": 1.0,
      "sentiment_deterioration": 0.0,
      "thesis_invalidated": 0.0,
      "vol_expansion": 1.0
    },
    "v2_exit_score": 0.163335,
    "variant_id": "B2_live_paper"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:39:38.231897+00:00",
    "attribution_components": null,
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "BA|LONG|1777642759",
    "composite_at_entry": 0.0,
    "composite_at_exit": 0.0,
    "composite_components_at_entry": {},
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_BA_2026-05-01T13-39-37.9407",
    "direction": "unknown",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.0,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "low",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:39:38.098627+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:39:38.098627+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": 0.0,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 0,
      "delta_sector_strength": 0,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "UNRESOLVED_ENTRY_OID:BA|LONG|1777642759",
    "entry_price": 231.47,
    "entry_regime": "unknown",
    "entry_sector_profile": {
      "sector": "UNKNOWN"
    },
    "entry_timestamp": "2026-05-01T13:39:19.361711+00:00",
    "entry_ts": "2026-05-01T13:39:19.361711+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "f42972a7-3abb-4c72-87f6-14a24b2e0d88",
    "exit_price": 230.37,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": false
      },
      "mae": null,
      "mfe": 0.0,
      "post_exit_excursion": null,
      "profit_giveback": null,
      "realized_pnl_price": -1.1,
      "time_in_trade_sec": 18.58
    },
    "exit_reason": "dynamic_atr_trailing_stop",
    "exit_reason_code": "other",
    "exit_regime": "unknown",
    "exit_regime_context": {
      "atr": 0.5424824678162478,
      "dynamic_atr_stop": 230.40773006931886
    },
    "exit_regime_decision": "normal",
    "exit_regime_reason": "dynamic_atr_trailing_stop",
    "exit_sector_profile": {
      "sector": "UNKNOWN"
    },
    "exit_ts": "2026-05-01T13:39:37.940727+00:00",
    "exit_uw": {},
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "f42972a7-3abb-4c72-87f6-14a24b2e0d88",
    "pnl": -2.2,
    "pnl_pct": -0.475224,
    "position_side": "long",
    "qty": 2.0,
    "regime_label": "UNKNOWN",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.0,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "BA",
    "time_in_trade_minutes": 0.3096502666666667,
    "timestamp": "2026-05-01T13:39:37.940727+00:00",
    "trade_id": "open_BA_2026-05-01T13:39:19.361711+00:00",
    "trade_key": "BA|LONG|1777642759",
    "v2_exit_components": {},
    "v2_exit_score": 0.0,
    "variant_id": "B2_live_paper"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:39:50.231125+00:00",
    "attribution_components": null,
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "XLF|LONG|1777642622",
    "composite_at_entry": 3.5639999999999996,
    "composite_at_exit": 0.0,
    "composite_components_at_entry": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_XLF_2026-05-01T13-39-50.1036",
    "direction": "bullish",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.0,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "low",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "FINANCIALS",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:37:02.393345+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "FINANCIALS",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:39:50.104433+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -3.564,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 1,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "63e9c7eb-029a-4064-9a40-da0109e35bca",
    "entry_price": 52.35,
    "entry_regime": "NEUTRAL",
    "entry_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 0.9,
        "flow_weight": 1.0,
        "short_interest_weight": 0.9
      },
      "sector": "FINANCIALS",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "entry_timestamp": "2026-05-01T13:37:02.267158+00:00",
    "entry_ts": "2026-05-01T13:37:02.267158+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "b14db2a7-46e9-410e-81cb-4cf837ef767a",
    "exit_price": 52.21,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": false
      },
      "mae": null,
      "mfe": 0.0,
      "post_exit_excursion": null,
      "profit_giveback": null,
      "realized_pnl_price": -0.14,
      "time_in_trade_sec": 167.84
    },
    "exit_reason": "dynamic_atr_trailing_stop",
    "exit_reason_code": "other",
    "exit_regime": "mixed",
    "exit_regime_context": {
      "atr": 0.06255448782923188,
      "dynamic_atr_stop": 52.24488264159858
    },
    "exit_regime_decision": "normal",
    "exit_regime_reason": "dynamic_atr_trailing_stop",
    "exit_sector_profile": {
      "sector": "UNKNOWN"
    },
    "exit_ts": "2026-05-01T13:39:50.103627+00:00",
    "exit_uw": {},
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "b14db2a7-46e9-410e-81cb-4cf837ef767a",
    "pnl": -0.14,
    "pnl_pct": -0.267431,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "MIXED",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.0,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "XLF",
    "time_in_trade_minutes": 2.797274483333333,
    "timestamp": "2026-05-01T13:39:50.103627+00:00",
    "trade_id": "open_XLF_2026-05-01T13:37:02.267158+00:00",
    "trade_key": "XLF|LONG|1777642622",
    "v2_exit_components": {},
    "v2_exit_score": 0.0,
    "variant_id": "paper_aggressive"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:39:53.294555+00:00",
    "attribution_components": null,
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "HD|LONG|1777642577",
    "composite_at_entry": 3.581,
    "composite_at_exit": 0.0,
    "composite_components_at_entry": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_HD_2026-05-01T13-39-53.1570",
    "direction": "bullish",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "low"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": 0.0,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "low",
        "vol_regime_exit": "low"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:36:17.884648+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:39:53.157815+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -3.581,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 0,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "41ebd551-505f-465e-84d2-8aab71ee3c1b",
    "entry_price": 328.73,
    "entry_regime": "NEUTRAL",
    "entry_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 1.0,
        "flow_weight": 1.0,
        "short_interest_weight": 1.0
      },
      "sector": "UNKNOWN",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "entry_timestamp": "2026-05-01T13:36:17.761189+00:00",
    "entry_ts": "2026-05-01T13:36:17.761189+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "98a8dc17-5afd-42da-ab48-e2b29efc7c09",
    "exit_price": 326.69,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": false
      },
      "mae": null,
      "mfe": 0.0,
      "post_exit_excursion": null,
      "profit_giveback": null,
      "realized_pnl_price": -2.04,
      "time_in_trade_sec": 215.4
    },
    "exit_reason": "dynamic_atr_trailing_stop",
    "exit_reason_code": "other",
    "exit_regime": "mixed",
    "exit_regime_context": {
      "atr": 0.6700293509854965,
      "dynamic_atr_stop": 327.44530601326204
    },
    "exit_regime_decision": "normal",
    "exit_regime_reason": "dynamic_atr_trailing_stop",
    "exit_sector_profile": {
      "sector": "UNKNOWN"
    },
    "exit_ts": "2026-05-01T13:39:53.157003+00:00",
    "exit_uw": {},
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "98a8dc17-5afd-42da-ab48-e2b29efc7c09",
    "pnl": -2.04,
    "pnl_pct": -0.62057,
    "position_side": "long",
    "qty": 1.0,
    "regime_label": "MIXED",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.0,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "HD",
    "time_in_trade_minutes": 3.5899302333333334,
    "timestamp": "2026-05-01T13:39:53.157003+00:00",
    "trade_id": "open_HD_2026-05-01T13:36:17.761189+00:00",
    "trade_key": "HD|LONG|1777642577",
    "v2_exit_components": {},
    "v2_exit_score": 0.0,
    "variant_id": "paper_aggressive"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:43:06.132079+00:00",
    "attribution_components": null,
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "XLI|LONG|1777642661",
    "composite_at_entry": 3.5389999999999997,
    "composite_at_exit": 0.0,
    "composite_components_at_entry": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_XLI_2026-05-01T13-43-05.9962",
    "direction": "bullish",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_direction",
        "uw_direction"
      ],
      "direction_intel_components_exit": {
        "breadth_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 1.0
        },
        "etf_flow_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "futures_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": -0.00591977233294818
        },
        "macro_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "overnight_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": -0.00591977233294818
        },
        "postmarket_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "premarket_direction": {
          "contribution_to_direction_score": -1.0,
          "normalized_value": -1.0,
          "raw_value": "bearish"
        },
        "sector_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": 0.0
        },
        "uw_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "neutral"
        },
        "volatility_direction": {
          "contribution_to_direction_score": 0.0,
          "normalized_value": 0.0,
          "raw_value": "mid"
        }
      },
      "intel_deltas": {
        "breadth_adv_dec_delta": 0.0,
        "futures_direction_delta": -0.00591977233294818,
        "macro_risk_entry": false,
        "macro_risk_exit": false,
        "overnight_volatility_delta": 0.0,
        "sector_strength_delta": 0.0,
        "vol_regime_entry": "low",
        "vol_regime_exit": "mid"
      },
      "intel_snapshot_entry": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "flat",
          "NQ_direction": "flat",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": 0.0
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": 0.0,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": 0.0,
          "premarket_sentiment": "neutral",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "flat",
            "qqq_overnight_ret": 0.0,
            "risk_on_off": "neutral",
            "spy_overnight_ret": 0.0,
            "stale_1m": true,
            "volatility_regime": "low",
            "vxx_vxz_ratio": 0.0
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:31:02.428661+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:37:41.396539+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 10.0,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "low"
        }
      },
      "intel_snapshot_exit": {
        "breadth_intel": {
          "adv_dec_ratio": 1.0,
          "index_breadth": {},
          "new_highs_lows": 0.0,
          "sector_breadth": {},
          "up_vol_down_vol_ratio": 1.0
        },
        "etf_flow_intel": {
          "IWM_flow": 0.0,
          "QQQ_flow": 0.0,
          "SPY_flow": 0.0,
          "sector_ETF_flows": {}
        },
        "futures_intel": {
          "ES_direction": "down",
          "NQ_direction": "down",
          "RTY_direction": "flat",
          "VX_direction": "flat",
          "futures_basis": 0.0,
          "futures_trend_strength": -0.00591977233294818
        },
        "macro_intel": {
          "macro_events_today": [],
          "macro_risk_flag": false,
          "macro_sentiment_score": 0.0
        },
        "overnight_intel": {
          "overnight_dark_pool_imbalance": 0.0,
          "overnight_flow": 0.0,
          "overnight_return": -0.00591977233294818,
          "overnight_volatility": 0.0
        },
        "postmarket_intel": {
          "after_hours_volume_ratio": 1.0,
          "earnings_reaction_flag": false,
          "postmarket_gap_pct": 0.0,
          "postmarket_sentiment": "neutral"
        },
        "premarket_intel": {
          "premarket_flow": 0.0,
          "premarket_gap_pct": -0.591977233294818,
          "premarket_sentiment": "bearish",
          "premarket_volatility": 0.0,
          "premarket_volume_ratio": 1.0
        },
        "regime_posture": {
          "market_context": {
            "market_trend": "down",
            "qqq_overnight_ret": -0.008261392847060142,
            "risk_on_off": "neutral",
            "spy_overnight_ret": -0.0035781518188362166,
            "stale_1m": true,
            "volatility_regime": "mid",
            "vxx_vxz_ratio": 0.5081997084548104
          },
          "posture": "neutral",
          "posture_flags": {
            "allow_new_longs": true,
            "prefer_shorts": false,
            "tighten_long_exits": false
          },
          "regime_confidence": 0.45,
          "regime_label": "chop",
          "regime_source": "default_chop",
          "structural_confidence": 0.5,
          "structural_regime": "NEUTRAL",
          "ts": "2026-05-01T13:41:58.241658+00:00"
        },
        "sector_intel": {
          "sector": "UNKNOWN",
          "sector_ETF_flow": 0.0,
          "sector_momentum": 0.0,
          "sector_strength_rank": 0,
          "sector_volatility": 0.0
        },
        "timestamp": "2026-05-01T13:43:05.997091+00:00",
        "uw_intel": {
          "uw_overnight_sentiment": "neutral",
          "uw_premarket_sentiment": "neutral",
          "uw_preopen_dark_pool": 0.0,
          "uw_preopen_flow": 0.0
        },
        "volatility_intel": {
          "VIX_change": 0.0,
          "VIX_level": 33.467999999999996,
          "VVIX_level": 0.0,
          "realized_vol_1d": 0.0,
          "realized_vol_20d": 0.2,
          "realized_vol_5d": 0.0,
          "vol_regime": "mid"
        }
      }
    },
    "entry_exit_deltas": {
      "delta_composite": -3.539,
      "delta_dark_pool_notional": 0.0,
      "delta_flow_conviction": -1.0,
      "delta_gamma": 0.0,
      "delta_iv_rank": 0.0,
      "delta_regime": 1,
      "delta_sector_strength": 0,
      "delta_sentiment": 1,
      "delta_squeeze_score": 0.0,
      "delta_vol": 0.0
    },
    "entry_order_id": "ed924505-4c9e-4e4c-a293-9eb8c0618650",
    "entry_price": 174.683333,
    "entry_regime": "NEUTRAL",
    "entry_sector_profile": {
      "multipliers": {
        "darkpool_weight": 1.0,
        "earnings_weight": 1.0,
        "flow_weight": 1.0,
        "short_interest_weight": 1.0
      },
      "sector": "UNKNOWN",
      "version": "2026-01-20_sector_profiles_v1"
    },
    "entry_timestamp": "2026-05-01T13:37:41.285956+00:00",
    "entry_ts": "2026-05-01T13:37:41.285956+00:00",
    "entry_uw": {
      "darkpool_bias": 0.0,
      "earnings_proximity": 999,
      "flow_strength": 1.0,
      "regime_alignment": 0.25,
      "sector_alignment": 0.0,
      "sentiment": "NEUTRAL",
      "sentiment_score": 0.0,
      "uw_intel_source": "premarket_postmarket",
      "uw_intel_version": "2026-01-20_uw_v1"
    },
    "exit_components_granular": {
      "exit_dark_pool_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_flow_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_gamma_collapse": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_insider_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_microstructure_noise": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_regime_shift": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_score_deterioration": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sector_rotation": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_sentiment_reversal": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_time_decay": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      },
      "exit_volatility_spike": {
        "contribution_to_exit_score": 0.0,
        "normalized_value": 0.0,
        "raw_value": 0.0
      }
    },
    "exit_order_id": "2fce4523-2207-4434-800a-2649cbb07273",
    "exit_price": 174.23,
    "exit_quality_metrics": {
      "exit_efficiency": {
        "left_money": false,
        "saved_loss": false
      },
      "mae": null,
      "mfe": 0.0,
      "post_exit_excursion": null,
      "profit_giveback": null,
      "realized_pnl_price": -0.453333,
      "time_in_trade_sec": 324.71
    },
    "exit_reason": "dynamic_atr_trailing_stop",
    "exit_reason_code": "other",
    "exit_regime": "mixed",
    "exit_regime_context": {
      "atr": 0.24488617629921966,
      "dynamic_atr_stop": 174.24776725738275
    },
    "exit_regime_decision": "normal",
    "exit_regime_reason": "dynamic_atr_trailing_stop",
    "exit_sector_profile": {
      "sector": "UNKNOWN"
    },
    "exit_ts": "2026-05-01T13:43:05.996297+00:00",
    "exit_uw": {},
    "fees_usd": 0.0,
    "mode": "UNKNOWN",
    "order_id": "2fce4523-2207-4434-800a-2649cbb07273",
    "pnl": -1.36,
    "pnl_pct": -0.259517,
    "position_side": "long",
    "qty": 3.0,
    "regime_label": "MIXED",
    "relative_strength_deterioration": 0.0,
    "replacement_candidate": null,
    "replacement_reasoning": null,
    "score_deterioration": 0.0,
    "side": "buy",
    "strategy": "UNKNOWN",
    "symbol": "XLI",
    "time_in_trade_minutes": 5.411839016666667,
    "timestamp": "2026-05-01T13:43:05.996297+00:00",
    "trade_id": "open_XLI_2026-05-01T13:37:41.285956+00:00",
    "trade_key": "XLI|LONG|1777642661",
    "v2_exit_components": {},
    "v2_exit_score": 0.0,
    "variant_id": "paper_aggressive"
  },
  {
    "_day": "2026-05-01",
    "_enriched_at": "2026-05-01T13:44:16.564493+00:00",
    "attribution_components": null,
    "attribution_schema_version": "1.0.0",
    "canonical_trade_id": "COST|LONG|1777642595",
    "composite_at_entry": 3.577,
    "composite_at_exit": 0.0,
    "composite_components_at_entry": {
      "calendar": 0.0,
      "congress": 0.0,
      "dark_pool": 0.023,
      "etf_flow": 0.012,
      "event": 0.204,
      "flow": 2.5,
      "freshness_factor": 0.943,
      "ftd_pressure": 0.036,
      "greeks_gamma": 0.0,
      "insider": 0.075,
      "institutional": 0.0,
      "iv_rank": 0.018,
      "iv_skew": 0.07,
      "market_tide": 0.276,
      "motif_bonus": 0.0,
      "oi_change": 0.042,
      "regime": 0.008,
      "shorts_squeeze": 0.0,
      "smile": 0.004,
      "squeeze_score": 0.03,
      "toxicity_correlation_penalty": 0.0,
      "toxicity_penalty": -0.162,
      "whale": 0.0
    },
    "composite_components_at_exit": {},
    "composite_version": "v2",
    "decision_id": "dec_COST_2026-05-01T13-44-16.3309",
    "direction": "bullish",
    "direction_intel_embed": {
      "canonical_direction_components": [
        "premarket_direction",
        "postmarket_direction",
        "overnight_direction",
        "futures_direction",
        "volatility_direction",
        "breadth_direction",
        "sector_direction",
        "etf_flow_direction",
        "macro_di
```

### All parity rows (telemetry computed)
```
(missing)
```

### All UW intel snapshots (telemetry state)
```
[]
```

### Telemetry computed artifacts (index only)
```
{
  "computed_files": []
}
```

## SHADOW TUNING APPENDIX
- This appendix is large and intended to be machine-readable for future tuning.
### Per-symbol tuning payload (shadow-only; sufficient samples)
```
{
  "range": "2026-05-01",
  "symbols": []
}
```

### Per-feature EV curve summaries (shadow-only)
```
{
  "features": []
}
```

### Per-signal EV summaries (shadow-only)
```
{
  "signals": []
}
```


## Validation issues (best-effort)
- contains_nan_string
