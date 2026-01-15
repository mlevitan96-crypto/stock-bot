# Stock-Bot Daily Review – 2026-01-15 (Alpaca)

**Report Generated:** 2026-01-15T22:30:19+00:00
**Data Source:** Droplet Production Server
**Data Fetched:** 2026-01-15T22:30:19.145285+00:00
**Details bundle:** `reports/stock-bot-daily-review-2026-01-15-artifacts` (CSV + JSON exports)

## 1. Session overview
- **Trading window (UTC):** 2026-01-15T15:59:39+00:00 → 2026-01-15T22:15:00+00:00
- **Total executed trade events (attribution):** 94 (includes opens/closes)
- **Total realized closes/scales:** 18
- **Net realized PnL (close/scale legs):** $-7.30
- **Win rate (close/scale legs):** 38.9% (7W / 11L)
- **Max drawdown (realized-PnL curve proxy):** $32.73 (peak $15.29)
- **Max single-position size at entry (proxy):** $495.34 (max equity seen $51,019.15)

## 2. Execution summary
- **Executed entry events (opens):** 76 (filled-order match: 76*)
- **Executed exit events (closes/scales):** 18

### Per-symbol realized results (close/scale legs)
| Symbol | Closed legs | PnL (USD) | Win rate | Avg hold (min) |
| --- | --- | --- | --- | --- |
| C | 1 | $21.71 | 100.0% | 1146.3 |
| DIA | 1 | $7.63 | 100.0% | 1148.8 |
| HOOD | 1 | $5.14 | 100.0% | 32.7 |
| COIN | 1 | $5.00 | 100.0% | 25.2 |
| LOW | 1 | $2.13 | 100.0% | 1147.9 |
| SLB | 1 | $1.39 | 100.0% | 1150.4 |
| PFE | 1 | $0.63 | 100.0% | 1150.2 |
| WMT | 1 | $-0.60 | 0.0% | 1149.7 |
| PLTR | 1 | $-1.65 | 0.0% | 1152.1 |
| XLI | 1 | $-1.88 | 0.0% | 1151.7 |
| JNJ | 1 | $-3.14 | 0.0% | 1148.4 |
| IWM | 1 | $-3.59 | 0.0% | 1151.5 |
| BAC | 1 | $-3.72 | 0.0% | 1151.8 |
| F | 1 | $-3.90 | 0.0% | 1149.6 |
| JPM | 1 | $-4.17 | 0.0% | 1152.2 |
| NVDA | 1 | $-5.41 | 0.0% | 1152.4 |
| BA | 1 | $-10.33 | 0.0% | 1215.2 |
| TSLA | 1 | $-12.54 | 0.0% | 1152.3 |

### Realized trade ledger (all closes/scales today)
| Symbol | Side | Qty | Entry time (UTC) | Exit time (UTC) | Entry px | Exit px | PnL (USD) | PnL (%) | Hold (min) | Exit reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BA | sell | 2 | 2026-01-14T19:44:32+00:00 | 2026-01-15T15:59:44+00:00 | 241.8250 | 246.9900 | $-10.33 | -2.14% | 1215.2 | signal_decay(0.82)+stale_trade(1215min,-0.02%) |
| BAC | sell | 6 | 2026-01-14T20:47:53+00:00 | 2026-01-15T15:59:44+00:00 | 52.3500 | 52.9700 | $-3.72 | -1.18% | 1151.8 | signal_decay(0.91)+stale_trade(1152min,-0.01%) |
| C | buy | 4 | 2026-01-14T20:53:28+00:00 | 2026-01-15T15:59:44+00:00 | 112.3175 | 117.7450 | $21.71 | 4.83% | 1146.3 | signal_decay(0.68)+drawdown(4.8%)+stale_trade(1146min,0.05%) |
| DIA | buy | 2 | 2026-01-14T20:50:54+00:00 | 2026-01-15T15:59:44+00:00 | 490.9850 | 494.8000 | $7.63 | 0.78% | 1148.8 | signal_decay(0.66)+stale_trade(1149min,0.01%) |
| F | sell | 52 | 2026-01-14T20:50:09+00:00 | 2026-01-15T15:59:44+00:00 | 13.8200 | 13.8950 | $-3.90 | -0.54% | 1149.6 | signal_decay(0.82)+stale_trade(1150min,-0.01%) |
| IWM | sell | 1 | 2026-01-14T20:48:16+00:00 | 2026-01-15T15:59:44+00:00 | 262.8500 | 266.4399 | $-3.59 | -1.37% | 1151.5 | signal_decay(0.85)+stale_trade(1152min,-0.01%) |
| JNJ | buy | 4 | 2026-01-14T20:51:17+00:00 | 2026-01-15T15:59:44+00:00 | 218.4650 | 217.6800 | $-3.14 | -0.36% | 1148.4 | signal_decay(0.66)+stale_trade(1148min,-0.00%) |
| JPM | sell | 1 | 2026-01-14T20:47:33+00:00 | 2026-01-15T15:59:44+00:00 | 307.8100 | 311.9800 | $-4.17 | -1.35% | 1152.2 | signal_decay(0.88)+stale_trade(1152min,-0.01%) |
| LOW | buy | 1 | 2026-01-14T20:51:48+00:00 | 2026-01-15T15:59:44+00:00 | 275.2600 | 277.3950 | $2.13 | 0.78% | 1147.9 | signal_decay(0.74)+stale_trade(1148min,0.01%) |
| NVDA | sell | 1 | 2026-01-14T20:47:23+00:00 | 2026-01-15T15:59:44+00:00 | 182.2700 | 187.6750 | $-5.41 | -2.97% | 1152.4 | signal_decay(0.81)+drawdown(3.0%)+stale_trade(1152min,-0.03%) |
| PFE | sell | 14 | 2026-01-14T20:49:34+00:00 | 2026-01-15T15:59:44+00:00 | 25.4800 | 25.4350 | $0.63 | 0.18% | 1150.2 | signal_decay(0.83)+stale_trade(1150min,0.00%) |
| PLTR | sell | 1 | 2026-01-14T20:47:41+00:00 | 2026-01-15T15:59:44+00:00 | 178.1000 | 179.7500 | $-1.65 | -0.93% | 1152.1 | signal_decay(0.88)+stale_trade(1152min,-0.01%) |
| SLB | sell | 14 | 2026-01-14T20:49:21+00:00 | 2026-01-15T15:59:44+00:00 | 46.8250 | 46.7255 | $1.39 | 0.21% | 1150.4 | signal_decay(0.83)+stale_trade(1150min,0.00%) |
| TSLA | sell | 2 | 2026-01-14T20:47:25+00:00 | 2026-01-15T15:59:44+00:00 | 437.0850 | 443.3550 | $-12.54 | -1.43% | 1152.3 | signal_decay(0.71)+stale_trade(1152min,-0.01%) |
| WMT | sell | 6 | 2026-01-14T20:49:59+00:00 | 2026-01-15T15:59:44+00:00 | 120.3400 | 120.4400 | $-0.60 | -0.08% | 1149.7 | signal_decay(0.81)+stale_trade(1150min,-0.00%) |
| XLI | sell | 1 | 2026-01-14T20:48:00+00:00 | 2026-01-15T15:59:44+00:00 | 163.9000 | 165.7750 | $-1.88 | -1.14% | 1151.7 | signal_decay(0.85)+stale_trade(1152min,-0.01%) |
| COIN | long | 1 | 2026-01-15T19:45:03+00:00 | 2026-01-15T20:10:15+00:00 | 245.6800 | 240.6800 | $5.00 | 0.61% | 25.2 | signal_decay(0.87)+profit_target(2%) |
| HOOD | long | 2 | 2026-01-15T19:44:54+00:00 | 2026-01-15T20:17:36+00:00 | 113.5500 | 110.9800 | $5.14 | 0.68% | 32.7 | signal_decay(0.79)+profit_target(2%) |

<details>
<summary>Executed entry ledger (opens) – 76 rows</summary>

| Time (UTC) | Symbol | Direction | Score | Position size (USD) | Order type | Fill px (nearest) |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-15T16:00:09+00:00 | LOW | bullish | 4.193 | $277.41 | market | 277.5200 |
| 2026-01-15T16:00:09+00:00 | LOW | bullish | 4.194 | $277.41 | market | 277.5200 |
| 2026-01-15T16:00:21+00:00 | XOM | bullish | 4.117 | $389.40 | market | 129.8500 |
| 2026-01-15T16:00:21+00:00 | XOM | bullish | 4.117 | $389.40 | market | 129.8500 |
| 2026-01-15T16:00:36+00:00 | HD | bullish | 3.911 | $377.91 | market | 378.1300 |
| 2026-01-15T16:00:36+00:00 | HD | bullish | 3.911 | $377.91 | market | 378.1300 |
| 2026-01-15T16:01:02+00:00 | TGT | bullish | 3.896 | $439.60 | market | 109.9100 |
| 2026-01-15T16:01:05+00:00 | TGT | bullish | 3.896 | $439.60 | market | 109.9100 |
| 2026-01-15T16:01:18+00:00 | HOOD | bullish | 3.787 | $464.14 | market | 115.9600 |
| 2026-01-15T16:01:22+00:00 | HOOD | bullish | 3.786 | $464.14 | market | 115.9600 |
| 2026-01-15T16:01:34+00:00 | BAC | bearish | 3.749 | $317.77 | market | 52.9600 |
| 2026-01-15T16:01:37+00:00 | BAC | bearish | 3.749 | $317.77 | market | 52.9600 |
| 2026-01-15T16:02:41+00:00 | GOOGL | bullish | 4.383 | $332.63 | limit | 332.7800 |
| 2026-01-15T16:02:56+00:00 | GOOGL | bullish | 4.383 | $332.63 | market | 332.7800 |
| 2026-01-15T16:04:56+00:00 | AAPL | bullish | 4.168 | $259.99 | market | 260.2000 |
| 2026-01-15T16:04:56+00:00 | AAPL | bullish | 4.169 | $259.99 | market | 260.2000 |
| 2026-01-15T16:05:08+00:00 | V | bullish | 4.146 | $330.37 | market | 330.5000 |
| 2026-01-15T16:05:08+00:00 | V | bullish | 4.145 | $330.37 | market | 330.5000 |
| 2026-01-15T16:06:36+00:00 | F | bearish | 3.674 | $361.27 | limit | 13.8900 |
| 2026-01-15T16:06:36+00:00 | F | bearish | 3.673 | $361.27 | limit | 13.8900 |
| 2026-01-15T16:06:49+00:00 | BA | bearish | 3.512 | $247.15 | market | 247.1000 |
| 2026-01-15T16:06:49+00:00 | BA | bearish | 3.513 | $247.15 | market | 247.1000 |
| 2026-01-15T16:07:13+00:00 | RIVN | bearish | 3.368 | $223.93 | market | 17.2100 |
| 2026-01-15T16:07:17+00:00 | RIVN | bearish | 3.368 | $223.93 | market | 17.2100 |
| 2026-01-15T16:07:28+00:00 | NFLX | bearish | 3.355 | $178.39 | limit | 89.1700 |
| 2026-01-15T16:07:39+00:00 | MRNA | bearish | 3.243 | $238.44 | limit | 39.7000 |
| 2026-01-15T16:07:40+00:00 | NFLX | bearish | 3.355 | $178.37 | limit | 89.1700 |
| 2026-01-15T16:07:57+00:00 | COIN | bearish | 3.207 | $245.07 | limit | 244.9200 |
| 2026-01-15T16:08:05+00:00 | COIN | bearish | 3.208 | $245.13 | market | 244.9200 |
| 2026-01-15T16:08:22+00:00 | MS | bullish | 3.174 | $190.20 | market | 190.2700 |
| 2026-01-15T19:44:45+00:00 | AAPL | bullish | 3.425 | $257.73 | limit | 257.7100 |
| 2026-01-15T19:44:51+00:00 | HOOD | bullish | 4.666 | $453.46 | market | 113.5800 |
| 2026-01-15T19:44:53+00:00 | HOOD | bullish | 4.667 | $454.04 | limit | 113.5800 |
| 2026-01-15T19:44:56+00:00 | WMT | bullish | 4.440 | $478.68 | limit | 119.6700 |
| 2026-01-15T19:45:01+00:00 | WMT | bullish | 4.442 | $478.64 | limit | 119.6700 |
| 2026-01-15T19:45:01+00:00 | COIN | bullish | 4.301 | $491.49 | limit | 245.6800 |
| 2026-01-15T19:45:22+00:00 | UNH | bullish | 4.258 | $337.28 | market | 337.3000 |
| 2026-01-15T19:45:22+00:00 | UNH | bullish | 4.256 | $337.28 | market | 337.3000 |
| 2026-01-15T19:45:32+00:00 | RIVN | bearish | 3.146 | $221.46 | limit | 17.0300 |
| 2026-01-15T19:45:36+00:00 | RIVN | bearish | 3.147 | $221.46 | limit | 17.0300 |
| 2026-01-15T19:46:03+00:00 | AMZN | bullish | 4.012 | $475.30 | limit | 237.6600 |
| 2026-01-15T19:46:12+00:00 | AMZN | bullish | 4.013 | $475.32 | market | 237.6600 |
| 2026-01-15T19:47:23+00:00 | V | bullish | 3.944 | $327.14 | limit | 327.1200 |
| 2026-01-15T19:47:34+00:00 | V | bullish | 3.942 | $327.06 | market | 327.1200 |
| 2026-01-15T19:47:52+00:00 | HD | bullish | 3.869 | $379.29 | market | 379.3500 |
| 2026-01-15T19:47:59+00:00 | HD | bullish | 3.866 | $379.29 | market | 379.3500 |
| 2026-01-15T19:48:28+00:00 | MS | bullish | 3.445 | $191.09 | market | 191.1200 |
| 2026-01-15T19:48:32+00:00 | MS | bullish | 3.443 | $191.13 | market | 191.1200 |
| 2026-01-15T19:48:58+00:00 | LOW | bullish | 3.332 | $277.07 | market | 277.1900 |
| 2026-01-15T19:49:01+00:00 | LOW | bullish | 3.335 | $277.07 | market | 277.1900 |
| 2026-01-15T19:50:44+00:00 | MSFT | bullish | 3.539 | $457.57 | market | 457.7900 |
| 2026-01-15T19:50:44+00:00 | MSFT | bullish | 3.539 | $457.54 | market | 457.7900 |
| 2026-01-15T19:51:02+00:00 | NIO | bullish | 3.378 | $303.23 | limit | 4.6700 |
| 2026-01-15T19:51:02+00:00 | NIO | bullish | 3.378 | $303.23 | limit | 4.6700 |
| 2026-01-15T19:51:24+00:00 | DIA | bullish | 3.332 | $495.31 | limit | 495.2400 |
| 2026-01-15T19:51:24+00:00 | DIA | bullish | 3.332 | $495.34 | limit | 495.2400 |
| 2026-01-15T19:52:56+00:00 | V | bullish | 4.439 | $327.43 | market | 327.5500 |
| 2026-01-15T19:52:59+00:00 | V | bullish | 4.439 | $327.41 | market | 327.5500 |
| 2026-01-15T19:58:44+00:00 | V | bullish | 4.321 | $327.18 | market | 327.1400 |
| 2026-01-15T20:04:13+00:00 | V | bearish | 3.748 | $326.63 | market | 326.5100 |
| 2026-01-15T20:09:18+00:00 | V | bearish | 3.659 | $326.43 | limit | 326.4800 |
| 2026-01-15T20:15:30+00:00 | V | bearish | 3.559 | $326.85 | limit | 326.8200 |
| 2026-01-15T20:15:40+00:00 | V | bearish | 3.563 | $326.85 | market | 326.8200 |
| 2026-01-15T20:16:39+00:00 | GOOGL | bullish | 5.608 | $332.20 | limit | 332.1600 |
| 2026-01-15T20:21:26+00:00 | V | bearish | 3.476 | $327.14 | market | 326.9800 |
| 2026-01-15T20:27:16+00:00 | V | bearish | 3.381 | $327.18 | market | 327.0800 |
| 2026-01-15T20:27:19+00:00 | V | bearish | 3.381 | $327.15 | market | 327.0800 |
| 2026-01-15T20:27:59+00:00 | NVDA | bullish | 3.499 | $187.35 | limit | 187.2900 |
| 2026-01-15T20:27:59+00:00 | NVDA | bullish | 3.499 | $187.35 | limit | 187.2900 |
| 2026-01-15T20:33:04+00:00 | V | bearish | 3.299 | $327.43 | market | 327.4100 |
| 2026-01-15T20:38:53+00:00 | V | bearish | 3.213 | $327.52 | limit | 327.4700 |
| 2026-01-15T20:38:53+00:00 | V | bearish | 3.213 | $327.46 | limit | 327.4700 |
| 2026-01-15T20:44:21+00:00 | V | bearish | 3.141 | $327.54 | limit | 327.5700 |
| 2026-01-15T20:44:21+00:00 | V | bearish | 3.140 | $327.54 | limit | 327.5700 |
| 2026-01-15T20:45:34+00:00 | PLTR | bearish | 3.565 | $355.24 | limit | 177.6200 |
| 2026-01-15T20:45:34+00:00 | PLTR | bearish | 3.566 | $355.24 | limit | 177.6200 |

</details>

_\* Filled-order match is a time-window heuristic on `orders.jsonl`._

### Notable trades (largest PnL impact)
- **C buy**: PnL $21.71 (4.83%); hold 1146.3 min; exit `signal_decay(0.68)+drawdown(4.8%)+stale_trade(1146min,0.05%)`; entry 2026-01-14T20:53:28+00:00 → exit 2026-01-15T15:59:44+00:00
- **TSLA sell**: PnL $-12.54 (-1.43%); hold 1152.3 min; exit `signal_decay(0.71)+stale_trade(1152min,-0.01%)`; entry 2026-01-14T20:47:25+00:00 → exit 2026-01-15T15:59:44+00:00
- **BA sell**: PnL $-10.33 (-2.14%); hold 1215.2 min; exit `signal_decay(0.82)+stale_trade(1215min,-0.02%)`; entry 2026-01-14T19:44:32+00:00 → exit 2026-01-15T15:59:44+00:00
- **DIA buy**: PnL $7.63 (0.78%); hold 1148.8 min; exit `signal_decay(0.66)+stale_trade(1149min,0.01%)`; entry 2026-01-14T20:50:54+00:00 → exit 2026-01-15T15:59:44+00:00

## 3. Signal behavior
- **Total signals logged:** 2000
- **By direction:** bullish=1377, bearish=623
- **By source:** composite_v3=2000
- **Score buckets (composite_score):** [0.0,2.0)=0, [2.0,3.0)=356, [3.0,4.0)=1017, [4.0,5.0)=627, [5.0,6.0)=0, [6.0,9.0)=0
- **Avg toxicity:** 0.677 (from signal metadata)
- **Avg freshness:** 0.787 (from signal metadata)
- **Top sectors (sector_tide_info):** Financial=717, Consumer=516, Technology=480, Healthcare=168, ETF=33

### Per-signal table (derived key = source:version:direction)
| Signal | Fired | Executed* | Blocked* | Missed* | Counter* | Attributed PnL (USD)* |
| --- | --- | --- | --- | --- | --- | --- |
| composite_v3:V3.1:bearish | 623 | 48 | 331 | 215 | 437 | $0.00 |
| composite_v3:V3.1:bullish | 1377 | 31 | 131 | 1181 | 575 | $0.00 |

_\* Executed/Blocked/Missed/Counter and PnL attribution are **heuristics** based on time-window matching between `signals.jsonl`, `orders.jsonl`, `blocked_trades.jsonl`, and `attribution.jsonl`._

## 4. Blocked trades
- **Total blocked trades:** 570
- **Top reason codes:** order_validation_failed=236, expectancy_blocked:score_floor_breach=222, max_new_positions_per_cycle=100, max_positions_reached=9, symbol_on_cooldown=3

