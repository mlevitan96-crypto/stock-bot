# Trading environment review

Generated: 2026-02-24T23:41:59.903084+00:00
Last **150** closed equity trades (from logs/attribution.jsonl + logs/exit_attribution.jsonl).

## 1) Signal health (entry and exit signals firing)

- **Expectancy gate truth (last 7d):** 0 lines
- **Decision ledger (last 7d):** 0 lines
- **Orders filled (recent):** 1333
- **Submit order called (recent):** 0

**Verdict:** Entry signals are firing if gate_truth and ledger have recent activity; exit signals are firing if exit_attribution has recent lines and trades below have v2_exit_score populated.

## 2) Last 150 trades summary

- **Trades included:** 150
- **With entry_score:** 150
- **With v2_exit_score:** 150

## 3) Full list of entry signal scores (component stats)

| Signal | Count | Mean | Min | Max |
|--------|-------|------|-----|-----|
| flow | 142 | 2.2919 | 1.147 | 2.4 |
| dark_pool | 142 | 0.1737 | 0.172 | 0.175 |
| insider | 142 | 0.0835 | 0.083 | 0.084 |
| iv_skew | 142 | 0.0607 | 0.004 | 0.079 |
| smile | 142 | 0.005 | 0.005 | 0.005 |
| whale | 142 | 0.0 | 0.0 | 0.0 |
| event | 142 | 0.2179 | 0.053 | 0.228 |
| motif_bonus | 142 | 0.0 | 0.0 | 0.0 |
| toxicity_penalty | 142 | -0.1562 | -0.181 | -0.004 |
| regime | 142 | 0.008 | 0.008 | 0.008 |
| congress | 142 | 0.0065 | 0.0 | 0.072 |
| shorts_squeeze | 142 | 0.0 | 0.0 | 0.0 |
| institutional | 142 | 0.0 | 0.0 | 0.0 |
| market_tide | 142 | 0.1207 | -0.05 | 0.227 |
| calendar | 142 | 0.0 | 0.0 | 0.0 |
| greeks_gamma | 142 | 0.118 | 0.027 | 0.134 |
| ftd_pressure | 142 | 0.04 | 0.04 | 0.04 |
| iv_rank | 142 | 0.0733 | 0.02 | 0.134 |
| oi_change | 142 | 0.0469 | 0.046 | 0.047 |
| etf_flow | 142 | 0.04 | 0.04 | 0.04 |
| squeeze_score | 142 | 0.0515 | 0.026 | 0.067 |
| freshness_factor | 142 | 0.9343 | 0.805 | 0.996 |

## 4) Full list of exit signal scores (v2_exit_components stats)

(No v2_exit_components found; ensure exit_attribution is written on full closes.)

## 5) Persona profitability review

- **Win rate:** 35.3%
- **Total PnL (USD):** -6.52
- **Trades count:** 150

### By entry score bucket

- **mid_2.5_3.5:** count=88, win_rate=34.1%, avg_pnl=-0.03
- **high_>=3.5:** count=62, win_rate=37.1%, avg_pnl=-0.06

### By exit score bucket

- **low_<2:** count=150, win_rate=35.3%, avg_pnl=-0.04

### How to get better

- Win rate below 50%: consider tightening entry threshold (e.g. MIN_EXEC_SCORE) or improving exit timing (review v2_exit_score distribution vs PnL).
- High entry-score bucket (>=3.5) is losing on average: exits may be cutting winners too early or letting losers run; review exit signal weights and hold period.

## 6) Full trade list (last 150 with scores)

