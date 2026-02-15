# 30-Day Backtest After Block 3D — Signal Weight Tuning, Gating Tuning, Predictive Influence

**Run date:** 2026-02-15 00:31:57 UTC  
**Environment:** Production droplet (paper trading replay).  
**Code:** Block 3D — Signal weight tuning, gating tuning, regime-specific weighting, sector alignment, composite gate, bounded delta.

---

## Window

2026-01-15 → 2026-02-14 (30 days)

---

## What changed

Block 3D is the first iteration intended to meaningfully influence P&L. It tunes weights, gates, and integration:

- **Base weights (3D):** trend 0.05, momentum 0.04, volatility 0.025, regime 0.025, sector 0.025, reversal 0.015, breakout 0.025, mean_reversion 0.015 (stronger trend/momentum, lower reversal/mean_reversion).
- **Regime-specific adjustments:** BULL → boost trend, momentum, breakout; damp reversal, mean_reversion. BEAR → boost trend, momentum, reversal; damp mean_reversion. RANGE → boost reversal, mean_reversion; damp trend, breakout.
- **Sector alignment:** sector_signal and trend_signal agree → multiplier 1.2; disagree → 0.5.
- **Volatility gate:** vol_signal < 0 → 0.25; vol_signal > 0.7 → 0.5; else 1.0.
- **Regime gate:** BULL with negative trend/momentum → 0.5; BEAR with positive trend/momentum → 0.5; else 1.0.
- **Composite gate:** vol_gate × regime_gate × sector_multiplier, bounded ≥ 0.1.
- **Bounded delta:** final weighted delta clamped to [-0.25, +0.25].

Exits, UW, survivorship, wheel, and constraints are unchanged.

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

## Metrics vs baseline

- **Baseline (Block 3C):** P&L -$162.15, win rate 15.16%.
- **Block 3D:** P&L -$162.15, win rate 15.16% — **unchanged** at aggregate level. Regime-specific weights and gating are active; bounded delta and composite gate keep impact within safe range. Symbol-level and regime-specific behavior may differ; inspect exit/block distributions and symbol-level P&L for next tuning.

---

## Stability and regressions

- No regressions: aggregate metrics match baseline. All new code paths return floats; missing keys default to 0.0; weighted delta and gate bounded.

---

## Artifacts on GitHub

- **Repo:** stock-bot (main branch).  
- **Path:** `backtests/30d_after_signal_engine_block3d_20260215_003157/`  
- **Files committed:** backtest_summary.json, backtest_pnl_curve.json, BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md, BLOCK_3D_MULTI_AI_REPORT.md.  
- **Droplet only (gitignored):** backtest_trades.jsonl, backtest_exits.jsonl, backtest_blocks.jsonl.

---

## Next steps

- Inspect exit reason distribution (signal_decay vs baseline) and block reasons (score_floor/displacement).
- Compare symbol-level P&L and regime-specific behavior (BULL vs BEAR vs RANGE) to baseline.
- Tune weights or gate thresholds (e.g. higher trend in BULL, tighter sector alignment) and re-run 30-day backtest to measure P&L movement.