### Blocked trade log (first 200 rows; full day is large)
| Time (UTC) | Symbol | Direction | Score | Reason | Details |
| --- | --- | --- | --- | --- | --- |
| 2026-01-15T16:00:22+00:00 | BLK | bullish | 4.030 | order_validation_failed | Order $1148.00 exceeds max position size $825.00 |
| 2026-01-15T16:00:22+00:00 | BLK | bullish | 4.031 | order_validation_failed | Order $1148.00 exceeds max position size $825.00 |
| 2026-01-15T16:01:37+00:00 | C | bearish | 3.619 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | C | bearish | 3.619 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | V | bearish | 3.597 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | V | bearish | 3.597 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLF | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLF | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLE | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLE | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLP | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLP | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | BA | bearish | 3.559 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | BA | bearish | 3.559 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | AAPL | bullish | 3.535 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | AAPL | bullish | 3.535 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | NVDA | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | NVDA | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | COST | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | COST | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | F | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | F | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | XLK | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | XLK | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | DIA | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | DIA | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | PLTR | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | PLTR | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:44+00:00 | SLB | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:44+00:00 | SLB | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | JPM | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | JPM | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | XLV | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | XLV | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | RIVN | bearish | 3.485 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | RIVN | bearish | 3.485 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | QQQ | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | QQQ | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | SPY | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | SPY | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | CVX | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | CVX | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | NFLX | bearish | 3.467 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | NFLX | bearish | 3.467 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | GOOGL | bullish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | GOOGL | bullish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | PFE | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | PFE | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | JNJ | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | JNJ | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | GM | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | GM | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | MA | bullish | 3.382 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | MA | bullish | 3.382 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | GS | bearish | 3.380 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | GS | bearish | 3.380 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | LCID | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | LCID | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | SOFI | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | SOFI | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:54+00:00 | COP | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | COP | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | AMD | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | AMD | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | WMT | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | WMT | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | XLI | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | XLI | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | MSFT | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | MSFT | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | UNH | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | UNH | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | INTC | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | INTC | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | IWM | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | MRNA | bearish | 3.351 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | IWM | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | COIN | bearish | 3.312 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | MRNA | bearish | 3.351 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | CAT | bearish | 3.198 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | COIN | bearish | 3.312 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | TSLA | bullish | 3.068 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | CAT | bearish | 3.198 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:03+00:00 | TSLA | bullish | 3.068 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:03+00:00 | AMZN | bearish | 3.058 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:03+00:00 | AMZN | bearish | 3.058 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:45+00:00 | BLK | bullish | 4.376 | order_validation_failed | Order $1149.61 exceeds max position size $825.00 |
| 2026-01-15T16:03:03+00:00 | BLK | bullish | 4.376 | order_validation_failed | Order $1150.60 exceeds max position size $825.00 |
| 2026-01-15T16:05:08+00:00 | BLK | bullish | 3.934 | order_validation_failed | Order $1147.29 exceeds max position size $825.00 |
| 2026-01-15T16:05:08+00:00 | BLK | bullish | 3.933 | order_validation_failed | Order $1147.29 exceeds max position size $825.00 |
| 2026-01-15T16:06:33+00:00 | BLK | bullish | 4.398 | order_validation_failed | Order $1146.40 exceeds max position size $825.00 |
| 2026-01-15T16:06:33+00:00 | BLK | bullish | 4.397 | order_validation_failed | Order $1146.40 exceeds max position size $825.00 |
| 2026-01-15T16:07:47+00:00 | MRNA | bearish | 3.242 | symbol_on_cooldown | — |
| 2026-01-15T16:08:05+00:00 | MS | bullish | 3.175 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:05+00:00 | META | bullish | 3.120 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:05+00:00 | WFC | bullish | 3.029 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:05+00:00 | TSLA | bullish | 2.969 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T16:08:08+00:00 | C | bearish | 2.718 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T16:08:22+00:00 | META | bullish | 3.120 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:22+00:00 | WFC | bullish | 3.028 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:22+00:00 | TSLA | bullish | 2.969 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T16:08:22+00:00 | C | bearish | 2.717 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:44:56+00:00 | COST | bullish | 4.320 | order_validation_failed | Order $954.21 exceeds max position size $825.00 |
| 2026-01-15T19:45:02+00:00 | COST | bullish | 4.320 | order_validation_failed | Order $954.21 exceeds max position size $825.00 |
| 2026-01-15T19:46:03+00:00 | V | bullish | 3.984 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:03+00:00 | HD | bullish | 3.908 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:07+00:00 | NVDA | bullish | 3.571 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:07+00:00 | MS | bullish | 3.480 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:07+00:00 | LOW | bullish | 3.368 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:07+00:00 | BAC | bearish | 2.434 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:46:12+00:00 | V | bullish | 3.985 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:15+00:00 | COIN | bullish | 3.942 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:15+00:00 | HD | bullish | 3.910 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:15+00:00 | PLTR | bullish | 3.706 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:15+00:00 | NVDA | bullish | 3.572 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:18+00:00 | MS | bullish | 3.480 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:18+00:00 | BAC | bearish | 2.435 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:46:46+00:00 | COST | bullish | 4.276 | order_validation_failed | Order $954.43 exceeds max position size $825.00 |
| 2026-01-15T19:46:53+00:00 | COST | bullish | 4.273 | order_validation_failed | Order $954.42 exceeds max position size $825.00 |
| 2026-01-15T19:48:31+00:00 | GS | bullish | 3.358 | order_validation_failed | Order $974.00 exceeds max position size $825.00 |
| 2026-01-15T19:48:35+00:00 | GS | bullish | 3.355 | order_validation_failed | Order $973.99 exceeds max position size $825.00 |
| 2026-01-15T19:49:37+00:00 | COST | bullish | 4.812 | order_validation_failed | Order $953.98 exceeds max position size $825.00 |
| 2026-01-15T19:49:37+00:00 | COST | bullish | 4.811 | order_validation_failed | Order $953.98 exceeds max position size $825.00 |
| 2026-01-15T19:50:09+00:00 | GS | bullish | 3.908 | order_validation_failed | Order $975.03 exceeds max position size $825.00 |
| 2026-01-15T19:50:12+00:00 | GS | bullish | 3.908 | order_validation_failed | Order $975.12 exceeds max position size $825.00 |
| 2026-01-15T19:50:12+00:00 | BAC | bearish | 2.825 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:15+00:00 | BAC | bearish | 2.825 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:16+00:00 | C | bearish | 2.749 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:16+00:00 | BLK | bearish | 2.677 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:19+00:00 | AMD | bearish | 2.668 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:19+00:00 | C | bearish | 2.749 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:19+00:00 | BLK | bearish | 2.677 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:20+00:00 | AMD | bearish | 2.668 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:44+00:00 | JPM | bearish | 2.616 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:44+00:00 | JPM | bearish | 2.616 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:02+00:00 | XLE | bearish | 2.503 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:02+00:00 | XLF | bearish | 2.501 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:05+00:00 | XLE | bearish | 2.503 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:05+00:00 | XLF | bearish | 2.501 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:24+00:00 | XLK | bearish | 2.466 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:24+00:00 | XLK | bearish | 2.466 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:52:04+00:00 | BLK | bearish | 3.776 | order_validation_failed | Order $1157.79 exceeds max position size $825.00 |
| 2026-01-15T19:52:04+00:00 | BLK | bearish | 3.776 | order_validation_failed | Order $1157.79 exceeds max position size $825.00 |
| 2026-01-15T19:52:08+00:00 | COST | bullish | 4.760 | order_validation_failed | Order $953.89 exceeds max position size $825.00 |
| 2026-01-15T19:52:08+00:00 | COST | bullish | 4.760 | order_validation_failed | Order $953.89 exceeds max position size $825.00 |
| 2026-01-15T19:53:06+00:00 | GS | bullish | 3.870 | order_validation_failed | Order $974.74 exceeds max position size $825.00 |
| 2026-01-15T19:53:09+00:00 | BAC | bearish | 2.798 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:09+00:00 | GS | bullish | 3.869 | order_validation_failed | Order $974.74 exceeds max position size $825.00 |
| 2026-01-15T19:53:13+00:00 | BAC | bearish | 2.798 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:13+00:00 | C | bearish | 2.722 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:13+00:00 | AMD | bearish | 2.642 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:16+00:00 | JPM | bearish | 2.591 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:17+00:00 | C | bearish | 2.722 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:17+00:00 | AMD | bearish | 2.642 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:17+00:00 | XLE | bearish | 2.479 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:17+00:00 | JPM | bearish | 2.591 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:20+00:00 | XLF | bearish | 2.478 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:20+00:00 | XLK | bearish | 2.443 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:20+00:00 | XLE | bearish | 2.479 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:23+00:00 | XLF | bearish | 2.478 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:23+00:00 | XLK | bearish | 2.443 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:51+00:00 | COST | bearish | 3.766 | order_validation_failed | Order $953.99 exceeds max position size $825.00 |
| 2026-01-15T19:53:52+00:00 | BLK | bearish | 3.745 | order_validation_failed | Order $1158.24 exceeds max position size $825.00 |
| 2026-01-15T19:54:03+00:00 | COST | bearish | 3.765 | order_validation_failed | Order $953.88 exceeds max position size $825.00 |
| 2026-01-15T19:54:07+00:00 | BLK | bearish | 3.743 | order_validation_failed | Order $1158.01 exceeds max position size $825.00 |
| 2026-01-15T19:54:22+00:00 | GS | bullish | 3.840 | order_validation_failed | Order $974.48 exceeds max position size $825.00 |
| 2026-01-15T19:54:25+00:00 | BAC | bearish | 2.777 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:32+00:00 | C | bearish | 2.702 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:32+00:00 | AMD | bearish | 2.623 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:35+00:00 | JPM | bearish | 2.572 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:35+00:00 | XLE | bearish | 2.462 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:35+00:00 | XLF | bearish | 2.461 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:49+00:00 | GS | bullish | 3.839 | order_validation_failed | Order $975.00 exceeds max position size $825.00 |
| 2026-01-15T19:54:52+00:00 | BAC | bearish | 2.776 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:53+00:00 | C | bearish | 2.701 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:53+00:00 | AMD | bearish | 2.622 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:56+00:00 | JPM | bearish | 2.571 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:59+00:00 | XLE | bearish | 2.461 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:55:00+00:00 | XLF | bearish | 2.460 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:55:15+00:00 | COST | bearish | 3.742 | order_validation_failed | Order $953.85 exceeds max position size $825.00 |
| 2026-01-15T19:55:16+00:00 | BLK | bearish | 3.721 | order_validation_failed | Order $1157.66 exceeds max position size $825.00 |
| 2026-01-15T19:55:40+00:00 | COST | bearish | 3.739 | order_validation_failed | Order $953.85 exceeds max position size $825.00 |
| 2026-01-15T19:55:47+00:00 | BLK | bearish | 3.719 | order_validation_failed | Order $1157.03 exceeds max position size $825.00 |
| 2026-01-15T19:55:54+00:00 | GS | bullish | 3.817 | order_validation_failed | Order $974.78 exceeds max position size $825.00 |
| 2026-01-15T19:55:54+00:00 | BAC | bearish | 2.761 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:01+00:00 | C | bearish | 2.687 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:01+00:00 | AMD | bearish | 2.608 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:04+00:00 | JPM | bearish | 2.558 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:07+00:00 | XLE | bearish | 2.449 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:07+00:00 | XLF | bearish | 2.447 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:15+00:00 | GS | bullish | 3.815 | order_validation_failed | Order $974.50 exceeds max position size $825.00 |
| 2026-01-15T19:56:18+00:00 | BAC | bearish | 2.759 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:22+00:00 | C | bearish | 2.685 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:22+00:00 | AMD | bearish | 2.606 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:22+00:00 | JPM | bearish | 2.556 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:25+00:00 | XLE | bearish | 2.447 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:25+00:00 | XLF | bearish | 2.445 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:44+00:00 | COST | bearish | 3.719 | order_validation_failed | Order $953.80 exceeds max position size $825.00 |
| 2026-01-15T19:56:48+00:00 | BLK | bearish | 3.698 | order_validation_failed | Order $1157.67 exceeds max position size $825.00 |
| 2026-01-15T19:57:01+00:00 | COST | bearish | 3.715 | order_validation_failed | Order $954.10 exceeds max position size $825.00 |

<details>
<summary>Full blocked-trade ledger – 570 rows</summary>