| # | Symbol | Timestamp | Entry score | Exit score | PnL USD | Close reason |
|---|--------|-----------|-------------|------------|--------|--------------|
| 1 | XOM | 2026-02-24T20:59:52 | 2.65 | 0.00 | -0.05 | signal_decay(0.81) |
| 2 | WFC | 2026-02-24T20:59:50 | 3.65 | 0.00 | 0.00 | signal_decay(0.53)+f |
| 3 | XLI | 2026-02-24T20:59:47 | 3.67 | 0.00 | -0.03 | signal_decay(0.59)+f |
| 4 | V | 2026-02-24T20:59:44 | 3.69 | 0.00 | 0.05 | signal_decay(0.77)+f |
| 5 | BAC | 2026-02-24T20:59:15 | 3.69 | 0.00 | 0.06 | signal_decay(0.57)+f |
| 6 | MS | 2026-02-24T20:59:12 | 3.71 | 0.00 | 0.04 | signal_decay(0.61)+f |
| 7 | GOOGL | 2026-02-24T20:59:09 | 3.72 | 0.00 | -0.21 | signal_decay(0.66)+f |
| 8 | CVX | 2026-02-24T20:59:06 | 2.75 | 0.00 | 0.01 | signal_decay(0.85) |
| 9 | C | 2026-02-24T20:59:01 | 3.84 | 0.00 | 0.14 | signal_decay(0.57)+f |
| 10 | JPM | 2026-02-24T20:58:58 | 3.85 | 0.00 | 0.17 | signal_decay(0.58)+f |
| 11 | NIO | 2026-02-24T20:58:56 | 3.99 | 0.00 | -1.34 | signal_decay(0.90)+f |
| 12 | DIA | 2026-02-24T20:58:20 | 3.06 | 0.00 | 0.21 | signal_decay(0.69) |
| 13 | IWM | 2026-02-24T20:58:15 | 3.07 | 0.00 | 0.13 | signal_decay(0.63) |
| 14 | XLK | 2026-02-24T20:57:06 | 3.98 | 0.00 | -0.02 | signal_decay(0.88)+f |
| 15 | NVDA | 2026-02-24T20:57:01 | 4.03 | 0.00 | -0.10 | signal_decay(0.88)+f |
| 16 | INTC | 2026-02-24T20:56:58 | 4.07 | 0.00 | -0.14 | signal_decay(0.88)+f |
| 17 | COP | 2026-02-24T20:56:53 | 3.29 | 0.00 | 0.42 | signal_decay(0.85) |
| 18 | TSLA | 2026-02-24T20:55:44 | 4.17 | 0.00 | 0.94 | signal_decay(0.92)+f |
| 19 | RIVN | 2026-02-24T20:54:39 | 4.20 | 0.00 | 0.00 | signal_decay(0.85) |
| 20 | HOOD | 2026-02-24T20:53:28 | 4.43 | 0.00 | -0.15 | signal_decay(0.82) |
| 21 | BA | 2026-02-24T20:53:26 | 3.36 | 0.00 | -0.26 | signal_decay(0.92) |
| 22 | XLP | 2026-02-24T20:52:13 | 3.31 | 0.00 | -0.06 | signal_decay(0.91)+f |
| 23 | UNH | 2026-02-24T20:52:10 | 3.33 | 0.00 | -0.15 | signal_decay(0.90)+f |
| 24 | MA | 2026-02-24T20:52:07 | 3.34 | 0.00 | 0.30 | signal_decay(0.91)+f |
| 25 | XLV | 2026-02-24T20:52:03 | 3.35 | 0.00 | -0.11 | signal_decay(0.91)+f |
| 26 | XLF | 2026-02-24T20:52:00 | 3.37 | 0.00 | 0.18 | signal_decay(0.92)+f |
| 27 | WFC | 2026-02-24T20:51:57 | 3.39 | 0.00 | 0.02 | signal_decay(0.92)+f |
| 28 | NFLX | 2026-02-24T20:51:55 | 3.37 | 0.00 | 0.20 | signal_decay(0.90)+f |
| 29 | XLI | 2026-02-24T20:51:08 | 3.40 | 0.00 | 0.08 | signal_decay(0.89)+f |
| 30 | BAC | 2026-02-24T20:51:05 | 3.41 | 0.00 | -0.18 | signal_decay(0.89)+f |
| 31 | MS | 2026-02-24T20:51:00 | 3.43 | 0.00 | 0.21 | signal_decay(0.89)+f |
| 32 | F | 2026-02-24T20:50:57 | 3.51 | 0.00 | -1.11 | signal_decay(0.88)+f |
| 33 | GOOGL | 2026-02-24T20:50:51 | 3.51 | 0.00 | 0.28 | signal_decay(0.61)+f |
| 34 | C | 2026-02-24T20:50:48 | 3.52 | 0.00 | 0.38 | signal_decay(0.90)+f |
| 35 | JPM | 2026-02-24T20:50:42 | 3.52 | 0.00 | 0.07 | signal_decay(0.90)+f |
| 36 | GM | 2026-02-24T20:50:37 | 3.64 | 0.00 | -1.02 | signal_decay(0.90)+f |
| 37 | XLK | 2026-02-24T20:50:32 | 3.66 | 0.00 | 0.13 | signal_decay(0.90)+f |
| 38 | XLE | 2026-02-24T20:50:26 | 3.75 | 0.00 | 0.08 | signal_decay(0.91)+f |
| 39 | RIVN | 2026-02-24T20:50:22 | 3.84 | 0.00 | -0.20 | signal_decay(0.90)+f |
| 40 | HOOD | 2026-02-24T20:50:17 | 4.00 | 0.00 | 1.12 | signal_decay(0.92)+f |
| 41 | NIO | 2026-02-24T20:50:10 | 4.00 | 0.00 | -0.37 | signal_decay(0.92)+f |
| 42 | LCID | 2026-02-24T20:50:03 | 4.02 | 0.00 | 0.00 | signal_decay(0.92)+f |
| 43 | META | 2026-02-24T20:49:57 | 2.68 | 0.00 | 0.43 | signal_decay(0.86) |
| 44 | NFLX | 2026-02-24T20:48:15 | 3.08 | 0.00 | 0.40 | signal_decay(0.69)+f |
| 45 | NVDA | 2026-02-24T20:48:13 | 3.12 | 0.00 | 0.58 | signal_decay(0.66)+f |
| 46 | INTC | 2026-02-24T20:48:10 | 3.47 | 0.00 | 0.24 | signal_decay(0.86)+f |
| 47 | AMD | 2026-02-24T20:48:05 | 3.49 | 0.00 | -0.08 | signal_decay(0.66)+f |
| 48 | TSLA | 2026-02-24T20:48:02 | 3.53 | 0.00 | 0.51 | signal_decay(0.76) |
| 49 | SLB | 2026-02-24T20:46:53 | 2.56 | 0.00 | -0.09 | signal_decay(0.84)+f |
| 50 | COP | 2026-02-24T20:46:49 | 2.65 | 0.00 | -0.26 | signal_decay(0.86)+f |
| 51 | COIN | 2026-02-24T20:41:33 | 3.27 | 0.00 | -0.58 | signal_decay(0.92) |
| 52 | COP | 2026-02-24T20:41:26 | 3.32 | 0.00 | 0.02 | signal_decay(0.92) |
| 53 | LOW | 2026-02-24T20:41:23 | 2.97 | 0.00 | -0.08 | signal_decay(0.57) |
| 54 | MA | 2026-02-24T20:41:10 | 2.91 | 0.00 | -0.20 | signal_decay(0.81) |
| 55 | BA | 2026-02-24T20:41:08 | 2.91 | 0.00 | -0.11 | signal_decay(0.73) |
| 56 | WFC | 2026-02-24T20:41:05 | 2.96 | 0.00 | -0.30 | signal_decay(0.90) |
| 57 | PLTR | 2026-02-24T20:41:01 | 3.48 | 0.00 | -0.05 | signal_decay(0.93) |
| 58 | SOFI | 2026-02-24T20:40:59 | 3.52 | 0.00 | 0.37 | signal_decay(0.93) |
| 59 | XOM | 2026-02-24T20:40:30 | 2.99 | 0.00 | -0.01 | signal_decay(0.73) |
| 60 | HD | 2026-02-24T20:40:24 | 3.00 | 0.00 | -0.13 | signal_decay(0.58) |
| 61 | JNJ | 2026-02-24T20:40:19 | 3.02 | 0.00 | -0.02 | signal_decay(0.66) |
| 62 | WMT | 2026-02-24T20:39:06 | 3.04 | 0.00 | -0.16 | signal_decay(0.70)+f |
| 63 | TGT | 2026-02-24T20:39:03 | 3.06 | 0.00 | -0.14 | signal_decay(0.58) |
| 64 | F | 2026-02-24T20:39:01 | 3.06 | 0.00 | -0.24 | signal_decay(0.66) |
| 65 | CVX | 2026-02-24T20:38:55 | 3.08 | 0.00 | 0.03 | signal_decay(0.75)+f |
| 66 | PFE | 2026-02-24T20:38:53 | 3.13 | 0.00 | -0.10 | signal_decay(0.72)+f |
| 67 | UNH | 2026-02-24T20:38:50 | 3.21 | 0.00 | 0.13 | signal_decay(0.71)+f |
| 68 | MRNA | 2026-02-24T20:38:44 | 3.62 | 0.00 | -0.35 | signal_decay(0.78)+f |
| 69 | SLB | 2026-02-24T20:37:39 | 3.22 | 0.00 | -0.12 | signal_decay(0.80)+f |
| 70 | RIVN | 2026-02-24T20:37:34 | 3.34 | 0.00 | 0.00 | signal_decay(0.64) |
| 71 | LCID | 2026-02-24T20:37:28 | 3.53 | 0.00 | -0.17 | signal_decay(0.80) |
| 72 | GM | 2026-02-24T20:37:16 | 3.03 | 0.00 | -0.02 | signal_decay(0.66)+f |
| 73 | HOOD | 2026-02-24T20:33:10 | 3.17 | 0.00 | -0.16 | signal_decay(0.79) |
| 74 | NIO | 2026-02-24T20:33:07 | 3.48 | 0.00 | -0.08 | signal_decay(0.80) |
| 75 | WMT | 2026-02-24T20:33:03 | 3.36 | 0.00 | -0.06 | signal_decay(0.40) |
| 76 | RIVN | 2026-02-24T20:32:32 | 4.15 | 0.00 | 1.28 | signal_decay(0.56) |
| 77 | CVX | 2026-02-24T20:31:01 | 3.23 | 0.00 | -0.04 | signal_decay(0.60) |
| 78 | F | 2026-02-24T20:30:58 | 3.29 | 0.00 | -0.24 | signal_decay(0.80)+f |
| 79 | TGT | 2026-02-24T20:30:55 | 3.29 | 0.00 | -0.03 | signal_decay(0.44)+f |
| 80 | XOM | 2026-02-24T20:30:52 | 3.35 | 0.00 | -0.04 | signal_decay(0.72)+f |
| 81 | SOFI | 2026-02-24T20:30:49 | 2.76 | 0.00 | -0.91 | signal_decay(0.87) |
| 82 | PLTR | 2026-02-24T20:30:46 | 2.72 | 0.00 | 0.17 | signal_decay(0.87) |
| 83 | AMZN | 2026-02-24T20:29:52 | 3.42 | 0.00 | -0.12 | signal_decay(0.46)+f |
| 84 | GM | 2026-02-24T20:29:46 | 3.45 | 0.00 | 0.00 | signal_decay(0.59)+f |
| 85 | MA | 2026-02-24T20:29:40 | 3.14 | 0.00 | 0.10 | signal_decay(0.44) |
| 86 | BAC | 2026-02-24T20:29:38 | 3.23 | 0.00 | 0.24 | signal_decay(0.53) |
| 87 | JPM | 2026-02-24T20:29:32 | 3.36 | 0.00 | 0.12 | signal_decay(0.77)+f |
| 88 | MSFT | 2026-02-24T20:28:28 | 3.59 | 0.00 | 0.00 | signal_decay(0.67) |
| 89 | DIA | 2026-02-24T20:28:25 | 3.63 | 0.00 | -0.10 | signal_decay(0.81) |
| 90 | AAPL | 2026-02-24T20:28:22 | 3.64 | 0.00 | 0.02 | signal_decay(0.67) |
| 91 | IWM | 2026-02-24T20:28:16 | 3.64 | 0.00 | -0.04 | signal_decay(0.81) |
| 92 | XLV | 2026-02-24T20:28:14 | 3.67 | 0.00 | -0.12 | signal_decay(0.73) |
| 93 | XLF | 2026-02-24T20:27:09 | 3.70 | 0.00 | -0.20 | signal_decay(0.79) |
| 94 | NFLX | 2026-02-24T20:27:03 | 3.71 | 0.00 | -0.15 | signal_decay(0.89) |
| 95 | XLI | 2026-02-24T20:27:00 | 3.72 | 0.00 | -0.09 | signal_decay(0.79) |
| 96 | GOOGL | 2026-02-24T20:26:55 | 3.90 | 0.00 | -0.22 | signal_decay(0.74) |
| 97 | NIO | 2026-02-24T20:26:49 | 3.90 | 0.00 | -1.68 | signal_decay(0.90) |
| 98 | XLK | 2026-02-24T20:26:44 | 4.06 | 0.00 | -0.08 | signal_decay(0.65) |
| 99 | XLP | 2026-02-24T20:26:41 | 3.11 | 0.00 | -0.03 | signal_decay(0.92)+f |
| 100 | NVDA | 2026-02-24T20:25:30 | 4.15 | 0.00 | -0.02 | signal_decay(0.86) |
| 101 | INTC | 2026-02-24T20:25:22 | 4.16 | 0.00 | 0.30 | signal_decay(0.88) |
| 102 | XLE | 2026-02-24T20:25:17 | 4.17 | 0.00 | 0.18 | signal_decay(0.87) |
| 103 | AMD | 2026-02-24T20:25:11 | 4.21 | 0.00 | -1.38 | signal_decay(0.88) |
| 104 | TSLA | 2026-02-24T20:25:06 | 4.25 | 0.00 | -0.17 | signal_decay(0.89) |
| 105 | LCID | 2026-02-24T20:23:59 | 4.38 | 0.00 | -0.08 | signal_decay(0.92) |
| 106 | HOOD | 2026-02-24T20:23:56 | 4.42 | 0.00 | -0.30 | signal_decay(0.92) |
| 107 | HD | 2026-02-24T20:23:50 | 3.17 | 0.00 | -0.46 | signal_decay(0.41) |
| 108 | LOW | 2026-02-24T20:23:45 | 3.19 | 0.00 | -0.17 | signal_decay(0.39) |
| 109 | JNJ | 2026-02-24T20:23:13 | 3.25 | 0.00 | -0.13 | signal_decay(0.60)+f |
| 110 | UNH | 2026-02-24T20:23:11 | 3.44 | 0.00 | -0.11 | signal_decay(0.92)+f |
| 111 | CVX | 2026-02-24T20:22:41 | 3.16 | 0.00 | -0.04 | signal_decay(0.87) |
| 112 | WFC | 2026-02-24T20:22:38 | 3.20 | 0.00 | -0.02 | signal_decay(0.73)+f |
| 113 | V | 2026-02-24T20:22:38 | 3.23 | 0.00 | 0.25 | signal_decay(0.73)+f |
| 114 | COIN | 2026-02-24T20:22:33 | 3.53 | 0.00 | -0.46 | signal_decay(0.81)+f |
| 115 | MS | 2026-02-24T20:22:32 | 3.25 | 0.00 | 0.06 | signal_decay(0.76)+f |
| 116 | C | 2026-02-24T20:22:25 | 3.36 | 0.00 | 0.02 | signal_decay(0.74)+f |
| 117 | COP | 2026-02-24T20:22:17 | 3.39 | 0.00 | -0.13 | signal_decay(0.88) |
| 118 | WMT | 2026-02-24T20:21:10 | 3.28 | 0.00 | 0.00 | signal_decay(0.57)+f |
| 119 | TGT | 2026-02-24T20:21:05 | 3.31 | 0.00 | -0.07 | signal_decay(0.57)+f |
| 120 | NFLX | 2026-02-24T20:20:59 | 3.42 | 0.00 | -0.21 | signal_decay(0.69)+f |
| 121 | GOOGL | 2026-02-24T20:20:53 | 3.51 | 0.00 | -0.12 | signal_decay(0.59)+f |
| 122 | XLF | 2026-02-24T20:20:51 | 3.52 | 0.00 | -0.18 | signal_decay(0.70)+f |
| 123 | AMZN | 2026-02-24T20:20:48 | 3.00 | 0.00 | 0.22 | signal_decay(0.66)+f |
| 124 | AAPL | 2026-02-24T20:20:45 | 3.21 | 0.00 | 0.60 | signal_decay(0.57)+f |
| 125 | XLE | 2026-02-24T20:20:42 | 3.22 | 0.00 | -0.16 | signal_decay(0.91)+f |
| 126 | INTC | 2026-02-24T20:20:39 | 3.31 | 0.00 | 0.03 | signal_decay(0.85)+f |
| 127 | NVDA | 2026-02-24T20:19:36 | 3.73 | 0.00 | -0.16 | signal_decay(0.89) |
| 128 | AMD | 2026-02-24T20:19:33 | 3.79 | 0.00 | -0.17 | signal_decay(0.89) |
| 129 | TSLA | 2026-02-24T20:19:28 | 3.84 | 0.00 | -0.33 | signal_decay(0.89) |
| 130 | MRNA | 2026-02-24T20:19:25 | 3.94 | 0.00 | 0.18 | signal_decay(0.90) |
| 131 | XOM | 2026-02-24T20:19:16 | 3.53 | 0.00 | 0.39 | signal_decay(0.84) |
| 132 | F | 2026-02-24T20:17:39 | 3.61 | 0.00 | -0.44 | signal_decay(0.56) |
| 133 | PFE | 2026-02-24T20:17:33 | 3.34 | 0.00 | -0.26 | signal_decay(0.89)+f |
| 134 | MSFT | 2026-02-24T20:17:28 | 3.17 | 0.00 | -0.09 | signal_decay(0.90) |
| 135 | XLK | 2026-02-24T20:17:25 | 3.22 | 0.00 | 0.23 | signal_decay(0.63) |
| 136 | LCID | 2026-02-24T20:17:22 | 2.79 | 0.00 | -0.50 | signal_decay(0.89) |
| 137 | BA | 2026-02-24T20:16:02 | 3.42 | 0.00 | -0.09 | signal_decay(0.92)+f |
| 138 | XLP | 2026-02-24T20:15:59 | 3.42 | 0.00 | -0.04 | signal_decay(0.85)+f |
| 139 | TSLA | 2026-02-24T20:15:56 | 3.77 | 0.00 | 0.72 | signal_decay(0.92) |
| 140 | NVDA | 2026-02-24T20:15:53 | 3.66 | 0.00 | 0.20 | signal_decay(0.92) |
| 141 | GOOGL | 2026-02-24T20:15:51 | 3.48 | 0.00 | -0.16 | signal_decay(0.92) |
| 142 | COP | 2026-02-24T20:15:47 | 3.54 | 0.00 | 0.14 | signal_decay(0.90) |
| 143 | AMD | 2026-02-24T20:15:45 | 3.73 | 0.00 | -0.02 | signal_decay(0.92) |
| 144 | DIA | 2026-02-24T20:14:59 | 3.43 | 0.00 | -0.05 | signal_decay(0.90)+f |
| 145 | MA | 2026-02-24T20:14:54 | 3.44 | 0.00 | -0.23 | signal_decay(0.90)+f |
| 146 | IWM | 2026-02-24T20:14:51 | 3.45 | 0.00 | -0.06 | signal_decay(0.89)+f |
| 147 | XLV | 2026-02-24T20:14:46 | 3.46 | 0.00 | 0.02 | signal_decay(0.89)+f |
| 148 | SLB | 2026-02-24T20:14:40 | 3.47 | 0.00 | 0.14 | signal_decay(0.88)+f |
| 149 | TGT | 2026-02-24T20:14:37 | 3.22 | 0.00 | -0.12 | signal_decay(0.90)+f |
| 150 | WFC | 2026-02-24T20:13:29 | 3.50 | 0.00 | -0.03 | signal_decay(0.87) |