# 30-Day Backtest After Block 3G — Replay-Time Signal Injection

**Run date:** 2026-02-15 15:56:17 UTC  
**Environment:** Production droplet (paper trading replay).  
**Code:** Block 3G — Replay-time signal injection (no trading logic changes).

---

## Window

2026-01-15 → 2026-02-14 (30 days)

---

## What Block 3G is

Block 3G adds **replay-time signal injection**: during backtest replay, the script computes raw signals (trend, momentum, volatility, regime, sector, reversal, breakout, mean_reversion) at each ENTRY and BLOCK timestamp using historical bars and the same `raw_signal_engine` used in live scoring, then injects them into the attribution payload. This produces the first complete per-signal, per-regime edge dataset without waiting 30 days of live Block 3E data.

**Note:** This specific run (155617) was executed on the droplet **before** the Block 3G injection code was merged. So this dir still shows "missing" for raw signals in the Signal Edge Analysis report. A **subsequent** 3g run (same prefix, new timestamp) with the merged code will have all signal fields populated in `backtest_trades.jsonl` and `backtest_blocks.jsonl`.

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

## Artifacts in this dir

- **backtest_summary.json** — counts, P&L, exit/block reason counts.  
- **backtest_pnl_curve.json** — cumulative P&L by trade index.  
- **SIGNAL_EDGE_ANALYSIS_REPORT.md** — per-signal and per-regime buckets (raw signals "missing" in this run; see note above).  
- **BLOCK_3G_MULTI_AI_REPORT.md** — multi-role review and recommendations.  
- **BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md** (this file).

`backtest_trades.jsonl`, `backtest_exits.jsonl`, and `backtest_blocks.jsonl` are generated on the droplet and are gitignored.

---

## For the reviewer

Block 3G establishes replay-time signal injection. Once a 3g backtest runs **with** the merged code, the output will have all signal fields populated and Signal Edge Analysis will answer: which signals show positive edge, in which regimes, and where to adjust weights for Block 3H.