| Time (UTC) | Symbol | Direction | Score | Reason | Details |
| --- | --- | --- | --- | --- | --- |
| 2026-01-15T16:00:22+00:00 | BLK | bullish | 4.030 | order_validation_failed | Order $1148.00 exceeds max position size $825.00 |
| 2026-01-15T16:00:22+00:00 | BLK | bullish | 4.031 | order_validation_failed | Order $1148.00 exceeds max position size $825.00 |
| 2026-01-15T16:01:37+00:00 | C | bearish | 3.619 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | C | bearish | 3.619 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | V | bearish | 3.597 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | V | bearish | 3.597 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLF | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLF | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLE | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLE | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLP | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | XLP | bearish | 3.567 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:37+00:00 | BA | bearish | 3.559 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | BA | bearish | 3.559 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | AAPL | bullish | 3.535 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | AAPL | bullish | 3.535 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | NVDA | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:40+00:00 | NVDA | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | COST | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | COST | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | F | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | F | bearish | 3.528 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | XLK | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | XLK | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | DIA | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | DIA | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | PLTR | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:43+00:00 | PLTR | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:44+00:00 | SLB | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:44+00:00 | SLB | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | JPM | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | JPM | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | XLV | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | XLV | bearish | 3.495 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | RIVN | bearish | 3.485 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | RIVN | bearish | 3.485 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | QQQ | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | QQQ | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | SPY | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:47+00:00 | SPY | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | CVX | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | CVX | bearish | 3.481 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | NFLX | bearish | 3.467 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | NFLX | bearish | 3.467 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | GOOGL | bullish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | GOOGL | bullish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | PFE | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | PFE | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:50+00:00 | JNJ | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | JNJ | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | GM | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | GM | bearish | 3.445 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | MA | bullish | 3.382 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | MA | bullish | 3.382 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | GS | bearish | 3.380 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | GS | bearish | 3.380 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | LCID | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | LCID | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | SOFI | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:53+00:00 | SOFI | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:54+00:00 | COP | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | COP | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | AMD | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | AMD | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | WMT | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | WMT | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | XLI | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | XLI | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | MSFT | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | MSFT | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | UNH | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:01:57+00:00 | UNH | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | INTC | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | INTC | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | IWM | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | MRNA | bearish | 3.351 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | IWM | bearish | 3.358 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | COIN | bearish | 3.312 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | MRNA | bearish | 3.351 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | CAT | bearish | 3.198 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | COIN | bearish | 3.312 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | TSLA | bullish | 3.068 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:00+00:00 | CAT | bearish | 3.198 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:03+00:00 | TSLA | bullish | 3.068 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:03+00:00 | AMZN | bearish | 3.058 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:03+00:00 | AMZN | bearish | 3.058 | max_new_positions_per_cycle | — |
| 2026-01-15T16:02:45+00:00 | BLK | bullish | 4.376 | order_validation_failed | Order $1149.61 exceeds max position size $825.00 |
| 2026-01-15T16:03:03+00:00 | BLK | bullish | 4.376 | order_validation_failed | Order $1150.60 exceeds max position size $825.00 |
| 2026-01-15T16:05:08+00:00 | BLK | bullish | 3.934 | order_validation_failed | Order $1147.29 exceeds max position size $825.00 |
| 2026-01-15T16:05:08+00:00 | BLK | bullish | 3.933 | order_validation_failed | Order $1147.29 exceeds max position size $825.00 |
| 2026-01-15T16:06:33+00:00 | BLK | bullish | 4.398 | order_validation_failed | Order $1146.40 exceeds max position size $825.00 |
| 2026-01-15T16:06:33+00:00 | BLK | bullish | 4.397 | order_validation_failed | Order $1146.40 exceeds max position size $825.00 |
| 2026-01-15T16:07:47+00:00 | MRNA | bearish | 3.242 | symbol_on_cooldown | — |
| 2026-01-15T16:08:05+00:00 | MS | bullish | 3.175 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:05+00:00 | META | bullish | 3.120 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:05+00:00 | WFC | bullish | 3.029 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:05+00:00 | TSLA | bullish | 2.969 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T16:08:08+00:00 | C | bearish | 2.718 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T16:08:22+00:00 | META | bullish | 3.120 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:22+00:00 | WFC | bullish | 3.028 | max_new_positions_per_cycle | — |
| 2026-01-15T16:08:22+00:00 | TSLA | bullish | 2.969 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T16:08:22+00:00 | C | bearish | 2.717 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:44:56+00:00 | COST | bullish | 4.320 | order_validation_failed | Order $954.21 exceeds max position size $825.00 |
| 2026-01-15T19:45:02+00:00 | COST | bullish | 4.320 | order_validation_failed | Order $954.21 exceeds max position size $825.00 |
| 2026-01-15T19:46:03+00:00 | V | bullish | 3.984 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:03+00:00 | HD | bullish | 3.908 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:07+00:00 | NVDA | bullish | 3.571 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:07+00:00 | MS | bullish | 3.480 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:07+00:00 | LOW | bullish | 3.368 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:07+00:00 | BAC | bearish | 2.434 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:46:12+00:00 | V | bullish | 3.985 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:15+00:00 | COIN | bullish | 3.942 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:15+00:00 | HD | bullish | 3.910 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:15+00:00 | PLTR | bullish | 3.706 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:15+00:00 | NVDA | bullish | 3.572 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:18+00:00 | MS | bullish | 3.480 | max_new_positions_per_cycle | — |
| 2026-01-15T19:46:18+00:00 | BAC | bearish | 2.435 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:46:46+00:00 | COST | bullish | 4.276 | order_validation_failed | Order $954.43 exceeds max position size $825.00 |
| 2026-01-15T19:46:53+00:00 | COST | bullish | 4.273 | order_validation_failed | Order $954.42 exceeds max position size $825.00 |
| 2026-01-15T19:48:31+00:00 | GS | bullish | 3.358 | order_validation_failed | Order $974.00 exceeds max position size $825.00 |
| 2026-01-15T19:48:35+00:00 | GS | bullish | 3.355 | order_validation_failed | Order $973.99 exceeds max position size $825.00 |
| 2026-01-15T19:49:37+00:00 | COST | bullish | 4.812 | order_validation_failed | Order $953.98 exceeds max position size $825.00 |
| 2026-01-15T19:49:37+00:00 | COST | bullish | 4.811 | order_validation_failed | Order $953.98 exceeds max position size $825.00 |
| 2026-01-15T19:50:09+00:00 | GS | bullish | 3.908 | order_validation_failed | Order $975.03 exceeds max position size $825.00 |
| 2026-01-15T19:50:12+00:00 | GS | bullish | 3.908 | order_validation_failed | Order $975.12 exceeds max position size $825.00 |
| 2026-01-15T19:50:12+00:00 | BAC | bearish | 2.825 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:15+00:00 | BAC | bearish | 2.825 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:16+00:00 | C | bearish | 2.749 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:16+00:00 | BLK | bearish | 2.677 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:19+00:00 | AMD | bearish | 2.668 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:19+00:00 | C | bearish | 2.749 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:19+00:00 | BLK | bearish | 2.677 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:20+00:00 | AMD | bearish | 2.668 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:44+00:00 | JPM | bearish | 2.616 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:50:44+00:00 | JPM | bearish | 2.616 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:02+00:00 | XLE | bearish | 2.503 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:02+00:00 | XLF | bearish | 2.501 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:05+00:00 | XLE | bearish | 2.503 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:05+00:00 | XLF | bearish | 2.501 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:24+00:00 | XLK | bearish | 2.466 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:51:24+00:00 | XLK | bearish | 2.466 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:52:04+00:00 | BLK | bearish | 3.776 | order_validation_failed | Order $1157.79 exceeds max position size $825.00 |
| 2026-01-15T19:52:04+00:00 | BLK | bearish | 3.776 | order_validation_failed | Order $1157.79 exceeds max position size $825.00 |
| 2026-01-15T19:52:08+00:00 | COST | bullish | 4.760 | order_validation_failed | Order $953.89 exceeds max position size $825.00 |
| 2026-01-15T19:52:08+00:00 | COST | bullish | 4.760 | order_validation_failed | Order $953.89 exceeds max position size $825.00 |
| 2026-01-15T19:53:06+00:00 | GS | bullish | 3.870 | order_validation_failed | Order $974.74 exceeds max position size $825.00 |
| 2026-01-15T19:53:09+00:00 | BAC | bearish | 2.798 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:09+00:00 | GS | bullish | 3.869 | order_validation_failed | Order $974.74 exceeds max position size $825.00 |
| 2026-01-15T19:53:13+00:00 | BAC | bearish | 2.798 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:13+00:00 | C | bearish | 2.722 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:13+00:00 | AMD | bearish | 2.642 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:16+00:00 | JPM | bearish | 2.591 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:17+00:00 | C | bearish | 2.722 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:17+00:00 | AMD | bearish | 2.642 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:17+00:00 | XLE | bearish | 2.479 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:17+00:00 | JPM | bearish | 2.591 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:20+00:00 | XLF | bearish | 2.478 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:20+00:00 | XLK | bearish | 2.443 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:20+00:00 | XLE | bearish | 2.479 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:23+00:00 | XLF | bearish | 2.478 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:23+00:00 | XLK | bearish | 2.443 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:53:51+00:00 | COST | bearish | 3.766 | order_validation_failed | Order $953.99 exceeds max position size $825.00 |
| 2026-01-15T19:53:52+00:00 | BLK | bearish | 3.745 | order_validation_failed | Order $1158.24 exceeds max position size $825.00 |
| 2026-01-15T19:54:03+00:00 | COST | bearish | 3.765 | order_validation_failed | Order $953.88 exceeds max position size $825.00 |
| 2026-01-15T19:54:07+00:00 | BLK | bearish | 3.743 | order_validation_failed | Order $1158.01 exceeds max position size $825.00 |
| 2026-01-15T19:54:22+00:00 | GS | bullish | 3.840 | order_validation_failed | Order $974.48 exceeds max position size $825.00 |
| 2026-01-15T19:54:25+00:00 | BAC | bearish | 2.777 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:32+00:00 | C | bearish | 2.702 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:32+00:00 | AMD | bearish | 2.623 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:35+00:00 | JPM | bearish | 2.572 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:35+00:00 | XLE | bearish | 2.462 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:35+00:00 | XLF | bearish | 2.461 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:49+00:00 | GS | bullish | 3.839 | order_validation_failed | Order $975.00 exceeds max position size $825.00 |
| 2026-01-15T19:54:52+00:00 | BAC | bearish | 2.776 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:53+00:00 | C | bearish | 2.701 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:53+00:00 | AMD | bearish | 2.622 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:56+00:00 | JPM | bearish | 2.571 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:54:59+00:00 | XLE | bearish | 2.461 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:55:00+00:00 | XLF | bearish | 2.460 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:55:15+00:00 | COST | bearish | 3.742 | order_validation_failed | Order $953.85 exceeds max position size $825.00 |
| 2026-01-15T19:55:16+00:00 | BLK | bearish | 3.721 | order_validation_failed | Order $1157.66 exceeds max position size $825.00 |
| 2026-01-15T19:55:40+00:00 | COST | bearish | 3.739 | order_validation_failed | Order $953.85 exceeds max position size $825.00 |
| 2026-01-15T19:55:47+00:00 | BLK | bearish | 3.719 | order_validation_failed | Order $1157.03 exceeds max position size $825.00 |
| 2026-01-15T19:55:54+00:00 | GS | bullish | 3.817 | order_validation_failed | Order $974.78 exceeds max position size $825.00 |
| 2026-01-15T19:55:54+00:00 | BAC | bearish | 2.761 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:01+00:00 | C | bearish | 2.687 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:01+00:00 | AMD | bearish | 2.608 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:04+00:00 | JPM | bearish | 2.558 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:07+00:00 | XLE | bearish | 2.449 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:07+00:00 | XLF | bearish | 2.447 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:15+00:00 | GS | bullish | 3.815 | order_validation_failed | Order $974.50 exceeds max position size $825.00 |
| 2026-01-15T19:56:18+00:00 | BAC | bearish | 2.759 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:22+00:00 | C | bearish | 2.685 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:22+00:00 | AMD | bearish | 2.606 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:22+00:00 | JPM | bearish | 2.556 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:25+00:00 | XLE | bearish | 2.447 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:25+00:00 | XLF | bearish | 2.445 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:56:44+00:00 | COST | bearish | 3.719 | order_validation_failed | Order $953.80 exceeds max position size $825.00 |
| 2026-01-15T19:56:48+00:00 | BLK | bearish | 3.698 | order_validation_failed | Order $1157.67 exceeds max position size $825.00 |
| 2026-01-15T19:57:01+00:00 | COST | bearish | 3.715 | order_validation_failed | Order $954.10 exceeds max position size $825.00 |
| 2026-01-15T19:57:05+00:00 | BLK | bearish | 3.694 | order_validation_failed | Order $1157.47 exceeds max position size $825.00 |
| 2026-01-15T19:57:30+00:00 | GS | bullish | 3.796 | order_validation_failed | Order $973.89 exceeds max position size $825.00 |
| 2026-01-15T19:57:30+00:00 | BAC | bearish | 2.745 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:37+00:00 | C | bearish | 2.671 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:37+00:00 | AMD | bearish | 2.593 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:40+00:00 | JPM | bearish | 2.543 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:40+00:00 | XLE | bearish | 2.435 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:40+00:00 | XLF | bearish | 2.434 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:44+00:00 | GS | bullish | 3.791 | order_validation_failed | Order $974.63 exceeds max position size $825.00 |
| 2026-01-15T19:57:47+00:00 | BAC | bearish | 2.742 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:48+00:00 | C | bearish | 2.668 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:51+00:00 | AMD | bearish | 2.591 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:51+00:00 | JPM | bearish | 2.542 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:58+00:00 | XLE | bearish | 2.433 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:57:58+00:00 | XLF | bearish | 2.432 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:58:14+00:00 | COST | bearish | 3.693 | order_validation_failed | Order $954.29 exceeds max position size $825.00 |
| 2026-01-15T19:58:15+00:00 | BLK | bearish | 3.672 | order_validation_failed | Order $1158.59 exceeds max position size $825.00 |
| 2026-01-15T19:58:51+00:00 | GS | bullish | 3.770 | order_validation_failed | Order $974.51 exceeds max position size $825.00 |
| 2026-01-15T19:59:00+00:00 | COST | bearish | 3.691 | order_validation_failed | Order $954.20 exceeds max position size $825.00 |
| 2026-01-15T19:59:01+00:00 | BAC | bearish | 2.728 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:59:04+00:00 | BLK | bearish | 3.669 | order_validation_failed | Order $1159.58 exceeds max position size $825.00 |
| 2026-01-15T19:59:08+00:00 | C | bearish | 2.654 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:59:08+00:00 | AMD | bearish | 2.577 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:59:11+00:00 | JPM | bearish | 2.528 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:59:30+00:00 | GS | bullish | 3.768 | order_validation_failed | Order $975.15 exceeds max position size $825.00 |
| 2026-01-15T19:59:30+00:00 | BAC | bearish | 2.726 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:59:38+00:00 | C | bearish | 2.652 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:59:38+00:00 | AMD | bearish | 2.576 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:59:38+00:00 | JPM | bearish | 2.526 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T19:59:53+00:00 | COST | bearish | 3.669 | order_validation_failed | Order $954.16 exceeds max position size $825.00 |
| 2026-01-15T19:59:56+00:00 | BLK | bearish | 3.649 | order_validation_failed | Order $1159.59 exceeds max position size $825.00 |
| 2026-01-15T20:00:13+00:00 | GS | bullish | 3.748 | order_validation_failed | Order $974.56 exceeds max position size $825.00 |
| 2026-01-15T20:00:13+00:00 | BAC | bearish | 2.712 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:00:20+00:00 | C | bearish | 2.639 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:00:20+00:00 | AMD | bearish | 2.562 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:00:21+00:00 | JPM | bearish | 2.514 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:00:37+00:00 | BLK | bearish | 3.793 | order_validation_failed | Order $1158.43 exceeds max position size $825.00 |
| 2026-01-15T20:00:42+00:00 | COST | bearish | 3.658 | order_validation_failed | Order $954.20 exceeds max position size $825.00 |
| 2026-01-15T20:00:56+00:00 | BLK | bearish | 3.785 | order_validation_failed | Order $1159.15 exceeds max position size $825.00 |
| 2026-01-15T20:01:03+00:00 | COST | bearish | 3.649 | order_validation_failed | Order $954.35 exceeds max position size $825.00 |
| 2026-01-15T20:01:18+00:00 | GS | bullish | 3.738 | order_validation_failed | Order $974.79 exceeds max position size $825.00 |
| 2026-01-15T20:01:18+00:00 | BAC | bearish | 2.704 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:01:22+00:00 | C | bearish | 2.632 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:01:22+00:00 | AMD | bearish | 2.555 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:01:25+00:00 | JPM | bearish | 2.507 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:01:39+00:00 | GS | bullish | 3.730 | order_validation_failed | Order $974.61 exceeds max position size $825.00 |
| 2026-01-15T20:01:39+00:00 | BAC | bearish | 2.700 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:01:40+00:00 | C | bearish | 2.626 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:01:40+00:00 | AMD | bearish | 2.550 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:01:43+00:00 | JPM | bearish | 2.502 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:02:02+00:00 | BLK | bearish | 3.766 | order_validation_failed | Order $1160.22 exceeds max position size $825.00 |
| 2026-01-15T20:02:09+00:00 | COST | bearish | 3.631 | order_validation_failed | Order $954.23 exceeds max position size $825.00 |
| 2026-01-15T20:02:23+00:00 | BLK | bearish | 3.763 | order_validation_failed | Order $1160.12 exceeds max position size $825.00 |
| 2026-01-15T20:02:27+00:00 | COST | bearish | 3.628 | order_validation_failed | Order $954.53 exceeds max position size $825.00 |
| 2026-01-15T20:02:53+00:00 | GS | bullish | 3.709 | order_validation_failed | Order $975.85 exceeds max position size $825.00 |
| 2026-01-15T20:02:57+00:00 | BAC | bearish | 2.685 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:02:57+00:00 | GS | bullish | 3.712 | order_validation_failed | Order $975.90 exceeds max position size $825.00 |
| 2026-01-15T20:02:57+00:00 | BAC | bearish | 2.687 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:03:01+00:00 | C | bearish | 2.613 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:03:01+00:00 | AMD | bearish | 2.536 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:03:01+00:00 | JPM | bearish | 2.489 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:03:04+00:00 | C | bearish | 2.614 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:03:04+00:00 | AMD | bearish | 2.538 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:03:05+00:00 | JPM | bearish | 2.490 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:03:31+00:00 | BLK | bearish | 3.739 | order_validation_failed | Order $1160.36 exceeds max position size $825.00 |
| 2026-01-15T20:03:35+00:00 | COST | bearish | 3.607 | order_validation_failed | Order $954.44 exceeds max position size $825.00 |
| 2026-01-15T20:04:05+00:00 | GS | bullish | 3.690 | order_validation_failed | Order $975.00 exceeds max position size $825.00 |
| 2026-01-15T20:04:05+00:00 | BAC | bearish | 2.669 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:04:09+00:00 | C | bearish | 2.598 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:04:09+00:00 | AMD | bearish | 2.524 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:04:09+00:00 | JPM | bearish | 2.476 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:04:16+00:00 | BLK | bearish | 3.738 | order_validation_failed | Order $1160.43 exceeds max position size $825.00 |
| 2026-01-15T20:04:24+00:00 | COST | bearish | 3.605 | order_validation_failed | Order $954.30 exceeds max position size $825.00 |
| 2026-01-15T20:04:43+00:00 | BLK | bearish | 3.721 | order_validation_failed | Order $1160.21 exceeds max position size $825.00 |
| 2026-01-15T20:04:50+00:00 | COST | bearish | 3.589 | order_validation_failed | Order $954.49 exceeds max position size $825.00 |
| 2026-01-15T20:05:01+00:00 | GS | bullish | 3.688 | order_validation_failed | Order $976.00 exceeds max position size $825.00 |
| 2026-01-15T20:05:01+00:00 | BAC | bearish | 2.668 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:05:02+00:00 | C | bearish | 2.597 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:05:02+00:00 | AMD | bearish | 2.523 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:05:05+00:00 | JPM | bearish | 2.474 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:05:19+00:00 | GS | bullish | 3.673 | order_validation_failed | Order $976.60 exceeds max position size $825.00 |
| 2026-01-15T20:05:22+00:00 | BAC | bearish | 2.658 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:05:24+00:00 | C | bearish | 2.587 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:05:24+00:00 | AMD | bearish | 2.513 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:05:24+00:00 | JPM | bearish | 2.465 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:05:43+00:00 | BLK | bearish | 3.705 | order_validation_failed | Order $1161.16 exceeds max position size $825.00 |
| 2026-01-15T20:05:48+00:00 | COST | bearish | 3.574 | order_validation_failed | Order $954.12 exceeds max position size $825.00 |
| 2026-01-15T20:05:55+00:00 | BLK | bullish | 5.525 | order_validation_failed | Order $1161.45 exceeds max position size $825.00 |
| 2026-01-15T20:06:16+00:00 | COST | bearish | 3.568 | order_validation_failed | Order $954.46 exceeds max position size $825.00 |
| 2026-01-15T20:06:23+00:00 | GS | bullish | 3.658 | order_validation_failed | Order $975.82 exceeds max position size $825.00 |
| 2026-01-15T20:06:24+00:00 | BAC | bearish | 2.648 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:06:24+00:00 | C | bearish | 2.577 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:06:24+00:00 | AMD | bearish | 2.503 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:06:27+00:00 | JPM | bearish | 2.455 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:06:48+00:00 | GS | bullish | 3.653 | order_validation_failed | Order $975.20 exceeds max position size $825.00 |
| 2026-01-15T20:06:48+00:00 | BAC | bearish | 2.643 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:06:49+00:00 | C | bearish | 2.573 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:06:50+00:00 | AMD | bearish | 2.499 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:06:50+00:00 | JPM | bearish | 2.453 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:06:57+00:00 | BLK | bullish | 5.498 | order_validation_failed | Order $1161.43 exceeds max position size $825.00 |
| 2026-01-15T20:07:09+00:00 | COST | bearish | 3.552 | order_validation_failed | Order $954.39 exceeds max position size $825.00 |
| 2026-01-15T20:07:26+00:00 | GS | bullish | 3.637 | order_validation_failed | Order $975.00 exceeds max position size $825.00 |
| 2026-01-15T20:07:26+00:00 | BAC | bearish | 2.632 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:07:30+00:00 | C | bearish | 2.562 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:07:30+00:00 | AMD | bearish | 2.489 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:07:30+00:00 | JPM | bearish | 2.443 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:07:52+00:00 | BLK | bullish | 5.474 | order_validation_failed | Order $1161.54 exceeds max position size $825.00 |
| 2026-01-15T20:07:56+00:00 | BLK | bullish | 5.472 | order_validation_failed | Order $1161.29 exceeds max position size $825.00 |
| 2026-01-15T20:08:03+00:00 | COST | bearish | 3.538 | order_validation_failed | Order $954.15 exceeds max position size $825.00 |
| 2026-01-15T20:08:17+00:00 | COST | bearish | 3.536 | order_validation_failed | Order $954.41 exceeds max position size $825.00 |
| 2026-01-15T20:08:30+00:00 | GS | bullish | 3.624 | order_validation_failed | Order $976.13 exceeds max position size $825.00 |
| 2026-01-15T20:08:30+00:00 | BAC | bearish | 2.623 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:08:34+00:00 | C | bearish | 2.552 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:08:34+00:00 | AMD | bearish | 2.480 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:08:34+00:00 | JPM | bearish | 2.434 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:08:53+00:00 | GS | bullish | 3.622 | order_validation_failed | Order $975.81 exceeds max position size $825.00 |
| 2026-01-15T20:08:54+00:00 | BAC | bearish | 2.622 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:09:00+00:00 | C | bearish | 2.551 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:09:01+00:00 | AMD | bearish | 2.479 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:09:01+00:00 | JPM | bearish | 2.432 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:09:02+00:00 | BLK | bullish | 5.447 | order_validation_failed | Order $1159.32 exceeds max position size $825.00 |
| 2026-01-15T20:09:18+00:00 | COST | bearish | 3.520 | order_validation_failed | Order $954.54 exceeds max position size $825.00 |
| 2026-01-15T20:09:34+00:00 | BLK | bullish | 5.432 | order_validation_failed | Order $1158.28 exceeds max position size $825.00 |
| 2026-01-15T20:09:45+00:00 | COST | bearish | 3.511 | order_validation_failed | Order $954.56 exceeds max position size $825.00 |
| 2026-01-15T20:09:58+00:00 | GS | bullish | 3.607 | order_validation_failed | Order $975.07 exceeds max position size $825.00 |
| 2026-01-15T20:10:01+00:00 | BAC | bearish | 2.611 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:10:11+00:00 | C | bearish | 2.542 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:10:11+00:00 | AMD | bearish | 2.469 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:10:15+00:00 | GS | bullish | 3.598 | order_validation_failed | Order $974.85 exceeds max position size $825.00 |
| 2026-01-15T20:10:15+00:00 | BAC | bearish | 2.605 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:10:23+00:00 | C | bearish | 2.535 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:10:23+00:00 | AMD | bearish | 2.463 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:10:37+00:00 | BLK | bullish | 5.406 | order_validation_failed | Order $1157.79 exceeds max position size $825.00 |
| 2026-01-15T20:10:50+00:00 | COST | bearish | 3.495 | order_validation_failed | Order $954.46 exceeds max position size $825.00 |
| 2026-01-15T20:10:50+00:00 | BLK | bullish | 5.402 | order_validation_failed | Order $1157.74 exceeds max position size $825.00 |
| 2026-01-15T20:11:09+00:00 | COST | bearish | 3.492 | order_validation_failed | Order $954.65 exceeds max position size $825.00 |
| 2026-01-15T20:11:35+00:00 | GS | bullish | 3.581 | order_validation_failed | Order $975.78 exceeds max position size $825.00 |
| 2026-01-15T20:11:35+00:00 | BAC | bearish | 2.592 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:11:38+00:00 | GS | bullish | 3.583 | order_validation_failed | Order $975.78 exceeds max position size $825.00 |
| 2026-01-15T20:11:38+00:00 | BAC | bearish | 2.594 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:11:42+00:00 | C | bearish | 2.524 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:11:42+00:00 | AMD | bearish | 2.452 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:11:42+00:00 | C | bearish | 2.524 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:11:42+00:00 | AMD | bearish | 2.453 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:12:16+00:00 | BLK | bullish | 5.365 | order_validation_failed | Order $1156.96 exceeds max position size $825.00 |
| 2026-01-15T20:12:17+00:00 | BLK | bullish | 5.365 | order_validation_failed | Order $1156.96 exceeds max position size $825.00 |
| 2026-01-15T20:12:23+00:00 | COST | bearish | 3.469 | order_validation_failed | Order $955.15 exceeds max position size $825.00 |
| 2026-01-15T20:12:27+00:00 | COST | bearish | 3.470 | order_validation_failed | Order $955.15 exceeds max position size $825.00 |
| 2026-01-15T20:12:56+00:00 | GS | bullish | 3.559 | order_validation_failed | Order $976.13 exceeds max position size $825.00 |
| 2026-01-15T20:12:56+00:00 | BAC | bearish | 2.576 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:13:01+00:00 | C | bearish | 2.508 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:13:01+00:00 | AMD | bearish | 2.437 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:13:03+00:00 | GS | bullish | 3.559 | order_validation_failed | Order $975.92 exceeds max position size $825.00 |
| 2026-01-15T20:13:03+00:00 | BAC | bearish | 2.577 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:13:07+00:00 | C | bearish | 2.508 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:13:07+00:00 | AMD | bearish | 2.437 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:13:25+00:00 | BLK | bullish | 5.336 | order_validation_failed | Order $1158.89 exceeds max position size $825.00 |
| 2026-01-15T20:13:37+00:00 | COST | bearish | 3.451 | order_validation_failed | Order $955.26 exceeds max position size $825.00 |
| 2026-01-15T20:13:44+00:00 | BLK | bullish | 5.332 | order_validation_failed | Order $1158.91 exceeds max position size $825.00 |
| 2026-01-15T20:14:01+00:00 | GS | bullish | 3.542 | order_validation_failed | Order $976.14 exceeds max position size $825.00 |
| 2026-01-15T20:14:01+00:00 | BAC | bearish | 2.564 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:14:08+00:00 | C | bearish | 2.497 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:14:12+00:00 | COST | bearish | 3.449 | order_validation_failed | Order $955.14 exceeds max position size $825.00 |
| 2026-01-15T20:14:35+00:00 | GS | bullish | 3.540 | order_validation_failed | Order $975.83 exceeds max position size $825.00 |
| 2026-01-15T20:14:35+00:00 | BAC | bearish | 2.562 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:14:36+00:00 | C | bearish | 2.495 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:15:04+00:00 | BLK | bullish | 5.300 | order_validation_failed | Order $1158.40 exceeds max position size $825.00 |
| 2026-01-15T20:15:08+00:00 | BLK | bullish | 5.297 | order_validation_failed | Order $1158.40 exceeds max position size $825.00 |
| 2026-01-15T20:15:31+00:00 | COST | bearish | 3.426 | order_validation_failed | Order $954.97 exceeds max position size $825.00 |
| 2026-01-15T20:15:41+00:00 | COST | bearish | 3.429 | order_validation_failed | Order $955.09 exceeds max position size $825.00 |
| 2026-01-15T20:16:07+00:00 | GS | bullish | 3.520 | order_validation_failed | Order $974.62 exceeds max position size $825.00 |
| 2026-01-15T20:16:08+00:00 | BAC | bearish | 2.548 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:16:11+00:00 | GS | bullish | 3.521 | order_validation_failed | Order $974.62 exceeds max position size $825.00 |
| 2026-01-15T20:16:11+00:00 | BAC | bearish | 2.549 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:16:14+00:00 | C | bearish | 2.479 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:16:15+00:00 | C | bearish | 2.481 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:16:43+00:00 | BLK | bullish | 5.261 | order_validation_failed | Order $1157.97 exceeds max position size $825.00 |
| 2026-01-15T20:16:49+00:00 | GOOGL | bullish | 5.602 | symbol_on_cooldown | — |
| 2026-01-15T20:16:53+00:00 | BLK | bullish | 5.256 | order_validation_failed | Order $1158.37 exceeds max position size $825.00 |
| 2026-01-15T20:17:00+00:00 | COST | bearish | 3.404 | order_validation_failed | Order $954.63 exceeds max position size $825.00 |
| 2026-01-15T20:17:22+00:00 | COST | bearish | 3.400 | order_validation_failed | Order $954.68 exceeds max position size $825.00 |
| 2026-01-15T20:17:32+00:00 | GS | bullish | 3.497 | order_validation_failed | Order $974.74 exceeds max position size $825.00 |
| 2026-01-15T20:17:32+00:00 | BAC | bearish | 2.533 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:17:36+00:00 | C | bearish | 2.466 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:17:51+00:00 | GS | bullish | 3.494 | order_validation_failed | Order $974.74 exceeds max position size $825.00 |
| 2026-01-15T20:17:51+00:00 | BAC | bearish | 2.530 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:17:57+00:00 | C | bearish | 2.464 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:18:03+00:00 | BLK | bullish | 5.225 | order_validation_failed | Order $1157.24 exceeds max position size $825.00 |
| 2026-01-15T20:18:19+00:00 | COST | bearish | 3.382 | order_validation_failed | Order $954.74 exceeds max position size $825.00 |
| 2026-01-15T20:18:33+00:00 | BLK | bullish | 5.216 | order_validation_failed | Order $1157.46 exceeds max position size $825.00 |
| 2026-01-15T20:18:44+00:00 | GS | bullish | 3.476 | order_validation_failed | Order $974.58 exceeds max position size $825.00 |
| 2026-01-15T20:18:44+00:00 | BAC | bearish | 2.517 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:18:51+00:00 | C | bearish | 2.452 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:18:55+00:00 | COST | bearish | 3.376 | order_validation_failed | Order $954.72 exceeds max position size $825.00 |
| 2026-01-15T20:19:19+00:00 | GS | bullish | 3.472 | order_validation_failed | Order $974.71 exceeds max position size $825.00 |
| 2026-01-15T20:19:22+00:00 | BAC | bearish | 2.514 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:19:23+00:00 | BLK | bullish | 5.197 | order_validation_failed | Order $1156.99 exceeds max position size $825.00 |
| 2026-01-15T20:19:26+00:00 | C | bearish | 2.448 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:19:41+00:00 | COST | bearish | 3.364 | order_validation_failed | Order $954.85 exceeds max position size $825.00 |
| 2026-01-15T20:19:59+00:00 | GS | bullish | 3.460 | order_validation_failed | Order $974.30 exceeds max position size $825.00 |
| 2026-01-15T20:19:59+00:00 | BAC | bearish | 2.506 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:20:04+00:00 | C | bearish | 2.440 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:20:11+00:00 | BLK | bullish | 5.176 | order_validation_failed | Order $1157.62 exceeds max position size $825.00 |
| 2026-01-15T20:20:24+00:00 | COST | bearish | 3.351 | order_validation_failed | Order $954.94 exceeds max position size $825.00 |
| 2026-01-15T20:20:45+00:00 | BLK | bullish | 5.166 | order_validation_failed | Order $1157.45 exceeds max position size $825.00 |
| 2026-01-15T20:20:49+00:00 | GS | bullish | 3.448 | order_validation_failed | Order $973.24 exceeds max position size $825.00 |
| 2026-01-15T20:20:49+00:00 | BAC | bearish | 2.497 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:20:56+00:00 | C | bearish | 2.431 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:21:29+00:00 | BLK | bullish | 5.148 | order_validation_failed | Order $1156.82 exceeds max position size $825.00 |
| 2026-01-15T20:21:32+00:00 | COST | bearish | 3.344 | order_validation_failed | Order $955.32 exceeds max position size $825.00 |
| 2026-01-15T20:21:43+00:00 | V | bearish | 3.463 | symbol_on_cooldown | — |
| 2026-01-15T20:21:46+00:00 | COST | bearish | 3.334 | order_validation_failed | Order $955.36 exceeds max position size $825.00 |
| 2026-01-15T20:22:01+00:00 | GS | bullish | 3.442 | order_validation_failed | Order $972.94 exceeds max position size $825.00 |
| 2026-01-15T20:22:01+00:00 | BAC | bearish | 2.493 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:22:19+00:00 | GS | bullish | 3.431 | order_validation_failed | Order $972.98 exceeds max position size $825.00 |
| 2026-01-15T20:22:19+00:00 | BAC | bearish | 2.485 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:22:44+00:00 | BLK | bullish | 5.117 | order_validation_failed | Order $1158.60 exceeds max position size $825.00 |
| 2026-01-15T20:22:45+00:00 | BLK | bullish | 5.116 | order_validation_failed | Order $1158.60 exceeds max position size $825.00 |
| 2026-01-15T20:22:59+00:00 | COST | bearish | 3.314 | order_validation_failed | Order $955.51 exceeds max position size $825.00 |
| 2026-01-15T20:23:03+00:00 | COST | bearish | 3.314 | order_validation_failed | Order $955.35 exceeds max position size $825.00 |
| 2026-01-15T20:23:28+00:00 | GS | bullish | 3.413 | order_validation_failed | Order $973.07 exceeds max position size $825.00 |
| 2026-01-15T20:23:29+00:00 | BAC | bearish | 2.471 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:23:39+00:00 | GS | bullish | 3.412 | order_validation_failed | Order $972.92 exceeds max position size $825.00 |
| 2026-01-15T20:23:39+00:00 | BAC | bearish | 2.471 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:24:03+00:00 | BLK | bullish | 5.088 | order_validation_failed | Order $1159.18 exceeds max position size $825.00 |
| 2026-01-15T20:24:09+00:00 | BLK | bullish | 5.084 | order_validation_failed | Order $1159.17 exceeds max position size $825.00 |
| 2026-01-15T20:24:16+00:00 | COST | bearish | 3.296 | order_validation_failed | Order $955.26 exceeds max position size $825.00 |
| 2026-01-15T20:24:33+00:00 | COST | bearish | 3.294 | order_validation_failed | Order $955.22 exceeds max position size $825.00 |
| 2026-01-15T20:24:45+00:00 | GS | bullish | 3.395 | order_validation_failed | Order $971.89 exceeds max position size $825.00 |
| 2026-01-15T20:24:45+00:00 | BAC | bearish | 2.460 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:25:03+00:00 | GS | bullish | 3.394 | order_validation_failed | Order $972.00 exceeds max position size $825.00 |
| 2026-01-15T20:25:03+00:00 | BAC | bearish | 2.458 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:25:13+00:00 | BLK | bullish | 5.059 | order_validation_failed | Order $1159.58 exceeds max position size $825.00 |
| 2026-01-15T20:25:27+00:00 | COST | bearish | 3.278 | order_validation_failed | Order $955.35 exceeds max position size $825.00 |
| 2026-01-15T20:25:40+00:00 | BLK | bullish | 5.054 | order_validation_failed | Order $1159.08 exceeds max position size $825.00 |
| 2026-01-15T20:25:56+00:00 | GS | bullish | 3.378 | order_validation_failed | Order $972.02 exceeds max position size $825.00 |
| 2026-01-15T20:25:56+00:00 | BAC | bearish | 2.447 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:26:05+00:00 | COST | bearish | 3.275 | order_validation_failed | Order $955.38 exceeds max position size $825.00 |
| 2026-01-15T20:26:19+00:00 | GS | bullish | 3.376 | order_validation_failed | Order $972.40 exceeds max position size $825.00 |
| 2026-01-15T20:26:19+00:00 | BAC | bearish | 2.445 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:27:23+00:00 | COST | bearish | 3.255 | order_validation_failed | Order $955.48 exceeds max position size $825.00 |
| 2026-01-15T20:27:23+00:00 | COST | bearish | 3.255 | order_validation_failed | Order $955.48 exceeds max position size $825.00 |
| 2026-01-15T20:27:30+00:00 | BLK | bullish | 4.100 | order_validation_failed | Order $1158.49 exceeds max position size $825.00 |
| 2026-01-15T20:27:33+00:00 | BLK | bullish | 4.100 | order_validation_failed | Order $1158.49 exceeds max position size $825.00 |
| 2026-01-15T20:27:33+00:00 | LCID | bearish | 2.993 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:27:33+00:00 | LCID | bearish | 2.993 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:27:59+00:00 | GS | bullish | 3.358 | order_validation_failed | Order $973.00 exceeds max position size $825.00 |
| 2026-01-15T20:27:59+00:00 | GS | bullish | 3.358 | order_validation_failed | Order $973.00 exceeds max position size $825.00 |
| 2026-01-15T20:27:59+00:00 | BAC | bearish | 2.432 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:27:59+00:00 | BAC | bearish | 2.432 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:28:40+00:00 | COST | bearish | 3.233 | order_validation_failed | Order $955.49 exceeds max position size $825.00 |
| 2026-01-15T20:28:44+00:00 | COST | bearish | 3.234 | order_validation_failed | Order $955.46 exceeds max position size $825.00 |
| 2026-01-15T20:28:47+00:00 | BLK | bullish | 4.073 | order_validation_failed | Order $1157.34 exceeds max position size $825.00 |
| 2026-01-15T20:28:50+00:00 | BLK | bullish | 4.074 | order_validation_failed | Order $1157.34 exceeds max position size $825.00 |
| 2026-01-15T20:28:50+00:00 | LCID | bearish | 2.974 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:28:54+00:00 | LCID | bearish | 2.974 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:29:00+00:00 | GS | bullish | 3.336 | order_validation_failed | Order $972.98 exceeds max position size $825.00 |
| 2026-01-15T20:29:04+00:00 | GS | bullish | 3.336 | order_validation_failed | Order $972.64 exceeds max position size $825.00 |
| 2026-01-15T20:29:31+00:00 | COST | bearish | 3.219 | order_validation_failed | Order $955.59 exceeds max position size $825.00 |
| 2026-01-15T20:29:35+00:00 | BLK | bullish | 4.056 | order_validation_failed | Order $1157.39 exceeds max position size $825.00 |
| 2026-01-15T20:29:35+00:00 | LCID | bearish | 2.961 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:29:48+00:00 | GS | bullish | 3.323 | order_validation_failed | Order $972.35 exceeds max position size $825.00 |
| 2026-01-15T20:29:58+00:00 | COST | bearish | 3.217 | order_validation_failed | Order $955.41 exceeds max position size $825.00 |
| 2026-01-15T20:30:02+00:00 | BLK | bullish | 4.054 | order_validation_failed | Order $1156.93 exceeds max position size $825.00 |
| 2026-01-15T20:30:02+00:00 | LCID | bearish | 2.959 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:30:11+00:00 | GS | bullish | 3.320 | order_validation_failed | Order $972.23 exceeds max position size $825.00 |
| 2026-01-15T20:30:44+00:00 | COST | bearish | 3.204 | order_validation_failed | Order $955.29 exceeds max position size $825.00 |
| 2026-01-15T20:30:48+00:00 | BLK | bullish | 4.037 | order_validation_failed | Order $1157.09 exceeds max position size $825.00 |
| 2026-01-15T20:30:51+00:00 | COST | bearish | 3.203 | order_validation_failed | Order $955.40 exceeds max position size $825.00 |
| 2026-01-15T20:30:51+00:00 | LCID | bearish | 2.947 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:30:58+00:00 | BLK | bullish | 4.037 | order_validation_failed | Order $1156.92 exceeds max position size $825.00 |
| 2026-01-15T20:30:59+00:00 | LCID | bearish | 2.947 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:31:11+00:00 | GS | bullish | 3.308 | order_validation_failed | Order $972.71 exceeds max position size $825.00 |
| 2026-01-15T20:31:15+00:00 | GS | bullish | 3.308 | order_validation_failed | Order $972.71 exceeds max position size $825.00 |
| 2026-01-15T20:31:46+00:00 | COST | bearish | 3.190 | order_validation_failed | Order $955.87 exceeds max position size $825.00 |
| 2026-01-15T20:31:53+00:00 | BLK | bullish | 4.019 | order_validation_failed | Order $1156.54 exceeds max position size $825.00 |
| 2026-01-15T20:31:53+00:00 | LCID | bearish | 2.934 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:32:08+00:00 | COST | bearish | 3.188 | order_validation_failed | Order $956.05 exceeds max position size $825.00 |
| 2026-01-15T20:32:11+00:00 | GS | bullish | 3.295 | order_validation_failed | Order $973.55 exceeds max position size $825.00 |
| 2026-01-15T20:32:15+00:00 | BLK | bullish | 4.016 | order_validation_failed | Order $1156.38 exceeds max position size $825.00 |
| 2026-01-15T20:32:15+00:00 | LCID | bearish | 2.933 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:32:28+00:00 | GS | bullish | 3.293 | order_validation_failed | Order $973.59 exceeds max position size $825.00 |
| 2026-01-15T20:33:06+00:00 | COST | bearish | 3.176 | max_positions_reached | — |
| 2026-01-15T20:33:41+00:00 | COST | bearish | 3.163 | order_validation_failed | Order $956.47 exceeds max position size $825.00 |
| 2026-01-15T20:33:47+00:00 | BLK | bullish | 3.988 | order_validation_failed | Order $1158.11 exceeds max position size $825.00 |
| 2026-01-15T20:33:53+00:00 | LCID | bearish | 2.911 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:33:54+00:00 | COST | bearish | 3.162 | order_validation_failed | Order $956.50 exceeds max position size $825.00 |
| 2026-01-15T20:34:00+00:00 | BLK | bullish | 3.985 | order_validation_failed | Order $1158.69 exceeds max position size $825.00 |
| 2026-01-15T20:34:00+00:00 | LCID | bearish | 2.910 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:34:08+00:00 | GS | bullish | 3.270 | order_validation_failed | Order $974.11 exceeds max position size $825.00 |
| 2026-01-15T20:34:15+00:00 | GS | bullish | 3.269 | order_validation_failed | Order $974.36 exceeds max position size $825.00 |
| 2026-01-15T20:34:37+00:00 | BLK | bearish | 3.786 | order_validation_failed | Order $1158.36 exceeds max position size $825.00 |
| 2026-01-15T20:34:47+00:00 | BLK | bearish | 3.784 | order_validation_failed | Order $1158.36 exceeds max position size $825.00 |
| 2026-01-15T20:34:51+00:00 | COST | bearish | 3.148 | order_validation_failed | Order $956.15 exceeds max position size $825.00 |
| 2026-01-15T20:34:54+00:00 | LCID | bearish | 2.898 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:35:08+00:00 | COST | bearish | 3.146 | order_validation_failed | Order $956.30 exceeds max position size $825.00 |
| 2026-01-15T20:35:12+00:00 | GS | bullish | 3.256 | order_validation_failed | Order $974.30 exceeds max position size $825.00 |
| 2026-01-15T20:35:15+00:00 | LCID | bearish | 2.896 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:35:29+00:00 | GS | bullish | 3.254 | order_validation_failed | Order $974.12 exceeds max position size $825.00 |
| 2026-01-15T20:35:38+00:00 | BLK | bearish | 3.770 | order_validation_failed | Order $1158.52 exceeds max position size $825.00 |
| 2026-01-15T20:35:50+00:00 | COST | bearish | 3.136 | order_validation_failed | Order $955.95 exceeds max position size $825.00 |
| 2026-01-15T20:35:54+00:00 | LCID | bearish | 2.886 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:36:04+00:00 | GS | bullish | 3.244 | order_validation_failed | Order $974.97 exceeds max position size $825.00 |
| 2026-01-15T20:36:07+00:00 | BLK | bearish | 3.761 | order_validation_failed | Order $1158.47 exceeds max position size $825.00 |
| 2026-01-15T20:36:24+00:00 | COST | bearish | 3.128 | order_validation_failed | Order $956.04 exceeds max position size $825.00 |
| 2026-01-15T20:36:28+00:00 | LCID | bearish | 2.880 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:36:38+00:00 | BLK | bearish | 3.753 | order_validation_failed | Order $1158.15 exceeds max position size $825.00 |
| 2026-01-15T20:36:59+00:00 | COST | bearish | 3.121 | order_validation_failed | Order $956.06 exceeds max position size $825.00 |
| 2026-01-15T20:37:03+00:00 | LCID | bearish | 2.874 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:37:13+00:00 | BLK | bearish | 3.743 | order_validation_failed | Order $1158.14 exceeds max position size $825.00 |
| 2026-01-15T20:37:32+00:00 | COST | bearish | 3.114 | order_validation_failed | Order $956.11 exceeds max position size $825.00 |
| 2026-01-15T20:37:35+00:00 | LCID | bearish | 2.867 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:37:46+00:00 | BLK | bearish | 3.734 | order_validation_failed | Order $1158.37 exceeds max position size $825.00 |
| 2026-01-15T20:38:02+00:00 | COST | bearish | 3.107 | order_validation_failed | Order $955.58 exceeds max position size $825.00 |
| 2026-01-15T20:38:03+00:00 | LCID | bearish | 2.861 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:38:35+00:00 | BLK | bearish | 3.720 | order_validation_failed | Order $1158.19 exceeds max position size $825.00 |
| 2026-01-15T20:38:35+00:00 | BLK | bearish | 3.719 | order_validation_failed | Order $1158.19 exceeds max position size $825.00 |
| 2026-01-15T20:38:57+00:00 | COST | bearish | 3.095 | max_positions_reached | — |
| 2026-01-15T20:38:57+00:00 | COST | bearish | 3.095 | max_positions_reached | — |
| 2026-01-15T20:39:00+00:00 | LCID | bearish | 2.849 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:39:00+00:00 | LCID | bearish | 2.850 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:39:29+00:00 | BLK | bearish | 3.705 | order_validation_failed | Order $1158.34 exceeds max position size $825.00 |
| 2026-01-15T20:39:38+00:00 | BLK | bearish | 3.704 | order_validation_failed | Order $1158.49 exceeds max position size $825.00 |
| 2026-01-15T20:39:45+00:00 | COST | bearish | 3.084 | order_validation_failed | Order $955.60 exceeds max position size $825.00 |
| 2026-01-15T20:39:49+00:00 | LCID | bearish | 2.839 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:40:03+00:00 | COST | bearish | 3.083 | order_validation_failed | Order $955.54 exceeds max position size $825.00 |
| 2026-01-15T20:40:04+00:00 | LCID | bearish | 2.839 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:40:30+00:00 | BLK | bearish | 3.688 | order_validation_failed | Order $1160.40 exceeds max position size $825.00 |
| 2026-01-15T20:40:46+00:00 | COST | bearish | 3.071 | order_validation_failed | Order $955.89 exceeds max position size $825.00 |
| 2026-01-15T20:40:46+00:00 | LCID | bearish | 2.828 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:40:56+00:00 | BLK | bearish | 3.685 | order_validation_failed | Order $1160.67 exceeds max position size $825.00 |
| 2026-01-15T20:41:14+00:00 | COST | bearish | 3.068 | order_validation_failed | Order $955.89 exceeds max position size $825.00 |
| 2026-01-15T20:41:14+00:00 | LCID | bearish | 2.826 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:41:40+00:00 | BLK | bearish | 3.670 | order_validation_failed | Order $1161.39 exceeds max position size $825.00 |
| 2026-01-15T20:41:55+00:00 | BLK | bearish | 3.667 | order_validation_failed | Order $1161.71 exceeds max position size $825.00 |
| 2026-01-15T20:42:02+00:00 | COST | bearish | 3.056 | order_validation_failed | Order $956.26 exceeds max position size $825.00 |
| 2026-01-15T20:42:02+00:00 | LCID | bearish | 2.815 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:42:17+00:00 | COST | bearish | 3.054 | order_validation_failed | Order $956.16 exceeds max position size $825.00 |
| 2026-01-15T20:42:20+00:00 | PLTR | bearish | 2.960 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:42:20+00:00 | LCID | bearish | 2.813 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:42:51+00:00 | BLK | bearish | 3.650 | order_validation_failed | Order $1161.96 exceeds max position size $825.00 |
| 2026-01-15T20:43:01+00:00 | BLK | bearish | 3.648 | order_validation_failed | Order $1161.99 exceeds max position size $825.00 |
| 2026-01-15T20:43:07+00:00 | COST | bearish | 3.040 | order_validation_failed | Order $956.65 exceeds max position size $825.00 |
| 2026-01-15T20:43:08+00:00 | PLTR | bearish | 2.947 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:43:11+00:00 | LCID | bearish | 2.801 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:43:22+00:00 | COST | bearish | 3.039 | order_validation_failed | Order $956.63 exceeds max position size $825.00 |
| 2026-01-15T20:43:22+00:00 | PLTR | bearish | 2.947 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:43:25+00:00 | LCID | bearish | 2.800 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:43:57+00:00 | BLK | bearish | 3.632 | order_validation_failed | Order $1161.58 exceeds max position size $825.00 |
| 2026-01-15T20:44:01+00:00 | BLK | bearish | 3.632 | order_validation_failed | Order $1161.37 exceeds max position size $825.00 |
| 2026-01-15T20:44:21+00:00 | COST | bearish | 3.027 | max_positions_reached | — |
| 2026-01-15T20:44:24+00:00 | PLTR | bearish | 2.934 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:44:24+00:00 | LCID | bearish | 2.788 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:44:27+00:00 | COST | bearish | 3.026 | max_positions_reached | — |
| 2026-01-15T20:44:30+00:00 | MA | bullish | 3.397 | max_positions_reached | — |
| 2026-01-15T20:44:30+00:00 | PLTR | bearish | 2.934 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:44:34+00:00 | LCID | bearish | 2.787 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:44:37+00:00 | MA | bullish | 3.396 | max_positions_reached | — |
| 2026-01-15T20:45:27+00:00 | BLK | bearish | 4.410 | order_validation_failed | Order $1160.96 exceeds max position size $825.00 |
| 2026-01-15T20:45:27+00:00 | PFE | bullish | 2.865 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:45:27+00:00 | WFC | bullish | 2.830 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:45:27+00:00 | BLK | bearish | 4.409 | order_validation_failed | Order $1160.70 exceeds max position size $825.00 |
| 2026-01-15T20:45:27+00:00 | PFE | bullish | 2.864 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:45:27+00:00 | WFC | bullish | 2.828 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:45:29+00:00 | COST | bearish | 3.677 | order_validation_failed | Order $956.65 exceeds max position size $825.00 |
| 2026-01-15T20:45:29+00:00 | COST | bearish | 3.675 | order_validation_failed | Order $956.65 exceeds max position size $825.00 |
| 2026-01-15T20:45:38+00:00 | LCID | bearish | 3.386 | max_positions_reached | — |
| 2026-01-15T20:45:38+00:00 | MA | bullish | 2.250 | expectancy_blocked:score_floor_breach | — |
| 2026-01-15T20:45:41+00:00 | LCID | bearish | 3.386 | max_positions_reached | — |
| 2026-01-15T20:45:41+00:00 | MA | bullish | 2.251 | expectancy_blocked:score_floor_breach | — |

