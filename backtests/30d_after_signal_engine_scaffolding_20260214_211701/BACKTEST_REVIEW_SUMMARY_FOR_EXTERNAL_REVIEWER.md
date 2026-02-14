# 30-Day Backtest After Block 3A — Raw Signal Engine Scaffolding

**Run date:** 2026-02-14 21:17:01 UTC  
**Environment:** Production droplet (paper trading replay).  
**Code:** Block 3A — Raw Signal Engine Scaffolding (trend, momentum, volatility, regime, sector, reversal, breakout, mean-reversion placeholders).

---

## Window

2026-01-15 → 2026-02-14 (30 days)

---

## Purpose

This block creates the raw signal engine scaffolding without altering behavior. Placeholder functions return 0.0; market_context is extended with raw signal keys (trend_signal, momentum_signal, volatility_signal, regime_signal, sector_signal, reversal_signal, breakout_signal, mean_reversion_signal). The system is ready for Block 3B to fill in real logic.

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

## Artifacts on GitHub

- **Repo:** stock-bot (main branch).  
- **Path:** `backtests/30d_after_signal_engine_scaffolding_20260214_211701/`  
- **Files committed:** backtest_summary.json, backtest_pnl_curve.json, BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md.  
- **Droplet only (gitignored):** backtest_trades.jsonl, backtest_exits.jsonl, backtest_blocks.jsonl.

---

## Context for reviewer

This run is expected to match prior results because the scaffolding contains placeholder logic only. It ensures the system can safely support full signal-engine logic in Block 3B.
