# 30-Day Backtest After Block 3F — First True Signal Edge Run

**Run date:** 2026-02-15 15:31:19 UTC  
**Environment:** Production droplet (paper trading replay).  
**Code:** Block 3F — First full signal edge backtest (no logic changes; run, analyze, report).

---

## Window

2026-01-15 → 2026-02-14 (30 days)

---

## What Block 3F is

Block 3F is the **first 30-day backtest** intended to produce **real per-signal, per-regime edge tables** using attribution and blocked-trade data that was logged **with** raw signals (from Block 3E). No trading logic changes; only run, signal edge analysis, and reporting.

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

## Signal data in this run

The backtest **replays from** the droplet’s `logs/attribution.jsonl` and `state/blocked_trades.jsonl`. Those files in the 30d window were written **before** the bot ran with Block 3E (or the window is entirely pre–Block 3E). Therefore:

- **Raw signals** (trend_signal, momentum_signal, volatility_signal, sector_signal, reversal_signal, breakout_signal, mean_reversion_signal) still appear as **"missing"** in the Signal Edge Analysis report.
- **regime_signal** (from market_regime) is present and bucketed (e.g. near_zero / MIXED).
- **entry_score** is present (positive / near_zero).

So this run is the **first signal-edge backtest by label**, but it does **not** yet have full per-signal data. The first backtest with **all** entries/blocks logged with raw signals will be when either:

1. The bot has run with Block 3E for a full 30 days in the window and we re-run the backtest, or  
2. The backtest is extended to **inject signals at replay time** (compute market_context at each entry/block timestamp and merge signal fields into the written records).

---

## Artifacts in this dir

- **backtest_summary.json** — counts, P&L, exit/block reason counts.  
- **backtest_pnl_curve.json** — cumulative P&L by trade index.  
- **SIGNAL_EDGE_ANALYSIS_REPORT.md** — per-signal and per-regime buckets; most signals show "missing" until source data includes them.  
- **BLOCK_3F_MULTI_AI_REPORT.md** — multi-role review and recommendations.  
- **BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md** (this file).

`backtest_trades.jsonl`, `backtest_exits.jsonl`, and `backtest_blocks.jsonl` are generated on the droplet and are gitignored.

---

## For the reviewer

Block 3F establishes the **run + analyze + report** workflow for signal edge. Once attribution and blocked_trades are logged with Block 3E over the backtest window (or replay injects signals), the same pipeline will produce real answers to: which signals have positive edge, in which regimes, and where to adjust weights.