</details>

**Hindsight note:** outcome-tracking fields are frequently `outcome_tracked=false`, so PnL impact of blocks is mostly not inferable from today’s stored data.

## 5. Missed trades
- **Missed-trade candidates (gate_passed signals with no nearby order/blocked event):** 1396

### Highest-score missed candidates (top 40)
| Time (UTC) | Symbol | Direction | Score | Notes (truncated) |
| --- | --- | --- | --- | --- |
| 2026-01-15T20:03:25+00:00 | AAPL | bullish | 4.810 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:31+00:00 | AAPL | bullish | 4.807 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:53+00:00 | AAPL | bullish | 4.802 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:05+00:00 | AAPL | bullish | 4.798 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:29+00:00 | AAPL | bullish | 4.786 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:35+00:00 | AAPL | bullish | 4.783 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:35+00:00 | AAPL | bullish | 4.783 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:51:58+00:00 | AAPL | bullish | 4.772 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:51:58+00:00 | AAPL | bullish | 4.771 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:28+00:00 | AAPL | bullish | 4.764 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:49+00:00 | AAPL | bullish | 4.756 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:53+00:00 | AAPL | bullish | 4.734 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:46+00:00 | AAPL | bullish | 4.732 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:52+00:00 | AAPL | bullish | 4.729 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:56+00:00 | LOW | bullish | 4.720 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:35+00:00 | NVDA | bullish | 4.718 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:38+00:00 | NVDA | bullish | 4.717 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:51+00:00 | AAPL | bullish | 4.713 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:55+00:00 | AAPL | bullish | 4.711 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:58+00:00 | NVDA | bullish | 4.709 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:13+00:00 | MS | bullish | 4.708 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:47:01+00:00 | NVDA | bullish | 4.708 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:30+00:00 | LOW | bullish | 4.707 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:10+00:00 | AAPL | bullish | 4.701 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:18+00:00 | AAPL | bullish | 4.697 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:56+00:00 | AAPL | bullish | 4.689 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:10+00:00 | MS | bullish | 4.688 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:35+00:00 | LOW | bullish | 4.685 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:43+00:00 | LOW | bullish | 4.682 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:32+00:00 | MS | bullish | 4.680 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:30+00:00 | AAPL | bullish | 4.676 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:34+00:00 | AAPL | bullish | 4.670 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:25+00:00 | META | bullish | 4.670 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:30+00:00 | META | bullish | 4.668 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:47+00:00 | AAPL | bullish | 4.665 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:19+00:00 | MS | bullish | 4.663 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:35+00:00 | AAPL | bullish | 4.654 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:46+00:00 | AAPL | bullish | 4.650 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:15+00:00 | LOW | bullish | 4.649 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:16+00:00 | LOW | bullish | 4.649 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |

