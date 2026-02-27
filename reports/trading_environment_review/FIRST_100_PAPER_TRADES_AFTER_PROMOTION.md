# First 100 PAPER trades closed after exit promotion

**Promotion timestamp:** `2026-02-24T03:16:57Z`  
(Exit strategy promotion: grid-approved exit params → runtime config; PAPER trading uses new exits.)

**Source:** `reports/trading_environment_review/TRADING_ENVIRONMENT_REVIEW_2026-02-24.json` (closed equity trades from droplet `logs/attribution.jsonl` + `logs/exit_attribution.jsonl`).

**Filter:** Close timestamp ≥ promotion timestamp; sorted by close time ascending (earliest first).  
**Total closed after promotion in report:** 150  
**Shown below:** First 100.

---

| # | Symbol | Close time (UTC) | PnL USD | Close reason |
|---|--------|------------------|--------|--------------|
| 1 | XLV | 2026-02-24T15:11:24 | -0.66 | signal_decay(0.70)+flow_reversal |
| 2 | XLP | 2026-02-24T15:11:27 | -0.12 | signal_decay(0.47) |
| 3 | DIA | 2026-02-24T15:11:32 | -0.24 | signal_decay(0.71) |
| 4 | GM | 2026-02-24T15:11:44 | -0.72 | signal_decay(0.88) |
| 5 | LCID | 2026-02-24T15:12:37 | -0.52 | signal_decay(0.76) |
| 6 | RIVN | 2026-02-24T15:12:42 | -0.23 | signal_decay(0.76) |
| 7 | TSLA | 2026-02-24T15:13:47 | -1.12 | signal_decay(0.80) |
| 8 | AMD | 2026-02-24T15:13:53 | -0.96 | signal_decay(0.80) |
| 9 | INTC | 2026-02-24T15:13:56 | -0.21 | signal_decay(0.80) |
| 10 | NVDA | 2026-02-24T15:13:58 | -0.86 | signal_decay(0.80) |
| 11 | GM | 2026-02-24T15:14:01 | 0.32 | signal_decay(0.71) |
| 12 | C | 2026-02-24T15:15:10 | 0.54 | signal_decay(0.75) |
| 13 | F | 2026-02-24T15:15:13 | -0.25 | signal_decay(0.67) |
| 14 | MS | 2026-02-24T15:15:21 | -0.51 | signal_decay(0.75) |
| 15 | BAC | 2026-02-24T15:15:26 | 0.20 | signal_decay(0.75) |
| 16 | JNJ | 2026-02-24T15:16:47 | -1.80 | signal_decay(0.52)+flow_reversal |
| 17 | NIO | 2026-02-24T15:16:49 | -0.62 | signal_decay(0.92) |
| 18 | XLI | 2026-02-24T15:16:55 | -0.06 | signal_decay(0.70) |
| 19 | WFC | 2026-02-24T15:16:58 | 0.22 | signal_decay(0.70) |
| 20 | XLF | 2026-02-24T15:17:01 | 0.40 | signal_decay(0.70) |
| 21 | MA | 2026-02-24T15:17:04 | 0.15 | signal_decay(0.69) |
| 22 | XLV | 2026-02-24T15:18:09 | 0.04 | signal_decay(0.66) |
| 23 | IWM | 2026-02-24T15:18:15 | 0.03 | signal_decay(0.80) |
| 24 | DIA | 2026-02-24T15:18:20 | -0.09 | signal_decay(0.80) |
| 25 | XLP | 2026-02-24T15:18:26 | -0.51 | signal_decay(0.66) |
| 26 | MSFT | 2026-02-24T15:18:31 | 0.22 | signal_decay(0.79) |
| 27 | TGT | 2026-02-24T15:19:18 | 0.21 | signal_decay(0.72) |
| 28 | WMT | 2026-02-24T15:19:23 | 0.13 | signal_decay(0.66) |
| 29 | HD | 2026-02-24T15:19:26 | 0.02 | signal_decay(0.70) |
| 30 | AAPL | 2026-02-24T15:20:51 | 0.75 | signal_decay(0.73) |
| 31 | JPM | 2026-02-24T15:20:57 | 2.50 | signal_decay(0.72) |
| 32 | QQQ | 2026-02-24T15:21:31 | 1.01 | signal_decay(0.72) |
| 33 | TSLA | 2026-02-24T15:22:01 | 0.99 | signal_decay(0.76)+flow_reversal |
| 34 | AMD | 2026-02-24T15:22:03 | 1.31 | signal_decay(0.75) |
| 35 | INTC | 2026-02-24T15:22:08 | 3.06 | signal_decay(0.75) |
| 36 | XLE | 2026-02-24T15:23:20 | -1.44 | signal_decay(0.63) |
| 37 | XLK | 2026-02-24T15:23:26 | -0.38 | signal_decay(0.62) |
| 38 | NVDA | 2026-02-24T15:23:31 | -0.14 | signal_decay(0.69)+flow_reversal |
| 39 | JPM | 2026-02-24T15:23:37 | -0.34 | signal_decay(0.54)+flow_reversal |
| 40 | C | 2026-02-24T15:23:40 | -0.91 | signal_decay(0.69)+flow_reversal |
| 41 | BAC | 2026-02-24T15:23:42 | -0.70 | signal_decay(0.53)+flow_reversal |
| 42 | XLI | 2026-02-24T15:23:48 | 0.03 | signal_decay(0.62)+flow_reversal |
| 43 | WFC | 2026-02-24T15:23:51 | 0.07 | signal_decay(0.69)+flow_reversal |
| 44 | XLF | 2026-02-24T15:23:56 | 0.03 | signal_decay(0.36)+flow_reversal |
| 45 | XLV | 2026-02-24T15:24:02 | -0.16 | signal_decay(0.57)+flow_reversal |
| 46 | IWM | 2026-02-24T15:25:10 | 0.42 | signal_decay(0.71)+flow_reversal |
| 47 | DIA | 2026-02-24T15:25:19 | 0.28 | signal_decay(0.71)+flow_reversal |
| 48 | XLP | 2026-02-24T15:25:21 | 0.07 | signal_decay(0.71)+flow_reversal |
| 49 | V | 2026-02-24T15:25:27 | 0.00 | signal_decay(0.74)+flow_reversal |
| 50 | MSFT | 2026-02-24T15:25:32 | -0.64 | signal_decay(0.72)+flow_reversal |
| 51 | F | 2026-02-24T15:25:48 | -0.12 | signal_decay(0.91) |
| 52 | RIVN | 2026-02-24T15:26:03 | -0.75 | signal_decay(0.92) |
| 53 | TGT | 2026-02-24T15:27:45 | -0.33 | signal_decay(0.92) |
| 54 | WMT | 2026-02-24T15:27:50 | -0.04 | signal_decay(0.92) |
| 55 | XLE | 2026-02-24T15:27:53 | 0.11 | signal_decay(0.74)+flow_reversal |
| 56 | XLK | 2026-02-24T15:27:56 | -0.13 | signal_decay(0.73)+flow_reversal |
| 57 | INTC | 2026-02-24T15:32:09 | -1.04 | signal_decay(0.75) |
| 58 | NFLX | 2026-02-24T15:32:11 | -0.90 | signal_decay(0.87)+flow_reversal |
| 59 | SLB | 2026-02-24T15:33:32 | -0.39 | signal_decay(0.68) |
| 60 | CVX | 2026-02-24T15:33:35 | -0.15 | signal_decay(0.62)+flow_reversal |
| 61 | XOM | 2026-02-24T15:33:41 | -0.32 | signal_decay(0.60)+flow_reversal |
| 62 | COP | 2026-02-24T15:33:43 | -1.12 | signal_decay(0.71) |
| 63 | JNJ | 2026-02-24T15:33:46 | -0.29 | signal_decay(0.65) |
| 64 | XLE | 2026-02-24T15:33:52 | 0.24 | signal_decay(0.79) |
| 65 | WFC | 2026-02-24T15:34:57 | -0.07 | signal_decay(0.72) |
| 66 | XLV | 2026-02-24T15:35:00 | 0.09 | signal_decay(0.81) |
| 67 | XLP | 2026-02-24T15:35:06 | -0.02 | signal_decay(0.72) |
| 68 | TGT | 2026-02-24T15:35:12 | -0.24 | signal_decay(0.80) |
| 69 | WMT | 2026-02-24T15:36:03 | 0.02 | signal_decay(0.76) |
| 70 | SOFI | 2026-02-24T15:36:21 | -0.14 | signal_decay(0.86)+flow_reversal |
| 71 | GM | 2026-02-24T15:36:23 | -0.22 | signal_decay(0.91) |
| 72 | PFE | 2026-02-24T15:36:26 | 0.04 | signal_decay(0.92)+flow_reversal |
| 73 | RIVN | 2026-02-24T15:36:37 | 0.60 | signal_decay(0.76) |
| 74 | LCID | 2026-02-24T15:36:50 | -2.44 | signal_decay(0.73) |
| 75 | MA | 2026-02-24T15:36:53 | -0.22 | signal_decay(0.86) |
| 76 | BA | 2026-02-24T15:38:17 | 1.67 | signal_decay(0.52) |
| 77 | NIO | 2026-02-24T15:38:22 | 2.46 | signal_decay(0.64)+flow_reversal |
| 78 | HD | 2026-02-24T15:38:25 | -1.01 | signal_decay(0.72) |
| 79 | LOW | 2026-02-24T15:38:28 | -0.15 | signal_decay(0.89) |
| 80 | DIA | 2026-02-24T15:38:33 | -0.25 | signal_decay(0.87) |
| 81 | XLK | 2026-02-24T15:38:36 | -0.12 | signal_decay(0.78) |
| 82 | MA | 2026-02-24T15:38:41 | -0.51 | signal_decay(0.76) |
| 83 | HOOD | 2026-02-24T15:39:52 | -1.31 | signal_decay(0.91)+flow_reversal |
| 84 | MSFT | 2026-02-24T15:39:54 | -0.17 | signal_decay(0.79)+flow_reversal |
| 85 | XLV | 2026-02-24T15:41:03 | 0.00 | signal_decay(0.90)+flow_reversal |
| 86 | PFE | 2026-02-24T15:41:09 | -0.19 | signal_decay(0.89) |
| 87 | TGT | 2026-02-24T15:41:14 | -0.43 | signal_decay(0.64)+flow_reversal |
| 88 | WMT | 2026-02-24T15:41:17 | 0.00 | signal_decay(0.55) |
| 89 | AAPL | 2026-02-24T15:41:57 | 0.11 | signal_decay(0.89) |
| 90 | AMD | 2026-02-24T15:41:59 | 2.44 | trail_stop |
| 91 | GOOGL | 2026-02-24T15:42:02 | -0.88 | signal_decay(0.89) |
| 92 | MRNA | 2026-02-24T15:42:05 | -0.75 | signal_decay(0.70) |
| 93 | NVDA | 2026-02-24T15:42:08 | 0.09 | signal_decay(0.91) |
| 94 | UNH | 2026-02-24T15:42:11 | -0.29 | signal_decay(0.56) |
| 95 | SOFI | 2026-02-24T15:42:14 | -0.05 | signal_decay(0.92) |
| 96 | GM | 2026-02-24T15:42:16 | -0.02 | signal_decay(0.73) |
| 97 | COP | 2026-02-24T15:42:20 | -0.13 | signal_decay(0.82)+flow_reversal |
| 98 | RIVN | 2026-02-24T15:42:34 | -0.04 | signal_decay(0.91)+flow_reversal |
| 99 | XLI | 2026-02-24T15:43:41 | -0.01 | signal_decay(0.73)+flow_reversal |
| 100 | XLF | 2026-02-24T15:43:48 | 0.05 | signal_decay(0.76)+flow_reversal |

---

**Summary (first 100):**  
- **Wins (PnL > 0):** 35  
- **Losses (PnL < 0):** 62  
- **Flat (PnL = 0):** 3  
- **Close reasons:** Mostly `signal_decay(...)` with many `+flow_reversal`; one `trail_stop` (AMD #90).
