# 30-Day Backtest After Block 3E — Signal Attribution Logging

**Run date:** 2026-02-15 01:00:31 UTC  
**Environment:** Production droplet (paper trading replay).  
**Code:** Block 3E — Signal attribution logging (entry context, blocked trades).

---

## Window

2026-01-15 → 2026-02-14 (30 days)

---

## What changed

Block 3E adds **signal attribution logging** so Signal Edge Analysis can compute real per-signal, per-regime edge:

- **Entry attribution:** Raw signals (trend_signal, momentum_signal, volatility_signal, regime_signal, sector_signal, reversal_signal, breakout_signal, mean_reversion_signal) are now written into the attribution context when trades are logged at entry.
- **Blocked trades:** `log_blocked_trade` accepts `market_context` and merges the same signal fields into blocked_trades.jsonl.
- **Backtest loader:** Preserves signal fields from attribution context and blocked records when replaying.
- **No trading logic changes:** Entry/exit decisions, UW, survivorship, wheel, and constraints unchanged.

---

## Aggregate results

| Metric | Value |
|--------|--------|
| Trades (executed) | 2,243 |
| Exits (recorded) | 2,815 |
| Blocks (blocked attempts) | 2,000 |
| Total P&L (USD) | -$162.15 |
| Winning trades | 340 |
| Losing trades | 650 |
| Win rate (%) | 15.16 |

---

## Signal edge report

The backtest used **historical attribution** logged before Block 3E. Raw signals (trend, momentum, volatility, sector, reversal, breakout, mean_reversion) appear as "missing" in this run because those records were created with prior code.

- **Going forward:** As the bot runs with Block 3E, new entry and blocked logs will include signal fields.
- **Next backtest:** After accumulating new attribution with signals, re-run the 30-day backtest and Signal Edge Analysis to get real per-signal, per-regime edge tables.
- **Regime signal:** regime_signal (derived from market_regime) is available and bucketed as "near_zero" (MIXED regime).

---

## Artifacts on GitHub

- **Path:** `backtests/30d_after_signal_engine_block3e_20260215_010031/`
- **Files:** backtest_summary.json, backtest_pnl_curve.json, SIGNAL_EDGE_ANALYSIS_REPORT.md, BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md.
- **Droplet only (gitignored):** backtest_trades.jsonl, backtest_exits.jsonl, backtest_blocks.jsonl.

---

## Context for reviewer

Block 3E establishes the plumbing for per-signal edge analysis. Once new trades and blocks are logged with this code, the Signal Edge Analysis report will answer: Which signals show positive edge? In which regimes? Which look harmful? Where should we tune weights?