<details>
<summary>Full missed-trade candidate ledger – 1396 rows</summary>

| Time (UTC) | Symbol | Direction | Score | Notes (truncated) |
| --- | --- | --- | --- | --- |
| 2026-01-15T19:46:46+00:00 | LCID | bearish | 3.460 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:46:53+00:00 | LCID | bearish | 3.458 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:49:35+00:00 | AAPL | bullish | 4.783 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:35+00:00 | PFE | bullish | 4.590 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:35+00:00 | AAPL | bullish | 4.783 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:35+00:00 | PFE | bullish | 4.590 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:36+00:00 | WFC | bullish | 4.530 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:36+00:00 | WFC | bullish | 4.529 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:37+00:00 | WMT | bullish | 4.400 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:37+00:00 | WMT | bullish | 4.400 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:37+00:00 | HOOD | bullish | 4.290 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:37+00:00 | HOOD | bullish | 4.290 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:37+00:00 | UNH | bullish | 4.250 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:37+00:00 | UNH | bullish | 4.250 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:37+00:00 | COIN | bullish | 3.995 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:37+00:00 | COIN | bullish | 3.994 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:38+00:00 | RIVN | bearish | 3.909 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:49:38+00:00 | RIVN | bearish | 3.909 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:49:38+00:00 | LCID | bearish | 3.907 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:49:38+00:00 | LCID | bearish | 3.907 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:49:47+00:00 | PLTR | bullish | 3.803 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:47+00:00 | PLTR | bullish | 3.803 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:54+00:00 | AMZN | bullish | 3.752 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:49:54+00:00 | AMZN | bullish | 3.752 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:50:01+00:00 | NVDA | bullish | 3.403 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:50:01+00:00 | NVDA | bullish | 3.403 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:50:12+00:00 | META | bullish | 3.099 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:50:15+00:00 | META | bullish | 3.099 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:51:24+00:00 | MA | bullish | 2.712 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:51:24+00:00 | MA | bullish | 2.712 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:51:58+00:00 | AAPL | bullish | 4.772 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:51:58+00:00 | PFE | bullish | 4.540 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:51:58+00:00 | AAPL | bullish | 4.771 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:51:58+00:00 | PFE | bullish | 4.540 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:51:59+00:00 | WFC | bullish | 4.480 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:51:59+00:00 | WFC | bullish | 4.480 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:00+00:00 | WMT | bullish | 4.351 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:00+00:00 | HOOD | bullish | 4.243 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:00+00:00 | WMT | bullish | 4.352 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:00+00:00 | HOOD | bullish | 4.244 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:00+00:00 | UNH | bullish | 4.204 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:00+00:00 | UNH | bullish | 4.205 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:08+00:00 | COIN | bullish | 3.952 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:08+00:00 | COIN | bullish | 3.952 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:08+00:00 | RIVN | bearish | 3.868 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:52:11+00:00 | LCID | bearish | 3.866 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:52:11+00:00 | RIVN | bearish | 3.868 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:52:11+00:00 | LCID | bearish | 3.866 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:52:20+00:00 | PLTR | bullish | 3.763 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:23+00:00 | PLTR | bullish | 3.763 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:23+00:00 | AMZN | bullish | 3.709 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:24+00:00 | AMZN | bullish | 3.709 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:56+00:00 | HD | bullish | 3.638 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:59+00:00 | NVDA | bullish | 3.369 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:59+00:00 | HD | bullish | 3.638 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:52:59+00:00 | NVDA | bullish | 3.368 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:02+00:00 | MS | bullish | 3.295 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:06+00:00 | MS | bullish | 3.295 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:06+00:00 | LOW | bullish | 3.206 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:53:09+00:00 | META | bullish | 3.068 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:09+00:00 | LOW | bullish | 3.206 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:53:13+00:00 | META | bullish | 3.068 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:46+00:00 | AAPL | bullish | 4.732 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:47+00:00 | PFE | bullish | 4.503 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:48+00:00 | WFC | bullish | 4.443 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:50+00:00 | WMT | bullish | 4.316 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:50+00:00 | HOOD | bullish | 4.210 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:51+00:00 | UNH | bullish | 4.171 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:52+00:00 | COIN | bullish | 3.920 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:52+00:00 | RIVN | bearish | 3.837 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:53:52+00:00 | AAPL | bullish | 4.729 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:52+00:00 | LCID | bearish | 3.835 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:53:52+00:00 | PFE | bullish | 4.501 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:56+00:00 | WFC | bullish | 4.441 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:59+00:00 | WMT | bullish | 4.314 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:53:59+00:00 | HOOD | bullish | 4.208 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:03+00:00 | UNH | bullish | 4.168 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:07+00:00 | COIN | bullish | 3.918 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:07+00:00 | RIVN | bearish | 3.835 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:54:07+00:00 | PLTR | bullish | 3.733 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:10+00:00 | LCID | bearish | 3.834 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:54:14+00:00 | AMZN | bullish | 3.677 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:18+00:00 | HD | bullish | 3.610 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:18+00:00 | NVDA | bullish | 3.343 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:21+00:00 | MS | bullish | 3.270 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:22+00:00 | LOW | bullish | 3.182 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:54:25+00:00 | META | bullish | 3.045 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:28+00:00 | PLTR | bullish | 3.732 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:32+00:00 | MSFT | bullish | 2.900 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:35+00:00 | NIO | bullish | 2.769 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:54:35+00:00 | DIA | bullish | 2.732 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:35+00:00 | AMZN | bullish | 3.675 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:42+00:00 | HD | bullish | 3.608 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:42+00:00 | NVDA | bullish | 3.341 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:49+00:00 | MS | bullish | 3.269 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:49+00:00 | LOW | bullish | 3.181 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:54:52+00:00 | META | bullish | 3.044 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:53+00:00 | MSFT | bullish | 2.898 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:54:56+00:00 | NIO | bullish | 2.768 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:55:00+00:00 | DIA | bullish | 2.731 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:10+00:00 | AAPL | bullish | 4.701 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:10+00:00 | PFE | bullish | 4.474 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:12+00:00 | WFC | bullish | 4.415 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:14+00:00 | WMT | bullish | 4.288 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:14+00:00 | HOOD | bullish | 4.183 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:15+00:00 | UNH | bullish | 4.144 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:16+00:00 | COIN | bullish | 3.896 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:16+00:00 | RIVN | bearish | 3.814 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:55:17+00:00 | LCID | bearish | 3.812 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:55:18+00:00 | AAPL | bullish | 4.697 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:18+00:00 | PFE | bullish | 4.471 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:26+00:00 | WFC | bullish | 4.412 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:29+00:00 | PLTR | bullish | 3.710 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:33+00:00 | AMZN | bullish | 3.652 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:36+00:00 | WMT | bullish | 4.285 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:36+00:00 | HOOD | bullish | 4.180 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:37+00:00 | HD | bullish | 3.588 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:40+00:00 | UNH | bullish | 4.141 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:40+00:00 | NVDA | bullish | 3.323 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:47+00:00 | COIN | bullish | 3.893 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:47+00:00 | RIVN | bearish | 3.810 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:55:47+00:00 | LCID | bearish | 3.809 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:55:50+00:00 | MS | bullish | 3.251 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:54+00:00 | LOW | bullish | 3.163 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:55:54+00:00 | META | bullish | 3.028 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:55:59+00:00 | PLTR | bullish | 3.707 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:01+00:00 | MSFT | bullish | 2.883 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:03+00:00 | AMZN | bullish | 3.650 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:04+00:00 | NIO | bullish | 2.754 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:56:07+00:00 | HD | bullish | 3.585 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:07+00:00 | NVDA | bullish | 3.321 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:07+00:00 | DIA | bullish | 2.717 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:14+00:00 | MS | bullish | 3.249 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:15+00:00 | LOW | bullish | 3.161 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:56:18+00:00 | META | bullish | 3.026 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:22+00:00 | MSFT | bullish | 2.881 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:22+00:00 | NIO | bullish | 2.752 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:56:25+00:00 | DIA | bullish | 2.715 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:34+00:00 | AAPL | bullish | 4.670 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:34+00:00 | PFE | bullish | 4.446 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:35+00:00 | WFC | bullish | 4.387 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:43+00:00 | WMT | bullish | 4.261 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:43+00:00 | HOOD | bullish | 4.157 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:44+00:00 | UNH | bullish | 4.118 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:47+00:00 | AAPL | bullish | 4.665 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:47+00:00 | PFE | bullish | 4.442 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:48+00:00 | COIN | bullish | 3.872 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:50+00:00 | WFC | bullish | 4.382 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:54+00:00 | RIVN | bearish | 3.790 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:56:54+00:00 | LCID | bearish | 3.789 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:56:54+00:00 | WMT | bullish | 4.256 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:56:57+00:00 | HOOD | bullish | 4.153 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:01+00:00 | UNH | bullish | 4.113 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:05+00:00 | COIN | bullish | 3.868 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:05+00:00 | RIVN | bearish | 3.786 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:57:06+00:00 | PLTR | bullish | 3.688 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:08+00:00 | LCID | bearish | 3.785 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:57:10+00:00 | AMZN | bullish | 3.628 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:14+00:00 | HD | bullish | 3.566 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:17+00:00 | PLTR | bullish | 3.684 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:20+00:00 | NVDA | bullish | 3.303 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:20+00:00 | AMZN | bullish | 3.624 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:23+00:00 | MS | bullish | 3.232 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:27+00:00 | HD | bullish | 3.562 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:30+00:00 | LOW | bullish | 3.145 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:57:30+00:00 | META | bullish | 3.011 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:31+00:00 | NVDA | bullish | 3.300 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:34+00:00 | MS | bullish | 3.229 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:37+00:00 | MSFT | bullish | 2.867 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:40+00:00 | NIO | bullish | 2.739 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:57:40+00:00 | DIA | bullish | 2.702 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:44+00:00 | LOW | bullish | 3.142 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:57:47+00:00 | META | bullish | 3.007 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:51+00:00 | MSFT | bullish | 2.864 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:57:51+00:00 | NIO | bullish | 2.736 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:58:09+00:00 | AAPL | bullish | 4.637 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:09+00:00 | PFE | bullish | 4.414 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:11+00:00 | WFC | bullish | 4.356 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:12+00:00 | WMT | bullish | 4.231 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:13+00:00 | HOOD | bullish | 4.127 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:14+00:00 | UNH | bullish | 4.089 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:15+00:00 | COIN | bullish | 3.845 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:15+00:00 | RIVN | bearish | 3.764 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:58:15+00:00 | LCID | bearish | 3.763 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:58:16+00:00 | AAPL | bullish | 4.634 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:19+00:00 | PFE | bullish | 4.412 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:23+00:00 | WFC | bullish | 4.352 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:25+00:00 | PLTR | bullish | 3.663 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:44+00:00 | AMZN | bullish | 3.601 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:44+00:00 | HD | bullish | 3.542 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:44+00:00 | NVDA | bullish | 3.282 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:48+00:00 | MS | bullish | 3.211 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:51+00:00 | LOW | bullish | 3.125 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:58:57+00:00 | WMT | bullish | 4.228 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:58:57+00:00 | HOOD | bullish | 4.125 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:00+00:00 | UNH | bullish | 4.087 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:01+00:00 | META | bullish | 2.991 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:04+00:00 | COIN | bullish | 3.842 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:04+00:00 | RIVN | bearish | 3.761 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:59:07+00:00 | LCID | bearish | 3.760 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:59:08+00:00 | MSFT | bullish | 2.849 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:11+00:00 | NIO | bullish | 2.722 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:59:17+00:00 | PLTR | bullish | 3.660 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:21+00:00 | AMZN | bullish | 3.598 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:21+00:00 | HD | bullish | 3.540 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:24+00:00 | NVDA | bullish | 3.279 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:28+00:00 | MS | bullish | 3.209 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:30+00:00 | LOW | bullish | 3.123 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T19:59:30+00:00 | META | bullish | 2.990 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:34+00:00 | AAPL | bullish | 4.606 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:34+00:00 | PFE | bullish | 4.386 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:38+00:00 | MSFT | bullish | 2.847 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:38+00:00 | NIO | bullish | 2.720 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T19:59:38+00:00 | WFC | bullish | 4.327 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:49+00:00 | WMT | bullish | 4.203 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:49+00:00 | HOOD | bullish | 4.101 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:53+00:00 | UNH | bullish | 4.063 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:56+00:00 | COIN | bullish | 3.821 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T19:59:56+00:00 | RIVN | bearish | 3.740 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T19:59:56+00:00 | LCID | bearish | 3.739 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:00:06+00:00 | PLTR | bullish | 3.639 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:09+00:00 | AMZN | bullish | 3.576 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:09+00:00 | HD | bullish | 3.520 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:10+00:00 | NVDA | bullish | 3.262 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:12+00:00 | MS | bullish | 3.192 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:13+00:00 | LOW | bullish | 3.106 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:00:13+00:00 | META | bullish | 2.974 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:14+00:00 | AAPL | bullish | 4.592 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:17+00:00 | PFE | bullish | 4.373 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:20+00:00 | MSFT | bullish | 2.833 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:21+00:00 | NIO | bullish | 2.706 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:00:21+00:00 | WFC | bullish | 4.314 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:37+00:00 | WMT | bullish | 4.191 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:38+00:00 | HOOD | bullish | 4.089 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:42+00:00 | UNH | bullish | 4.051 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:42+00:00 | AAPL | bullish | 4.583 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:42+00:00 | COIN | bullish | 3.810 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:42+00:00 | PFE | bullish | 4.363 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:45+00:00 | RIVN | bearish | 3.729 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:00:45+00:00 | LCID | bearish | 3.728 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:00:46+00:00 | LOW | bearish | 4.347 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:00:49+00:00 | WFC | bullish | 4.304 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:00:56+00:00 | WMT | bullish | 4.181 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:00+00:00 | HOOD | bullish | 4.082 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:03+00:00 | PLTR | bullish | 3.629 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:03+00:00 | UNH | bullish | 4.043 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:05+00:00 | AMZN | bullish | 3.565 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:05+00:00 | HD | bullish | 3.510 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:07+00:00 | COIN | bullish | 3.802 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:07+00:00 | LCID | bearish | 3.722 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:01:08+00:00 | NVDA | bullish | 3.253 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:11+00:00 | MS | bullish | 3.183 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:18+00:00 | LOW | bullish | 3.097 | adaptive_weights_active; mild_toxicity(0.49); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:01:18+00:00 | META | bullish | 2.966 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:19+00:00 | RIVN | bearish | 3.721 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:01:22+00:00 | PLTR | bullish | 3.620 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:22+00:00 | MSFT | bullish | 2.825 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:29+00:00 | AMZN | bullish | 3.557 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:32+00:00 | HD | bullish | 3.503 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:32+00:00 | NVDA | bullish | 3.246 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:36+00:00 | MS | bullish | 3.177 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:39+00:00 | META | bullish | 2.960 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:40+00:00 | MSFT | bullish | 2.819 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:53+00:00 | AAPL | bullish | 4.802 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:53+00:00 | MSFT | bullish | 4.570 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:53+00:00 | PFE | bullish | 4.340 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:01:57+00:00 | LOW | bearish | 4.324 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:01:58+00:00 | WFC | bullish | 4.281 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:02+00:00 | WMT | bullish | 4.159 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:05+00:00 | HOOD | bullish | 4.061 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:05+00:00 | AAPL | bullish | 4.798 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:05+00:00 | MSFT | bullish | 4.567 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:08+00:00 | PFE | bullish | 4.337 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:09+00:00 | UNH | bullish | 4.022 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:12+00:00 | COIN | bullish | 3.782 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:12+00:00 | LCID | bearish | 3.703 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:02:12+00:00 | LOW | bearish | 4.321 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:02:15+00:00 | WFC | bullish | 4.278 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:23+00:00 | WMT | bullish | 4.155 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:24+00:00 | HOOD | bullish | 4.057 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:24+00:00 | RIVN | bearish | 3.702 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:02:27+00:00 | UNH | bullish | 4.019 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:30+00:00 | COIN | bullish | 3.780 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:30+00:00 | LCID | bearish | 3.700 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:02:33+00:00 | PLTR | bullish | 3.602 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:37+00:00 | AMZN | bullish | 3.537 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:37+00:00 | HD | bullish | 3.486 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:41+00:00 | NVDA | bullish | 3.230 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:42+00:00 | RIVN | bearish | 3.699 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:02:43+00:00 | PLTR | bullish | 3.600 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:46+00:00 | AMZN | bullish | 3.534 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:46+00:00 | HD | bullish | 3.483 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:46+00:00 | NVDA | bullish | 3.227 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:50+00:00 | MS | bullish | 3.159 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:53+00:00 | MS | bullish | 3.162 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:57+00:00 | META | bullish | 2.944 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:02:57+00:00 | META | bullish | 2.946 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:25+00:00 | AAPL | bullish | 4.810 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:25+00:00 | MSFT | bullish | 4.539 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:26+00:00 | PFE | bullish | 4.311 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:27+00:00 | LOW | bearish | 4.296 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:03:27+00:00 | WFC | bullish | 4.253 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:31+00:00 | AAPL | bullish | 4.807 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:31+00:00 | MSFT | bullish | 4.537 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:31+00:00 | PFE | bullish | 4.309 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:31+00:00 | WMT | bullish | 4.132 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:34+00:00 | HOOD | bullish | 4.031 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:35+00:00 | UNH | bullish | 3.994 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:38+00:00 | LOW | bearish | 4.294 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:03:38+00:00 | WFC | bullish | 4.251 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:38+00:00 | COIN | bullish | 3.757 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:41+00:00 | RIVN | bearish | 3.679 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:03:41+00:00 | LCID | bearish | 3.677 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:03:50+00:00 | PLTR | bullish | 3.580 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:54+00:00 | AMZN | bullish | 3.511 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:54+00:00 | HD | bullish | 3.463 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:03:54+00:00 | NVDA | bullish | 3.210 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:01+00:00 | MS | bullish | 3.142 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:05+00:00 | META | bullish | 2.928 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:16+00:00 | WMT | bullish | 4.130 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:20+00:00 | HOOD | bullish | 4.029 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:24+00:00 | UNH | bullish | 3.992 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:24+00:00 | COIN | bullish | 3.756 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:24+00:00 | RIVN | bearish | 3.677 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:04:24+00:00 | LCID | bearish | 3.675 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:04:29+00:00 | AAPL | bullish | 4.786 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:29+00:00 | MSFT | bullish | 4.517 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:29+00:00 | PFE | bullish | 4.290 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:33+00:00 | LOW | bearish | 4.275 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:04:33+00:00 | WFC | bullish | 4.232 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:37+00:00 | PLTR | bullish | 3.578 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:43+00:00 | WMT | bullish | 4.112 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:43+00:00 | HOOD | bullish | 4.012 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:47+00:00 | AMZN | bullish | 3.510 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:47+00:00 | HD | bullish | 3.461 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:50+00:00 | NVDA | bullish | 3.208 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:50+00:00 | UNH | bullish | 3.975 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:50+00:00 | COIN | bullish | 3.739 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:04:50+00:00 | RIVN | bearish | 3.661 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:04:53+00:00 | LCID | bearish | 3.660 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:04:54+00:00 | MS | bullish | 3.140 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:01+00:00 | META | bullish | 2.927 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:06+00:00 | PLTR | bullish | 3.563 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:10+00:00 | AMZN | bullish | 3.493 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:10+00:00 | HD | bullish | 3.447 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:11+00:00 | NVDA | bullish | 3.195 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:15+00:00 | MS | bullish | 3.127 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:22+00:00 | META | bullish | 2.915 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:28+00:00 | AAPL | bullish | 4.764 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:28+00:00 | MSFT | bullish | 4.496 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:31+00:00 | PFE | bullish | 4.271 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:32+00:00 | LOW | bearish | 4.256 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:05:35+00:00 | WFC | bullish | 4.214 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:43+00:00 | WMT | bullish | 4.094 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:43+00:00 | HOOD | bullish | 3.995 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:48+00:00 | UNH | bullish | 3.958 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:48+00:00 | COIN | bullish | 3.723 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:48+00:00 | RIVN | bearish | 3.645 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:05:48+00:00 | LCID | bearish | 3.644 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:05:49+00:00 | AAPL | bullish | 4.756 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:55+00:00 | MSFT | bullish | 4.489 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:05:58+00:00 | PFE | bullish | 4.264 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:00+00:00 | PLTR | bullish | 3.548 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:02+00:00 | LOW | bearish | 4.249 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:06:02+00:00 | WFC | bullish | 4.207 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:04+00:00 | AMZN | bullish | 3.477 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:04+00:00 | HD | bullish | 3.432 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:07+00:00 | NVDA | bullish | 3.182 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:10+00:00 | WMT | bullish | 4.088 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:11+00:00 | MS | bullish | 3.115 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:13+00:00 | HOOD | bullish | 3.988 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:16+00:00 | UNH | bullish | 3.952 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:16+00:00 | COIN | bullish | 3.718 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:16+00:00 | RIVN | bearish | 3.640 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:06:17+00:00 | LCID | bearish | 3.639 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:06:24+00:00 | META | bullish | 2.904 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:32+00:00 | PLTR | bullish | 3.543 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:33+00:00 | AMZN | bullish | 3.471 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:33+00:00 | HD | bullish | 3.427 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:36+00:00 | NVDA | bullish | 3.178 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:46+00:00 | MS | bullish | 3.110 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:48+00:00 | META | bullish | 2.900 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:53+00:00 | AAPL | bullish | 4.734 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:57+00:00 | MSFT | bullish | 4.468 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:06:57+00:00 | PFE | bullish | 4.244 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:01+00:00 | LOW | bearish | 4.229 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:07:01+00:00 | WFC | bullish | 4.187 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:05+00:00 | WMT | bullish | 4.068 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:05+00:00 | HOOD | bullish | 3.970 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:09+00:00 | UNH | bullish | 3.934 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:09+00:00 | COIN | bullish | 3.701 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:09+00:00 | RIVN | bearish | 3.624 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:07:09+00:00 | LCID | bearish | 3.623 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:07:18+00:00 | PLTR | bullish | 3.527 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:19+00:00 | AMZN | bullish | 3.454 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:19+00:00 | HD | bullish | 3.412 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:19+00:00 | NVDA | bullish | 3.164 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:23+00:00 | MS | bullish | 3.097 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:26+00:00 | META | bullish | 2.888 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:51+00:00 | AAPL | bullish | 4.713 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:52+00:00 | MSFT | bullish | 4.449 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:52+00:00 | PFE | bullish | 4.226 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:54+00:00 | LOW | bearish | 4.212 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:07:54+00:00 | WFC | bullish | 4.170 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:55+00:00 | AAPL | bullish | 4.711 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:56+00:00 | MSFT | bullish | 4.446 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:56+00:00 | PFE | bullish | 4.224 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:56+00:00 | WMT | bullish | 4.052 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:07:59+00:00 | HOOD | bullish | 3.953 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:00+00:00 | LOW | bearish | 4.209 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:08:03+00:00 | WFC | bullish | 4.167 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:03+00:00 | UNH | bullish | 3.918 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:03+00:00 | COIN | bullish | 3.686 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:03+00:00 | RIVN | bearish | 3.609 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:08:06+00:00 | LCID | bearish | 3.607 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:08:11+00:00 | WMT | bullish | 4.050 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:11+00:00 | HOOD | bullish | 3.951 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:16+00:00 | PLTR | bullish | 3.513 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:17+00:00 | UNH | bullish | 3.915 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:17+00:00 | COIN | bullish | 3.684 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:17+00:00 | RIVN | bearish | 3.607 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:08:19+00:00 | AMZN | bullish | 3.438 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:19+00:00 | HD | bullish | 3.399 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:20+00:00 | LCID | bearish | 3.606 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:08:22+00:00 | NVDA | bullish | 3.152 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:23+00:00 | MS | bullish | 3.085 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:30+00:00 | META | bullish | 2.877 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:45+00:00 | PLTR | bullish | 3.511 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:50+00:00 | AMZN | bullish | 3.437 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:51+00:00 | HD | bullish | 3.397 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:51+00:00 | NVDA | bullish | 3.150 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:52+00:00 | MS | bullish | 3.083 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:54+00:00 | META | bullish | 2.875 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:56+00:00 | LOW | bullish | 4.720 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:08:56+00:00 | AAPL | bullish | 4.689 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:02+00:00 | MSFT | bullish | 4.426 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:02+00:00 | PFE | bullish | 4.205 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:06+00:00 | WFC | bullish | 4.148 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:18+00:00 | WMT | bullish | 4.031 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:18+00:00 | HOOD | bullish | 3.934 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:18+00:00 | UNH | bullish | 3.898 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:19+00:00 | COIN | bullish | 3.668 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:22+00:00 | RIVN | bearish | 3.591 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:09:22+00:00 | LCID | bearish | 3.590 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:09:30+00:00 | LOW | bullish | 4.707 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:30+00:00 | AAPL | bullish | 4.676 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:34+00:00 | MSFT | bullish | 4.414 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:34+00:00 | PFE | bullish | 4.194 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:35+00:00 | PLTR | bullish | 3.496 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:37+00:00 | WFC | bullish | 4.138 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:41+00:00 | WMT | bullish | 4.020 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:41+00:00 | HOOD | bullish | 3.924 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:45+00:00 | UNH | bullish | 3.887 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:45+00:00 | AMZN | bullish | 3.420 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:48+00:00 | COIN | bullish | 3.658 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:48+00:00 | HD | bullish | 3.382 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:48+00:00 | RIVN | bearish | 3.582 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:09:48+00:00 | NVDA | bullish | 3.137 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:09:48+00:00 | LCID | bearish | 3.581 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:09:55+00:00 | MS | bullish | 3.070 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:01+00:00 | META | bullish | 2.864 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:03+00:00 | PLTR | bullish | 3.487 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:04+00:00 | AMZN | bullish | 3.411 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:04+00:00 | HD | bullish | 3.374 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:07+00:00 | NVDA | bullish | 3.129 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:08+00:00 | MS | bullish | 3.063 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:15+00:00 | META | bullish | 2.857 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:35+00:00 | LOW | bullish | 4.685 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:35+00:00 | AAPL | bullish | 4.654 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:36+00:00 | WMT | bullish | 4.572 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:37+00:00 | MSFT | bullish | 4.394 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:38+00:00 | PFE | bullish | 4.174 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:39+00:00 | WFC | bullish | 4.118 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:43+00:00 | HOOD | bullish | 3.905 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:43+00:00 | LOW | bullish | 4.682 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:46+00:00 | AAPL | bullish | 4.650 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:47+00:00 | WMT | bullish | 4.569 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:50+00:00 | UNH | bullish | 3.870 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:50+00:00 | COIN | bullish | 3.642 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:50+00:00 | RIVN | bearish | 3.566 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:10:50+00:00 | MSFT | bullish | 4.390 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:10:53+00:00 | LCID | bearish | 3.565 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:10:53+00:00 | PFE | bullish | 4.171 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:01+00:00 | WFC | bullish | 4.115 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:05+00:00 | HOOD | bullish | 3.903 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:09+00:00 | UNH | bullish | 3.867 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:09+00:00 | COIN | bullish | 3.640 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:09+00:00 | PLTR | bullish | 3.472 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:12+00:00 | RIVN | bearish | 3.564 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:11:12+00:00 | LCID | bearish | 3.562 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:11:13+00:00 | AMZN | bullish | 3.393 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:16+00:00 | HD | bullish | 3.359 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:16+00:00 | NVDA | bullish | 3.116 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:21+00:00 | PLTR | bullish | 3.469 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:23+00:00 | MS | bullish | 3.050 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:25+00:00 | AMZN | bullish | 3.391 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:25+00:00 | HD | bullish | 3.357 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:28+00:00 | NVDA | bullish | 3.114 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:29+00:00 | MS | bullish | 3.048 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:35+00:00 | META | bullish | 2.843 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:11:38+00:00 | META | bullish | 2.845 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:15+00:00 | LOW | bullish | 4.649 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:16+00:00 | AAPL | bullish | 4.618 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:16+00:00 | WMT | bullish | 4.538 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:16+00:00 | LOW | bullish | 4.649 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:16+00:00 | AAPL | bullish | 4.618 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:16+00:00 | WMT | bullish | 4.538 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:16+00:00 | MSFT | bullish | 4.360 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:17+00:00 | AMZN | bullish | 4.249 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:17+00:00 | MSFT | bullish | 4.360 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:17+00:00 | PFE | bullish | 4.143 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:17+00:00 | AMZN | bullish | 4.249 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:17+00:00 | PFE | bullish | 4.143 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:18+00:00 | WFC | bullish | 4.088 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:18+00:00 | WFC | bullish | 4.088 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:19+00:00 | V | bearish | 4.006 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:12:19+00:00 | V | bearish | 4.006 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:12:20+00:00 | HOOD | bullish | 3.876 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:20+00:00 | HOOD | bullish | 3.876 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:24+00:00 | UNH | bullish | 3.842 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:27+00:00 | COIN | bullish | 3.616 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:27+00:00 | UNH | bullish | 3.842 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:30+00:00 | RIVN | bearish | 3.541 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:12:30+00:00 | COIN | bullish | 3.616 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:30+00:00 | LCID | bearish | 3.539 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:12:30+00:00 | RIVN | bearish | 3.541 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:12:33+00:00 | LCID | bearish | 3.539 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:12:42+00:00 | PLTR | bullish | 3.447 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:43+00:00 | HD | bullish | 3.335 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:45+00:00 | PLTR | bullish | 3.447 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:46+00:00 | NVDA | bullish | 3.095 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:50+00:00 | MS | bullish | 3.029 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:53+00:00 | HD | bullish | 3.335 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:53+00:00 | NVDA | bullish | 3.095 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:12:56+00:00 | META | bullish | 2.826 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:00+00:00 | MS | bullish | 3.029 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:03+00:00 | META | bullish | 2.826 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:24+00:00 | LOW | bullish | 4.624 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:24+00:00 | AAPL | bullish | 4.593 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:24+00:00 | WMT | bullish | 4.513 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:25+00:00 | COIN | bearish | 4.345 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:13:25+00:00 | MSFT | bullish | 4.337 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:25+00:00 | AMZN | bullish | 4.225 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:26+00:00 | PFE | bullish | 4.121 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:30+00:00 | WFC | bullish | 4.066 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:33+00:00 | HOOD | bullish | 3.857 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:34+00:00 | LOW | bullish | 4.620 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:37+00:00 | UNH | bullish | 3.822 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:37+00:00 | RIVN | bearish | 3.523 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:13:40+00:00 | LCID | bearish | 3.522 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:13:40+00:00 | AAPL | bullish | 4.589 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:40+00:00 | WMT | bullish | 4.509 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:44+00:00 | COIN | bearish | 4.342 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:13:47+00:00 | MSFT | bullish | 4.334 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:47+00:00 | AMZN | bullish | 4.221 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:50+00:00 | PLTR | bullish | 3.430 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:51+00:00 | PFE | bullish | 4.118 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:53+00:00 | HD | bullish | 3.319 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:53+00:00 | NVDA | bullish | 3.080 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:57+00:00 | MS | bullish | 3.015 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:13:57+00:00 | WFC | bullish | 4.063 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:14:01+00:00 | META | bullish | 2.813 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:14:12+00:00 | HOOD | bullish | 3.854 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:14:12+00:00 | UNH | bullish | 3.819 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:14:12+00:00 | RIVN | bearish | 3.520 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:14:15+00:00 | LCID | bearish | 3.519 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:14:22+00:00 | PLTR | bullish | 3.427 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:14:26+00:00 | HD | bullish | 3.316 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:14:27+00:00 | NVDA | bullish | 3.077 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:14:34+00:00 | MS | bullish | 3.013 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:14:35+00:00 | META | bullish | 2.811 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:02+00:00 | LOW | bullish | 4.593 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:03+00:00 | AAPL | bullish | 4.562 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:03+00:00 | WMT | bullish | 4.483 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:04+00:00 | COIN | bearish | 4.317 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:15:05+00:00 | MSFT | bullish | 4.308 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:05+00:00 | AMZN | bullish | 4.193 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:05+00:00 | PFE | bullish | 4.093 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:07+00:00 | LOW | bullish | 4.590 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:07+00:00 | WFC | bullish | 4.040 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:07+00:00 | AAPL | bullish | 4.559 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:07+00:00 | WMT | bullish | 4.481 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:08+00:00 | COIN | bearish | 4.314 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:15:08+00:00 | MSFT | bullish | 4.305 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:08+00:00 | AMZN | bullish | 4.190 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:08+00:00 | PFE | bullish | 4.089 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:09+00:00 | WFC | bullish | 4.037 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:30+00:00 | HOOD | bullish | 3.828 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:31+00:00 | UNH | bullish | 3.795 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:34+00:00 | RIVN | bearish | 3.498 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:15:37+00:00 | LCID | bearish | 3.496 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:15:40+00:00 | HOOD | bullish | 3.831 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:41+00:00 | UNH | bullish | 3.797 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:44+00:00 | RIVN | bearish | 3.501 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:15:44+00:00 | LCID | bearish | 3.498 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:15:49+00:00 | PLTR | bullish | 3.407 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:53+00:00 | PLTR | bullish | 3.408 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:53+00:00 | HD | bullish | 3.296 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:15:56+00:00 | NVDA | bullish | 3.059 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:00+00:00 | HD | bullish | 3.298 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:00+00:00 | NVDA | bullish | 3.061 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:03+00:00 | MS | bullish | 2.995 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:07+00:00 | MS | bullish | 2.996 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:08+00:00 | META | bullish | 2.795 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:11+00:00 | META | bullish | 2.797 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:39+00:00 | MSFT | bullish | 4.577 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:39+00:00 | LOW | bullish | 4.558 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:39+00:00 | WMT | bullish | 4.449 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:43+00:00 | COIN | bearish | 4.284 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:16:44+00:00 | AMZN | bullish | 4.161 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:44+00:00 | PFE | bullish | 4.064 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:45+00:00 | WFC | bullish | 4.010 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:49+00:00 | MSFT | bullish | 4.573 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:49+00:00 | LOW | bullish | 4.553 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:53+00:00 | WMT | bullish | 4.444 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:53+00:00 | HOOD | bullish | 3.804 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:16:53+00:00 | COIN | bearish | 4.280 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:16:59+00:00 | AMZN | bullish | 4.156 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:00+00:00 | UNH | bullish | 3.769 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:00+00:00 | PFE | bullish | 4.060 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:00+00:00 | AAPL | bullish | 3.695 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:17:03+00:00 | RIVN | bearish | 3.475 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:17:03+00:00 | LCID | bearish | 3.475 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:17:04+00:00 | WFC | bullish | 4.006 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:12+00:00 | HOOD | bullish | 3.801 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:15+00:00 | PLTR | bullish | 3.384 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:16+00:00 | HD | bullish | 3.275 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:19+00:00 | NVDA | bullish | 3.040 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:22+00:00 | UNH | bullish | 3.766 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:22+00:00 | AAPL | bullish | 3.691 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:17:22+00:00 | RIVN | bearish | 3.472 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:17:22+00:00 | LCID | bearish | 3.471 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:17:29+00:00 | MS | bullish | 2.976 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:32+00:00 | META | bullish | 2.778 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:41+00:00 | PLTR | bullish | 3.381 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:42+00:00 | HD | bullish | 3.272 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:46+00:00 | NVDA | bullish | 3.037 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:47+00:00 | MS | bullish | 2.974 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:17:52+00:00 | META | bullish | 2.776 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:02+00:00 | MSFT | bullish | 4.546 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:02+00:00 | LOW | bullish | 4.527 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:02+00:00 | WMT | bullish | 4.420 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:03+00:00 | COIN | bearish | 4.255 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:18:06+00:00 | AMZN | bullish | 4.130 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:06+00:00 | PFE | bullish | 4.037 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:07+00:00 | WFC | bullish | 3.984 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:12+00:00 | HOOD | bullish | 3.779 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:19+00:00 | UNH | bullish | 3.745 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:19+00:00 | AAPL | bullish | 3.671 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:18:19+00:00 | RIVN | bearish | 3.454 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:18:19+00:00 | LCID | bearish | 3.453 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:18:23+00:00 | MSFT | bullish | 4.539 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:23+00:00 | LOW | bullish | 4.519 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:29+00:00 | WMT | bullish | 4.411 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:29+00:00 | PLTR | bullish | 3.363 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:33+00:00 | COIN | bearish | 4.248 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:18:33+00:00 | AMZN | bullish | 4.123 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:33+00:00 | HD | bullish | 3.255 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:33+00:00 | PFE | bullish | 4.030 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:36+00:00 | NVDA | bullish | 3.022 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:40+00:00 | MS | bullish | 2.958 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:40+00:00 | WFC | bullish | 3.977 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:44+00:00 | META | bullish | 2.762 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:51+00:00 | HOOD | bullish | 3.773 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:18:55+00:00 | UNH | bullish | 3.739 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:01+00:00 | AAPL | bullish | 3.665 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:19:02+00:00 | RIVN | bearish | 3.448 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:19:02+00:00 | LCID | bearish | 3.447 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:19:09+00:00 | PLTR | bullish | 3.358 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:11+00:00 | HD | bullish | 3.250 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:11+00:00 | NVDA | bullish | 3.017 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:13+00:00 | MS | bullish | 4.708 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:16+00:00 | MS | bullish | 2.954 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:16+00:00 | MSFT | bullish | 4.522 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:16+00:00 | LOW | bullish | 4.503 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:19+00:00 | WMT | bullish | 4.395 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:22+00:00 | META | bullish | 2.758 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:23+00:00 | COIN | bearish | 4.233 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:19:26+00:00 | AMZN | bullish | 4.107 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:29+00:00 | PFE | bullish | 4.016 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:33+00:00 | WFC | bullish | 3.962 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:40+00:00 | HOOD | bullish | 3.760 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:41+00:00 | UNH | bullish | 3.726 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:41+00:00 | AAPL | bullish | 3.652 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:19:44+00:00 | RIVN | bearish | 3.436 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:19:44+00:00 | LCID | bearish | 3.435 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:19:50+00:00 | PLTR | bullish | 3.346 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:51+00:00 | HD | bullish | 3.239 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:51+00:00 | NVDA | bullish | 3.007 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:19:59+00:00 | META | bullish | 2.749 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:10+00:00 | MS | bullish | 4.688 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:10+00:00 | GOOGL | bullish | 4.596 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:10+00:00 | MSFT | bullish | 4.503 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:10+00:00 | LOW | bullish | 4.484 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:10+00:00 | WMT | bullish | 4.377 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:11+00:00 | COIN | bearish | 4.215 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:20:14+00:00 | AMZN | bullish | 4.088 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:14+00:00 | PFE | bullish | 3.999 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:18+00:00 | WFC | bullish | 3.946 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:23+00:00 | HOOD | bullish | 3.744 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:24+00:00 | UNH | bullish | 3.711 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:24+00:00 | AAPL | bullish | 3.638 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:20:28+00:00 | RIVN | bearish | 3.423 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:20:28+00:00 | LCID | bearish | 3.421 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:20:32+00:00 | MS | bullish | 4.680 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:32+00:00 | GOOGL | bullish | 4.588 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:32+00:00 | MSFT | bullish | 4.495 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:35+00:00 | PLTR | bullish | 3.333 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:35+00:00 | LOW | bullish | 4.475 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:38+00:00 | WMT | bullish | 4.369 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:41+00:00 | HD | bullish | 3.226 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:41+00:00 | NVDA | bullish | 2.996 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:45+00:00 | COIN | bearish | 4.208 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:20:45+00:00 | AMZN | bullish | 4.080 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:45+00:00 | PFE | bullish | 3.992 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:49+00:00 | META | bullish | 2.739 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:20:52+00:00 | WFC | bullish | 3.939 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:19+00:00 | MS | bullish | 4.663 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:19+00:00 | WMT | bullish | 4.583 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:22+00:00 | GOOGL | bullish | 4.572 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:22+00:00 | MSFT | bullish | 4.478 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:22+00:00 | LOW | bullish | 4.459 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:26+00:00 | HOOD | bullish | 3.738 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:29+00:00 | COIN | bearish | 4.192 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:21:32+00:00 | UNH | bullish | 3.704 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:32+00:00 | AMZN | bullish | 4.065 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:32+00:00 | PFE | bullish | 3.978 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:32+00:00 | AAPL | bullish | 3.691 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:21:35+00:00 | RIVN | bearish | 3.417 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:21:35+00:00 | LCID | bearish | 3.416 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:21:39+00:00 | WFC | bullish | 3.926 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:43+00:00 | HOOD | bullish | 3.725 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:46+00:00 | UNH | bullish | 3.692 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:47+00:00 | PLTR | bullish | 3.327 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:49+00:00 | AAPL | bullish | 3.679 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:21:49+00:00 | RIVN | bearish | 3.406 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:21:50+00:00 | LCID | bearish | 3.404 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:21:54+00:00 | HD | bullish | 3.221 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:21:54+00:00 | NVDA | bullish | 2.991 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:01+00:00 | META | bullish | 2.735 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:05+00:00 | PLTR | bullish | 3.316 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:08+00:00 | HD | bullish | 3.210 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:08+00:00 | NVDA | bullish | 2.982 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:19+00:00 | META | bullish | 2.726 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:43+00:00 | MS | bullish | 4.633 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:43+00:00 | WMT | bullish | 4.555 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:43+00:00 | GOOGL | bullish | 4.543 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:44+00:00 | MSFT | bullish | 4.450 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:44+00:00 | LOW | bullish | 4.432 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:44+00:00 | MS | bullish | 4.633 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:44+00:00 | WMT | bullish | 4.554 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:44+00:00 | GOOGL | bullish | 4.542 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:44+00:00 | MSFT | bullish | 4.450 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:44+00:00 | COIN | bearish | 4.167 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:22:45+00:00 | LOW | bullish | 4.431 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:45+00:00 | AMZN | bullish | 4.037 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:45+00:00 | PFE | bullish | 3.954 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:45+00:00 | COIN | bearish | 4.167 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:22:45+00:00 | AMZN | bullish | 4.037 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:48+00:00 | PFE | bullish | 3.953 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:49+00:00 | WFC | bullish | 3.902 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:49+00:00 | WFC | bullish | 3.902 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:52+00:00 | HOOD | bullish | 3.703 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:59+00:00 | HOOD | bullish | 3.702 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:59+00:00 | UNH | bullish | 3.670 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:22:59+00:00 | AAPL | bullish | 3.657 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:23:02+00:00 | RIVN | bearish | 3.386 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:23:02+00:00 | LCID | bearish | 3.384 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:23:03+00:00 | UNH | bullish | 3.669 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:23:06+00:00 | AAPL | bullish | 3.656 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:23:06+00:00 | RIVN | bearish | 3.386 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:23:06+00:00 | LCID | bearish | 3.384 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:23:15+00:00 | PLTR | bullish | 3.298 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:23:16+00:00 | PLTR | bullish | 3.297 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:23:18+00:00 | HD | bullish | 3.192 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:23:18+00:00 | NVDA | bullish | 2.965 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:23:28+00:00 | HD | bullish | 3.192 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:23:29+00:00 | META | bullish | 2.712 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:23:32+00:00 | NVDA | bullish | 2.965 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:23:39+00:00 | META | bullish | 2.712 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:01+00:00 | MS | bullish | 4.607 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:01+00:00 | MSFT | bullish | 4.578 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:01+00:00 | WMT | bullish | 4.528 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:01+00:00 | GOOGL | bullish | 4.516 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:02+00:00 | LOW | bullish | 4.407 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:03+00:00 | COIN | bearish | 4.143 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:24:03+00:00 | AMZN | bullish | 4.012 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:03+00:00 | PFE | bullish | 3.932 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:05+00:00 | WFC | bullish | 3.880 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:05+00:00 | MS | bullish | 4.604 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:05+00:00 | MSFT | bullish | 4.576 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:05+00:00 | WMT | bullish | 4.526 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:05+00:00 | GOOGL | bullish | 4.514 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:05+00:00 | LOW | bullish | 4.405 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:09+00:00 | COIN | bearish | 4.142 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:24:12+00:00 | AMZN | bullish | 4.010 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:12+00:00 | PFE | bullish | 3.930 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:13+00:00 | HOOD | bullish | 3.682 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:16+00:00 | WFC | bullish | 3.878 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:16+00:00 | UNH | bullish | 3.650 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:19+00:00 | AAPL | bullish | 3.637 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:24:19+00:00 | RIVN | bearish | 3.368 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:24:19+00:00 | LCID | bearish | 3.366 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:24:30+00:00 | HOOD | bullish | 3.681 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:33+00:00 | UNH | bullish | 3.648 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:33+00:00 | AAPL | bullish | 3.635 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:24:34+00:00 | PLTR | bullish | 3.280 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:38+00:00 | HD | bullish | 3.175 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:39+00:00 | RIVN | bearish | 3.366 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:24:41+00:00 | NVDA | bullish | 2.950 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:54+00:00 | PLTR | bullish | 3.279 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:58+00:00 | HD | bullish | 3.174 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:24:58+00:00 | NVDA | bullish | 2.949 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:12+00:00 | MS | bullish | 4.580 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:12+00:00 | MSFT | bullish | 4.552 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:12+00:00 | WMT | bullish | 4.502 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:12+00:00 | GOOGL | bullish | 4.491 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:13+00:00 | LOW | bullish | 4.381 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:13+00:00 | COIN | bearish | 4.120 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:25:17+00:00 | AMZN | bullish | 3.989 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:17+00:00 | PFE | bullish | 3.910 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:18+00:00 | WFC | bullish | 3.859 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:23+00:00 | HOOD | bullish | 3.663 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:27+00:00 | UNH | bullish | 3.630 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:30+00:00 | MS | bullish | 4.576 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:30+00:00 | MSFT | bullish | 4.548 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:30+00:00 | AAPL | bullish | 3.617 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:25:30+00:00 | WMT | bullish | 4.498 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:30+00:00 | RIVN | bearish | 3.350 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:25:33+00:00 | GOOGL | bullish | 4.488 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:36+00:00 | LOW | bullish | 4.378 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:40+00:00 | COIN | bearish | 4.117 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:25:40+00:00 | AMZN | bullish | 3.985 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:43+00:00 | PFE | bullish | 3.907 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:45+00:00 | PLTR | bullish | 3.263 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:46+00:00 | HD | bullish | 3.159 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:25:53+00:00 | WFC | bullish | 3.856 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:01+00:00 | HOOD | bullish | 3.660 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:05+00:00 | UNH | bullish | 3.627 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:08+00:00 | AAPL | bullish | 3.614 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:26:08+00:00 | RIVN | bearish | 3.347 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:26:14+00:00 | PLTR | bullish | 3.260 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:14+00:00 | HD | bullish | 3.156 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:51+00:00 | MS | bullish | 4.546 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:51+00:00 | MSFT | bullish | 4.518 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:51+00:00 | MS | bullish | 4.546 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:51+00:00 | WMT | bullish | 4.470 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:51+00:00 | MSFT | bullish | 4.518 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:51+00:00 | GOOGL | bullish | 4.458 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:51+00:00 | WMT | bullish | 4.470 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:52+00:00 | LOW | bullish | 4.350 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:52+00:00 | GOOGL | bullish | 4.458 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:52+00:00 | COIN | bearish | 4.091 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:26:52+00:00 | LOW | bullish | 4.350 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:52+00:00 | AMZN | bullish | 3.957 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:52+00:00 | COIN | bearish | 4.091 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:26:52+00:00 | PFE | bullish | 3.882 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:52+00:00 | AMZN | bullish | 3.957 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:52+00:00 | PFE | bullish | 3.882 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:53+00:00 | WFC | bullish | 3.832 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:26:53+00:00 | WFC | bullish | 3.832 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:27:16+00:00 | HOOD | bullish | 3.637 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:27:19+00:00 | HOOD | bullish | 3.637 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:27:23+00:00 | UNH | bullish | 3.605 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:27:23+00:00 | UNH | bullish | 3.605 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:27:23+00:00 | AAPL | bullish | 3.592 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:27:23+00:00 | AAPL | bullish | 3.592 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:27:30+00:00 | RIVN | bearish | 3.328 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:27:33+00:00 | RIVN | bearish | 3.328 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:27:33+00:00 | PLTR | bullish | 3.241 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:27:33+00:00 | PLTR | bullish | 3.241 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:27:40+00:00 | HD | bullish | 3.138 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:27:40+00:00 | HD | bullish | 3.138 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:24+00:00 | MS | bullish | 4.514 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:24+00:00 | MSFT | bullish | 4.486 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | WMT | bullish | 4.438 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | MS | bullish | 4.514 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | GOOGL | bullish | 4.426 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | MSFT | bullish | 4.486 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | LOW | bullish | 4.319 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | WMT | bullish | 4.438 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | COIN | bearish | 4.063 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:28:25+00:00 | GOOGL | bullish | 4.426 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | LOW | bullish | 4.319 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | AMZN | bullish | 3.927 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | COIN | bearish | 4.062 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:28:25+00:00 | PFE | bullish | 3.856 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | AMZN | bullish | 3.927 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:25+00:00 | PFE | bullish | 3.856 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:26+00:00 | WFC | bullish | 3.806 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:29+00:00 | WFC | bullish | 3.806 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:37+00:00 | HOOD | bullish | 3.612 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:37+00:00 | HOOD | bullish | 3.612 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:40+00:00 | UNH | bullish | 3.581 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:43+00:00 | AAPL | bullish | 3.568 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:28:44+00:00 | UNH | bullish | 3.581 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:44+00:00 | AAPL | bullish | 3.568 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:28:47+00:00 | RIVN | bearish | 3.305 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:28:50+00:00 | RIVN | bearish | 3.306 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:28:50+00:00 | PLTR | bullish | 3.220 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:54+00:00 | PLTR | bullish | 3.220 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:55+00:00 | HD | bullish | 3.118 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:28:57+00:00 | HD | bullish | 3.118 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:24+00:00 | MS | bullish | 4.494 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:24+00:00 | MSFT | bullish | 4.466 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:24+00:00 | WMT | bullish | 4.417 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:24+00:00 | GOOGL | bullish | 4.407 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:25+00:00 | COIN | bearish | 4.044 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:29:25+00:00 | AMZN | bullish | 3.908 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:25+00:00 | PFE | bullish | 3.839 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:27+00:00 | WFC | bullish | 3.789 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:30+00:00 | HOOD | bullish | 3.597 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:31+00:00 | UNH | bullish | 3.565 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:31+00:00 | AAPL | bullish | 3.553 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:29:31+00:00 | LOW | bullish | 3.535 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:29:32+00:00 | MS | bullish | 4.490 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:35+00:00 | RIVN | bearish | 3.292 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:29:35+00:00 | PLTR | bullish | 3.206 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:38+00:00 | MSFT | bullish | 4.463 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:38+00:00 | WMT | bullish | 4.415 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:41+00:00 | GOOGL | bullish | 4.403 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:41+00:00 | COIN | bearish | 4.042 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:29:41+00:00 | AMZN | bullish | 3.906 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:42+00:00 | PFE | bullish | 3.837 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:45+00:00 | HD | bullish | 3.105 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:48+00:00 | WFC | bullish | 3.786 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:54+00:00 | HOOD | bullish | 3.595 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:58+00:00 | UNH | bullish | 3.563 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:29:58+00:00 | AAPL | bullish | 3.551 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:29:58+00:00 | LOW | bullish | 3.533 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:30:02+00:00 | RIVN | bearish | 3.290 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:30:02+00:00 | PLTR | bullish | 3.205 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:04+00:00 | HD | bullish | 3.103 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:31+00:00 | MS | bullish | 4.471 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:32+00:00 | MSFT | bullish | 4.443 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:32+00:00 | WMT | bullish | 4.395 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:32+00:00 | GOOGL | bullish | 4.384 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:32+00:00 | COIN | bearish | 4.025 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:30:32+00:00 | AMZN | bullish | 3.887 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:32+00:00 | PFE | bullish | 3.820 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:33+00:00 | MS | bullish | 4.470 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:33+00:00 | MSFT | bullish | 4.443 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:33+00:00 | WMT | bullish | 4.395 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:33+00:00 | GOOGL | bullish | 4.383 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:33+00:00 | COIN | bearish | 4.024 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:30:33+00:00 | AMZN | bullish | 3.887 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:33+00:00 | PFE | bullish | 3.820 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:33+00:00 | WFC | bullish | 3.771 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:34+00:00 | WFC | bullish | 3.770 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:41+00:00 | HOOD | bullish | 3.580 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:44+00:00 | UNH | bullish | 3.548 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:44+00:00 | AAPL | bullish | 3.536 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:30:44+00:00 | LOW | bullish | 3.518 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:30:45+00:00 | HOOD | bullish | 3.579 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:48+00:00 | RIVN | bearish | 3.276 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:30:51+00:00 | UNH | bullish | 3.548 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:51+00:00 | AAPL | bullish | 3.536 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:30:51+00:00 | PLTR | bullish | 3.192 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:54+00:00 | LOW | bullish | 3.518 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:30:58+00:00 | RIVN | bearish | 3.276 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:30:59+00:00 | PLTR | bullish | 3.191 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:30:59+00:00 | HD | bullish | 3.091 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:02+00:00 | MA | bullish | 2.987 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:31:03+00:00 | HD | bullish | 3.091 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:04+00:00 | NVDA | bullish | 2.873 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:06+00:00 | MA | bullish | 2.987 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:31:11+00:00 | NVDA | bullish | 2.873 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:33+00:00 | MSFT | bullish | 4.580 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:34+00:00 | MS | bullish | 4.450 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:34+00:00 | WMT | bullish | 4.374 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:34+00:00 | GOOGL | bullish | 4.363 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:34+00:00 | COIN | bearish | 4.006 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:31:34+00:00 | AMZN | bullish | 3.868 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:35+00:00 | PFE | bullish | 3.803 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:36+00:00 | WFC | bullish | 3.753 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:38+00:00 | AAPL | bullish | 3.696 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:31:40+00:00 | MSFT | bullish | 4.577 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:40+00:00 | HOOD | bullish | 3.564 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:43+00:00 | MS | bullish | 4.447 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:43+00:00 | WMT | bullish | 4.372 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:46+00:00 | GOOGL | bullish | 4.361 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:46+00:00 | COIN | bearish | 4.003 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:31:46+00:00 | AMZN | bullish | 3.866 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:46+00:00 | PFE | bullish | 3.801 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:46+00:00 | UNH | bullish | 3.532 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:49+00:00 | LOW | bullish | 3.502 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:31:53+00:00 | WFC | bullish | 3.751 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:53+00:00 | RIVN | bearish | 3.262 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:31:53+00:00 | PLTR | bullish | 3.178 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:54+00:00 | AAPL | bullish | 3.694 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:31:57+00:00 | HD | bullish | 3.077 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:31:57+00:00 | MA | bullish | 2.974 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:32:04+00:00 | HOOD | bullish | 3.562 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:04+00:00 | NVDA | bullish | 2.861 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:08+00:00 | UNH | bullish | 3.530 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:11+00:00 | LOW | bullish | 3.500 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:32:15+00:00 | RIVN | bearish | 3.260 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:32:15+00:00 | PLTR | bullish | 3.176 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:22+00:00 | HD | bullish | 3.076 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:22+00:00 | MA | bullish | 2.973 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:32:24+00:00 | NVDA | bullish | 2.860 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:31+00:00 | MSFT | bullish | 4.560 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:31+00:00 | MS | bullish | 4.430 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:31+00:00 | WMT | bullish | 4.354 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:31+00:00 | GOOGL | bullish | 4.344 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:34+00:00 | COIN | bearish | 3.988 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:32:37+00:00 | AMZN | bullish | 3.850 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:37+00:00 | PFE | bullish | 3.787 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:41+00:00 | WFC | bullish | 3.737 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:42+00:00 | AAPL | bullish | 3.681 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:32:54+00:00 | MSFT | bullish | 4.551 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:54+00:00 | MS | bullish | 4.422 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:54+00:00 | WMT | bullish | 4.347 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:54+00:00 | GOOGL | bullish | 4.337 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:54+00:00 | COIN | bearish | 3.981 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:32:57+00:00 | AMZN | bullish | 3.842 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:32:57+00:00 | PFE | bullish | 3.780 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:01+00:00 | WFC | bullish | 3.731 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:04+00:00 | HOOD | bullish | 3.549 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:06+00:00 | UNH | bullish | 3.517 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:07+00:00 | LOW | bullish | 3.487 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:33:26+00:00 | MSFT | bullish | 4.541 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:26+00:00 | MS | bullish | 4.412 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:27+00:00 | WMT | bullish | 4.337 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:27+00:00 | GOOGL | bullish | 4.326 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:27+00:00 | COIN | bearish | 3.972 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:33:27+00:00 | AMZN | bullish | 3.833 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:27+00:00 | PFE | bullish | 3.772 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:29+00:00 | WFC | bullish | 3.723 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:30+00:00 | AAPL | bullish | 3.667 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:33:33+00:00 | MSFT | bullish | 4.538 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:33+00:00 | MS | bullish | 4.409 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:33+00:00 | WMT | bullish | 4.334 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:34+00:00 | HOOD | bullish | 3.535 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:36+00:00 | GOOGL | bullish | 4.324 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:36+00:00 | COIN | bearish | 3.970 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:33:36+00:00 | AMZN | bullish | 3.831 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:39+00:00 | PFE | bullish | 3.770 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:41+00:00 | UNH | bullish | 3.504 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:41+00:00 | LOW | bullish | 3.474 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:33:43+00:00 | WFC | bullish | 3.720 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:46+00:00 | AAPL | bullish | 3.664 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:33:47+00:00 | RIVN | bearish | 3.236 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:33:50+00:00 | HOOD | bullish | 3.533 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:53+00:00 | PLTR | bullish | 3.153 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:54+00:00 | UNH | bullish | 3.502 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:33:57+00:00 | LOW | bullish | 3.472 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:34:00+00:00 | HD | bullish | 3.054 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:00+00:00 | RIVN | bearish | 3.234 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:34:00+00:00 | MA | bullish | 2.952 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:34:00+00:00 | PLTR | bullish | 3.151 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:04+00:00 | NVDA | bullish | 2.840 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:04+00:00 | HD | bullish | 3.052 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:07+00:00 | MA | bullish | 2.950 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:34:11+00:00 | NVDA | bullish | 2.838 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:35+00:00 | MSFT | bullish | 4.517 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:35+00:00 | MS | bullish | 4.389 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:35+00:00 | WMT | bullish | 4.315 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:35+00:00 | GOOGL | bullish | 4.304 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:37+00:00 | COIN | bearish | 3.953 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:34:37+00:00 | AMZN | bullish | 3.812 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:37+00:00 | PFE | bullish | 3.753 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:39+00:00 | WFC | bullish | 3.705 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:40+00:00 | MSFT | bullish | 4.515 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:40+00:00 | AAPL | bullish | 3.649 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:34:40+00:00 | MS | bullish | 4.386 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:43+00:00 | WMT | bullish | 4.313 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:43+00:00 | GOOGL | bullish | 4.302 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:47+00:00 | COIN | bearish | 3.950 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:34:47+00:00 | HOOD | bullish | 3.518 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:47+00:00 | AMZN | bullish | 3.810 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:50+00:00 | PFE | bullish | 3.751 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:51+00:00 | UNH | bullish | 3.487 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:54+00:00 | LOW | bullish | 3.457 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:34:54+00:00 | RIVN | bearish | 3.221 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:34:54+00:00 | WFC | bullish | 3.702 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:54+00:00 | PLTR | bullish | 3.138 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:34:58+00:00 | AAPL | bullish | 3.646 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:35:01+00:00 | HD | bullish | 3.040 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:04+00:00 | MA | bullish | 2.938 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:35:05+00:00 | HOOD | bullish | 3.516 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:08+00:00 | NVDA | bullish | 2.827 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:08+00:00 | UNH | bullish | 3.485 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:11+00:00 | LOW | bullish | 3.456 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:35:12+00:00 | RIVN | bearish | 3.219 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:35:15+00:00 | PLTR | bullish | 3.137 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:23+00:00 | HD | bullish | 3.038 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:23+00:00 | MA | bullish | 2.937 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:35:24+00:00 | NVDA | bullish | 2.826 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:31+00:00 | MSFT | bullish | 4.497 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:31+00:00 | MS | bullish | 4.369 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:34+00:00 | WMT | bullish | 4.296 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:34+00:00 | GOOGL | bullish | 4.285 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:38+00:00 | COIN | bearish | 3.935 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:35:38+00:00 | AMZN | bullish | 3.794 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:38+00:00 | PFE | bullish | 3.737 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:45+00:00 | WFC | bullish | 3.688 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:46+00:00 | AAPL | bullish | 3.633 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:35:50+00:00 | HOOD | bullish | 3.503 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:50+00:00 | UNH | bullish | 3.472 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:53+00:00 | LOW | bullish | 3.443 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:35:54+00:00 | RIVN | bearish | 3.208 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:35:54+00:00 | PLTR | bullish | 3.125 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:58+00:00 | HD | bullish | 3.027 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:35:59+00:00 | MA | bullish | 2.927 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:36:00+00:00 | NVDA | bullish | 2.816 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:03+00:00 | MSFT | bullish | 4.486 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:03+00:00 | MS | bullish | 4.359 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:03+00:00 | WMT | bullish | 4.285 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:03+00:00 | GOOGL | bullish | 4.275 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:07+00:00 | COIN | bearish | 3.926 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:36:10+00:00 | AMZN | bullish | 3.784 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:10+00:00 | PFE | bullish | 3.728 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:11+00:00 | WFC | bullish | 3.680 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:16+00:00 | AAPL | bullish | 3.625 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:36:23+00:00 | HOOD | bullish | 3.495 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:24+00:00 | UNH | bullish | 3.464 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:25+00:00 | LOW | bullish | 3.435 | adaptive_weights_active; mild_toxicity(0.38); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:36:28+00:00 | RIVN | bearish | 3.201 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:36:28+00:00 | PLTR | bullish | 3.119 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:31+00:00 | MSFT | bullish | 4.477 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:31+00:00 | MS | bullish | 4.350 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:31+00:00 | LOW | bearish | 4.346 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:36:34+00:00 | WMT | bullish | 4.276 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:34+00:00 | GOOGL | bullish | 4.266 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:35+00:00 | HD | bullish | 3.021 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:38+00:00 | COIN | bearish | 3.918 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:36:38+00:00 | AMZN | bullish | 3.776 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:41+00:00 | MA | bullish | 2.921 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:36:41+00:00 | PFE | bullish | 3.721 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:45+00:00 | WFC | bullish | 3.672 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:45+00:00 | NVDA | bullish | 2.810 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:50+00:00 | AAPL | bullish | 3.617 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:36:58+00:00 | HOOD | bullish | 3.488 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:59+00:00 | UNH | bullish | 3.457 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:36:59+00:00 | RIVN | bearish | 3.194 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:37:03+00:00 | PLTR | bullish | 3.112 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:04+00:00 | HD | bullish | 3.015 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:04+00:00 | MA | bullish | 2.915 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:37:06+00:00 | NVDA | bullish | 2.805 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:06+00:00 | MSFT | bullish | 4.465 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:09+00:00 | MS | bullish | 4.338 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:09+00:00 | LOW | bearish | 4.335 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:37:09+00:00 | WMT | bullish | 4.265 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:09+00:00 | GOOGL | bullish | 4.255 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:13+00:00 | COIN | bearish | 3.908 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:37:16+00:00 | AMZN | bullish | 3.765 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:16+00:00 | PFE | bullish | 3.711 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:17+00:00 | WFC | bullish | 3.663 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:24+00:00 | AAPL | bullish | 3.608 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:37:28+00:00 | HOOD | bullish | 3.480 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:32+00:00 | UNH | bullish | 3.449 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:32+00:00 | RIVN | bearish | 3.187 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:37:35+00:00 | PLTR | bullish | 3.105 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:37+00:00 | MSFT | bullish | 4.454 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:37+00:00 | MS | bullish | 4.328 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:37+00:00 | LOW | bearish | 4.325 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:37:40+00:00 | HD | bullish | 3.008 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:40+00:00 | WMT | bullish | 4.255 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:40+00:00 | MA | bullish | 2.908 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:37:43+00:00 | GOOGL | bullish | 4.245 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:43+00:00 | NVDA | bullish | 2.798 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:46+00:00 | COIN | bearish | 3.899 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:37:46+00:00 | AMZN | bullish | 3.756 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:50+00:00 | PFE | bullish | 3.703 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:54+00:00 | WFC | bullish | 3.655 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:37:55+00:00 | AAPL | bullish | 3.600 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:37:59+00:00 | HOOD | bullish | 3.472 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:02+00:00 | UNH | bullish | 3.441 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:02+00:00 | RIVN | bearish | 3.180 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:38:03+00:00 | PLTR | bullish | 3.098 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:06+00:00 | HD | bullish | 3.002 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:06+00:00 | MA | bullish | 2.902 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:38:10+00:00 | NVDA | bullish | 2.793 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:33+00:00 | MSFT | bullish | 4.436 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:33+00:00 | MS | bullish | 4.311 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:34+00:00 | LOW | bearish | 4.308 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:38:34+00:00 | WMT | bullish | 4.239 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:34+00:00 | GOOGL | bullish | 4.228 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:34+00:00 | MSFT | bullish | 4.435 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:34+00:00 | MS | bullish | 4.310 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:34+00:00 | LOW | bearish | 4.307 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:38:35+00:00 | WMT | bullish | 4.239 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:35+00:00 | GOOGL | bullish | 4.227 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:35+00:00 | COIN | bearish | 3.884 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:38:35+00:00 | AMZN | bullish | 3.739 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:35+00:00 | PFE | bullish | 3.688 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:35+00:00 | COIN | bearish | 3.884 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:38:35+00:00 | AMZN | bullish | 3.739 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:38+00:00 | PFE | bullish | 3.688 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:39+00:00 | WFC | bullish | 3.641 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:42+00:00 | WFC | bullish | 3.640 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:43+00:00 | AAPL | bullish | 3.586 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:38:46+00:00 | AAPL | bullish | 3.586 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:38:53+00:00 | HOOD | bullish | 3.458 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:53+00:00 | HOOD | bullish | 3.458 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:57+00:00 | UNH | bullish | 3.428 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:57+00:00 | UNH | bullish | 3.428 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:38:57+00:00 | RIVN | bearish | 3.168 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:39:00+00:00 | RIVN | bearish | 3.169 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:39:00+00:00 | PLTR | bullish | 3.087 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:00+00:00 | PLTR | bullish | 3.088 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:25+00:00 | META | bullish | 4.670 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:27+00:00 | MSFT | bullish | 4.418 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:27+00:00 | MS | bullish | 4.294 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:27+00:00 | LOW | bearish | 4.291 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:39:28+00:00 | WMT | bullish | 4.222 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:28+00:00 | GOOGL | bullish | 4.211 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:29+00:00 | COIN | bearish | 3.869 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:39:29+00:00 | AMZN | bullish | 3.724 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:29+00:00 | PFE | bullish | 3.675 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:30+00:00 | META | bullish | 4.668 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:31+00:00 | WFC | bullish | 3.627 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:31+00:00 | MSFT | bullish | 4.416 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:31+00:00 | MS | bullish | 4.292 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:32+00:00 | LOW | bearish | 4.289 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:39:32+00:00 | AAPL | bullish | 3.573 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:39:35+00:00 | WMT | bullish | 4.220 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:35+00:00 | GOOGL | bullish | 4.210 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:38+00:00 | COIN | bearish | 3.867 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:39:41+00:00 | AMZN | bullish | 3.722 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:41+00:00 | PFE | bullish | 3.673 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:42+00:00 | HOOD | bullish | 3.446 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:45+00:00 | WFC | bullish | 3.626 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:45+00:00 | UNH | bullish | 3.416 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:48+00:00 | RIVN | bearish | 3.157 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:39:52+00:00 | AAPL | bullish | 3.571 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:39:52+00:00 | HD | bullish | 2.980 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:53+00:00 | MA | bullish | 2.882 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:39:59+00:00 | HOOD | bullish | 3.444 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:39:59+00:00 | NVDA | bullish | 2.773 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:03+00:00 | UNH | bullish | 3.414 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:03+00:00 | RIVN | bearish | 3.156 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:40:07+00:00 | HD | bullish | 2.979 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:07+00:00 | MA | bullish | 2.880 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:40:11+00:00 | NVDA | bullish | 2.772 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:27+00:00 | META | bullish | 4.648 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:28+00:00 | WMT | bullish | 4.577 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:28+00:00 | MSFT | bullish | 4.398 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:28+00:00 | MS | bullish | 4.274 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:28+00:00 | LOW | bearish | 4.271 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:40:29+00:00 | GOOGL | bullish | 4.192 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:30+00:00 | COIN | bearish | 3.851 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:40:30+00:00 | AMZN | bullish | 3.705 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:30+00:00 | PFE | bullish | 3.658 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:35+00:00 | WFC | bullish | 3.611 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:38+00:00 | META | bullish | 4.644 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:39+00:00 | AAPL | bullish | 3.557 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:40:43+00:00 | HOOD | bullish | 3.431 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:46+00:00 | UNH | bullish | 3.401 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:46+00:00 | RIVN | bearish | 3.143 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:40:49+00:00 | WMT | bullish | 4.574 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:49+00:00 | MSFT | bullish | 4.395 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:50+00:00 | MS | bullish | 4.271 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:50+00:00 | LOW | bearish | 4.268 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:40:50+00:00 | GOOGL | bullish | 4.189 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:50+00:00 | HD | bullish | 2.968 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:53+00:00 | MA | bullish | 2.870 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:40:56+00:00 | COIN | bearish | 3.849 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:40:56+00:00 | AMZN | bullish | 3.703 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:40:57+00:00 | PFE | bullish | 3.656 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:00+00:00 | NVDA | bullish | 2.762 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:01+00:00 | WFC | bullish | 3.609 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:05+00:00 | AAPL | bullish | 3.555 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:41:09+00:00 | HOOD | bullish | 3.428 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:14+00:00 | UNH | bullish | 3.398 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:14+00:00 | RIVN | bearish | 3.141 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:41:18+00:00 | HD | bullish | 2.966 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:18+00:00 | MA | bullish | 2.868 | adaptive_weights_active; congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); calendar_neutral_default;… |
| 2026-01-15T20:41:18+00:00 | NVDA | bullish | 2.760 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:31+00:00 | META | bullish | 4.624 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:32+00:00 | WMT | bullish | 4.554 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:35+00:00 | MSFT | bullish | 4.376 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:36+00:00 | MS | bullish | 4.252 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:36+00:00 | LOW | bearish | 4.249 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:41:36+00:00 | GOOGL | bullish | 4.171 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:40+00:00 | COIN | bearish | 3.833 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:41:40+00:00 | AMZN | bullish | 3.686 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:41+00:00 | PFE | bullish | 3.641 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:44+00:00 | META | bullish | 4.620 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:45+00:00 | WFC | bullish | 3.594 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:48+00:00 | WMT | bullish | 4.549 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:48+00:00 | MSFT | bullish | 4.373 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:48+00:00 | AAPL | bullish | 3.540 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:41:51+00:00 | MS | bullish | 4.249 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:51+00:00 | LOW | bearish | 4.246 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:41:51+00:00 | GOOGL | bullish | 4.168 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:55+00:00 | HOOD | bullish | 3.415 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:55+00:00 | COIN | bearish | 3.829 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:41:58+00:00 | AMZN | bullish | 3.683 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:41:58+00:00 | PFE | bullish | 3.638 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:02+00:00 | UNH | bullish | 3.385 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:02+00:00 | RIVN | bearish | 3.129 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:42:06+00:00 | WFC | bullish | 3.591 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:06+00:00 | HD | bullish | 2.954 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:09+00:00 | AAPL | bullish | 3.537 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:42:10+00:00 | NVDA | bullish | 2.750 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:13+00:00 | HOOD | bullish | 3.412 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:17+00:00 | UNH | bullish | 3.382 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:20+00:00 | RIVN | bearish | 3.127 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:42:20+00:00 | HD | bullish | 2.952 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:25+00:00 | NVDA | bullish | 2.748 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:47+00:00 | META | bullish | 4.598 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:49+00:00 | WMT | bullish | 4.528 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:50+00:00 | MSFT | bullish | 4.352 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:50+00:00 | MS | bullish | 4.229 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:50+00:00 | LOW | bearish | 4.226 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:42:50+00:00 | GOOGL | bullish | 4.148 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:51+00:00 | COIN | bearish | 3.812 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:42:51+00:00 | AMZN | bullish | 3.664 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:52+00:00 | META | bullish | 4.596 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:53+00:00 | WMT | bullish | 4.526 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:54+00:00 | MSFT | bullish | 4.349 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:54+00:00 | MS | bullish | 4.227 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:42:57+00:00 | LOW | bearish | 4.224 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:42:57+00:00 | AAPL | bullish | 3.521 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:42:57+00:00 | GOOGL | bullish | 4.146 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:01+00:00 | COIN | bearish | 3.810 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:43:01+00:00 | AMZN | bullish | 3.662 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:04+00:00 | HOOD | bullish | 3.397 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:07+00:00 | UNH | bullish | 3.367 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:08+00:00 | RIVN | bearish | 3.113 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:43:11+00:00 | HD | bullish | 2.940 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:11+00:00 | AAPL | bullish | 3.520 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:43:14+00:00 | NVDA | bullish | 2.737 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:19+00:00 | HOOD | bullish | 3.395 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:22+00:00 | UNH | bullish | 3.366 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:22+00:00 | RIVN | bearish | 3.112 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:43:25+00:00 | HD | bullish | 2.939 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:29+00:00 | NVDA | bullish | 2.736 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:53+00:00 | META | bullish | 4.575 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:56+00:00 | WMT | bullish | 4.506 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:56+00:00 | MSFT | bullish | 4.330 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:56+00:00 | META | bullish | 4.575 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:56+00:00 | MS | bullish | 4.208 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:56+00:00 | LOW | bearish | 4.206 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:43:56+00:00 | GOOGL | bullish | 4.128 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:57+00:00 | COIN | bearish | 3.794 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:43:57+00:00 | WMT | bullish | 4.505 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:57+00:00 | AMZN | bullish | 3.645 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:57+00:00 | MSFT | bullish | 4.329 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:57+00:00 | MS | bullish | 4.208 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:43:57+00:00 | LOW | bearish | 4.205 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:43:57+00:00 | GOOGL | bullish | 4.127 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:44:01+00:00 | COIN | bearish | 3.794 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:44:04+00:00 | AMZN | bullish | 3.644 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:44:05+00:00 | AAPL | bullish | 3.505 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:44:10+00:00 | AAPL | bullish | 3.505 | adaptive_weights_active; mild_toxicity(0.41); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); cale… |
| 2026-01-15T20:44:21+00:00 | HOOD | bullish | 3.381 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:44:21+00:00 | UNH | bullish | 3.352 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:44:21+00:00 | HOOD | bullish | 3.380 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:44:24+00:00 | RIVN | bearish | 3.099 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:44:24+00:00 | HD | bullish | 2.927 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:44:27+00:00 | UNH | bullish | 3.351 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:44:30+00:00 | NVDA | bullish | 2.725 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:44:30+00:00 | RIVN | bearish | 3.099 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:44:34+00:00 | HD | bullish | 2.927 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:44:37+00:00 | NVDA | bullish | 2.725 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:25+00:00 | META | bullish | 4.547 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:25+00:00 | META | bullish | 4.545 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:26+00:00 | WMT | bullish | 4.480 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:26+00:00 | AAPL | bearish | 4.411 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:45:26+00:00 | MSFT | bullish | 4.301 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:26+00:00 | WMT | bullish | 4.477 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:26+00:00 | LOW | bearish | 4.180 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:45:26+00:00 | AAPL | bearish | 4.409 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:45:26+00:00 | MS | bullish | 4.180 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:26+00:00 | MSFT | bullish | 4.300 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:26+00:00 | GOOGL | bullish | 4.100 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:26+00:00 | MS | bullish | 4.179 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:26+00:00 | LOW | bearish | 4.178 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:45:27+00:00 | GOOGL | bullish | 4.099 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:27+00:00 | COIN | bearish | 3.771 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:45:27+00:00 | AMZN | bullish | 3.619 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:27+00:00 | COIN | bearish | 3.770 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:45:27+00:00 | AMZN | bullish | 3.618 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:28+00:00 | HOOD | bullish | 3.359 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:28+00:00 | HOOD | bullish | 3.359 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:29+00:00 | UNH | bullish | 3.332 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:29+00:00 | UNH | bullish | 3.330 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:34+00:00 | RIVN | bearish | 3.080 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:45:34+00:00 | RIVN | bearish | 3.081 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_oppose(81%C); ca… |
| 2026-01-15T20:45:38+00:00 | HD | bullish | 2.910 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:38+00:00 | NVDA | bullish | 2.709 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:41+00:00 | HD | bullish | 2.911 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:45:41+00:00 | NVDA | bullish | 2.710 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:08+00:00 | META | bullish | 4.529 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:12+00:00 | META | bullish | 4.528 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:35+00:00 | NVDA | bullish | 4.718 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:35+00:00 | META | bullish | 4.519 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:38+00:00 | NVDA | bullish | 4.717 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:38+00:00 | META | bullish | 4.519 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:58+00:00 | NVDA | bullish | 4.709 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:46:58+00:00 | META | bullish | 4.511 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:47:01+00:00 | NVDA | bullish | 4.708 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |
| 2026-01-15T20:47:01+00:00 | META | bullish | 4.510 | adaptive_weights_active; toxicity_penalty(0.70); congress_neutral_default; shorts_neutral_default; tide_confirm(81%C); c… |

