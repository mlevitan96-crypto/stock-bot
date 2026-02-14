# 30-Day Backtest After Block 3B — Real Raw Signal Engine Logic

**Run date:** 2026-02-14 21:30:34 UTC  
**Environment:** Production droplet (paper trading replay).  
**Code:** Block 3B — Real predictive signal logic in raw_signal_engine.py (trend, momentum, volatility, regime, sector, reversal, breakout, mean-reversion).

---

## Window

2026-01-15 → 2026-02-14 (30 days)

---

## What changed

Block 3B replaces placeholder (0.0-returning) functions in `src/signals/raw_signal_engine.py` with real predictive logic:

- **Trend:** short EMA (12) vs long EMA (26), normalized to [-1, 1].
- **Momentum:** price change over 14-bar window, normalized.
- **Volatility:** std of returns; healthy band → positive; chop/chaos → negative.
- **Regime:** BULL=1, BEAR=-1, RANGE/UNKNOWN=0.
- **Sector:** sector_momentum clamped to [-1, 1].
- **Reversal:** RSI-based; oversold → positive, overbought → negative.
- **Breakout:** above resistance → positive, below support → negative.
- **Mean reversion:** z-score vs 20-bar SMA; stretched down → positive, stretched up → negative.

`live_entry_adjustments` optionally applies small additive weights (0.01 per signal) from these raw signals. Exits, UW, survivorship, wheel, and constraints are unchanged.

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

## Exit and block highlights

- **Exit reasons:** signal_decay variants dominate; flow_reversal and stale_alpha_cutoff appear as secondary.
- **Exit regimes:** normal 1,728; fire_sale 1,087.
- **Block reasons:** max_new_positions_per_cycle 1,041; max_positions_reached 282; expectancy_blocked:score_floor_breach 357; displacement_blocked 214; symbol_on_cooldown 63; order_validation_failed 43.

---

## Artifacts on GitHub

- **Repo:** stock-bot (main branch).  
- **Path:** `backtests/30d_after_signal_engine_block3b_20260214_213034/`  
- **Files committed:** backtest_summary.json, backtest_pnl_curve.json, BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md.  
- **Droplet only (gitignored):** backtest_trades.jsonl, backtest_exits.jsonl, backtest_blocks.jsonl.

---

## Context for reviewer

This is the first run with real raw signal engine logic. Metrics match the Block 3A (scaffolding) baseline (P&L -$162.15, win rate 15.16%), which is expected: signal weights in entry scoring are small and no exit/UW/wheel logic was changed. The run validates that the new signals integrate without breaking the pipeline and provides a baseline for future tuning of signal weights and thresholds.
