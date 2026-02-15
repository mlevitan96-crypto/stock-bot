# 30-Day Backtest After Block 3C — Signal Weighting, Gating, and Predictive Integration

**Run date:** 2026-02-15 00:25:15 UTC  
**Environment:** Production droplet (paper trading replay).  
**Code:** Block 3C — Signal weighting, gating (volatility/regime), and predictive integration.

---

## Window

2026-01-15 → 2026-02-14 (30 days)

---

## What changed

Block 3C adds **weighting** and **gating** so raw signals meaningfully influence entry scoring:

- **Weights (small, safe):** Per-signal weights in `DEFAULT_SIGNAL_WEIGHTS`: trend 0.03, momentum 0.03, volatility 0.02, regime 0.02, sector 0.02, reversal 0.02, breakout 0.02, mean_reversion 0.02 (max total ~0.18).
- **Gating:** `compute_signal_gate_multiplier(raw_signals)`:
  - **1.0** when volatility is in healthy band and regime is BULL/BEAR.
  - **0.5** when regime is RANGE/UNKNOWN (damp).
  - **0.25** when volatility indicates chop/chaos (vol_signal < 0).
- **Integration:** `apply_signal_quality_to_score` now uses `gate * get_weighted_signal_delta(raw_signals, DEFAULT_SIGNAL_WEIGHTS)` instead of a flat 0.01 per signal. Exits, UW, survivorship, wheel, and constraints are unchanged.

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

## Stability and regressions

- **No regressions:** Aggregate metrics match Block 3B baseline (P&L -$162.15, win rate 15.16%). Gating and bounded weights keep the first iteration safe.
- **Pre-existing test:** One validation test still fails (test_governance_enforcer_blocks_stale_actions — missing board.eod.governance_enforcer); not introduced by Block 3C.

---

## Artifacts on GitHub

- **Repo:** stock-bot (main branch).  
- **Path:** `backtests/30d_after_signal_engine_block3c_20260215_002515/`  
- **Files committed:** backtest_summary.json, backtest_pnl_curve.json, BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md.  
- **Droplet only (gitignored):** backtest_trades.jsonl, backtest_exits.jsonl, backtest_blocks.jsonl.

---

## Context for reviewer

First run where raw signals meaningfully influence scoring via explicit weights and volatility/regime gating. Metrics unchanged from Block 3B; next iteration can tune weights or gate thresholds and re-run backtests to measure impact.

---

## Next steps

- Tune per-signal weights (e.g. increase trend/momentum in BULL, reversal in RANGE).
- Optionally add sector/trend gating (e.g. damp when sector_signal and trend_signal disagree).
- Re-run 30-day backtest after tuning and compare P&L, win rate, and exit/block distributions.