</details>

## 6. Counter / opposing signals
- **Direction-flip conflicts (≤10 min apart, same symbol):** 12

| Symbol | Initial | Counter | Δt | Decision observed | PnL outcome (nearest close) |
| --- | --- | --- | --- | --- | --- |
| V | bullish | bearish | 4s | no_immediate_close_observed | — |
| LOW | bullish | bearish | 7s | no_immediate_close_observed | — |
| BLK | bearish | bullish | 10s | no_immediate_close_observed | — |
| PLTR | bullish | bearish | 18s | no_immediate_close_observed | — |
| LOW | bearish | bullish | 32s | no_immediate_close_observed | — |
| LOW | bullish | bearish | 33s | no_immediate_close_observed | — |
| BLK | bullish | bearish | 39s | no_immediate_close_observed | — |
| LOW | bullish | bearish | 40s | no_immediate_close_observed | — |
| COIN | bullish | bearish | 55s | no_immediate_close_observed | — |
| LOW | bearish | bullish | 56s | no_immediate_close_observed | — |
| AAPL | bullish | bearish | 76s | no_immediate_close_observed | — |
| COST | bullish | bearish | 106s | no_immediate_close_observed | — |

**PnL impact vs alternative:** not reliably computable today because we do not have a standardized “counter-signal decision record” with mid/mark prices at conflict time.

## 7. Risk & controls
- **Gate events logged:** 1885
- **Top gate events:** max_one_position_per_symbol=1056, momentum_ignition_passed=495, expectancy_blocked=222, max_new_positions_per_cycle_reached=100, max_positions_reached=9, symbol_on_cooldown=3

**Observed posture:** heavy blocking volume vs executions (blocked 570 vs 94 executed attribution events) suggests conservative gating/validation during this session.

## 8. Operational health
- **Total orders logged:** 2410
- **Order error/failed events (heuristic):** 1621
- **Top order errors/actions:** cannot access local variable 'time' where it is not associated with a value=783, submit_entry_failed=514, asset "LCID" cannot be sold short=265, client_order_id must be unique=24, invalid limit_price 115.945. sub-penny increment does not fulfill minimum pricing criteria=6, invalid limit_price 52.955. sub-penny increment does not fulfill minimum pricing criteria=6, invalid limit_price 277.505. sub-penny increment does not fulfill minimum pricing criteria=4, invalid limit_price 277.1326. sub-penny increment does not fulfill minimum pricing criteria=2, invalid limit_price 129.6702. sub-penny increment does not fulfill minimum pricing criteria=2, invalid limit_price 377.5621. sub-penny increment does not fulfill minimum pricing criteria=2, invalid limit_price 109.7901. sub-penny increment does not fulfill minimum pricing criteria=2, invalid limit_price 52.9699. sub-penny increment does not fulfill minimum pricing criteria=2

**Logging gap:** droplet path `/root/stock-bot/logs/exits.jsonl` was not found today; exit details appear only indirectly inside `attribution.jsonl` close events.

## 9. Improvement opportunities
- **Signal-level**: prioritize evaluating why a high volume of `gate_passed` signals do not translate into executions; add an explicit `final_decision` record tying signal → (executed|blocked|skipped) with a single correlation id.
- **Execution**: add consistent `client_order_id` / `correlation_id` to `orders.jsonl` filled records so we can join to attribution and compute slippage/time-to-fill per trade.
- **Risk**: `order_validation_failed` blocks often include explicit size constraint text; consider logging the numeric limit inputs (max position USD, per-name cap, equity) as structured fields (not just string).
- **Logging**: restore or standardize `exits.jsonl` (or deprecate it explicitly) and ensure all report-critical logs exist daily.

## 10. Appendix
### Sources used (droplet paths)
- `logs/attribution.jsonl` (executed trade attribution; includes close context with entry/exit and reason)
- `state/blocked_trades.jsonl` (blocked trade candidates with reason codes and validation errors)
- `logs/signals.jsonl` (signal snapshots including composite meta, components, motifs, expanded intel)
- `logs/orders.jsonl` (order events including fills and errors)
- `logs/gate.jsonl` (gate events / blockers and gate telemetry)
- `logs/exits.jsonl` (**missing today on droplet**)

### Repro script
- `reports/_daily_review_tools/generate_daily_review.py` (this report generator; uses `ReportDataFetcher(date='2026-01-15')`)

### Detailed exports (machine-readable)
- `reports/stock-bot-daily-review-2026-01-15-artifacts/daily_review_details.json` (summary + tables)
- `reports/stock-bot-daily-review-2026-01-15-artifacts/closed_trades.csv` (realized closes/scales)
- `reports/stock-bot-daily-review-2026-01-15-artifacts/open_events.csv` (executed opens, with nearest fill px)
- `reports/stock-bot-daily-review-2026-01-15-artifacts/blocked_trades.csv` (all blocked trades, filtered to date)
- `reports/stock-bot-daily-review-2026-01-15-artifacts/missed_candidates.csv` (all missed-trade candidates, filtered to date)
- `reports/stock-bot-daily-review-2026-01-15-artifacts/counter_conflicts.csv` (direction flips within 10 minutes)
- `reports/stock-bot-daily-review-2026-01-15-artifacts/per_symbol_summary.csv`
- `reports/stock-bot-daily-review-2026-01-15-artifacts/per_signal_summary.csv`
- `reports/stock-bot-daily-review-2026-01-15-artifacts/order_errors_summary.csv`
- `reports/stock-bot-daily-review-2026-01-15-artifacts/gate_events_summary.csv`

