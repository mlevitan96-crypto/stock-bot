# Backtest Results Check — Do We Have the Data We Need?

**Check date:** After review of all available backtest data on `main`.

---

## 1. Do we have the data we need to get profitable?

**Short answer: Not yet.**

The data we need for **data-driven** profitability is:

- **Per-signal edge:** For each of trend, momentum, volatility, sector, reversal, breakout, mean_reversion we need **buckets** (e.g. negative / near_zero / positive) with **trade count, win rate, avg P&L, expectancy** so we can:
  - Weight **up** signals whose positive (or higher) bucket has better expectancy
  - Weight **down** or gate signals whose negative (or harmful) bucket has worse expectancy

**What we have today:**

| Data | Status |
|------|--------|
| **Aggregate backtest** | ✓ One 3g run: 2,243 trades, -$162.15, 15.16% win rate, 2,815 exits, 2,000 blocks |
| **Exit/block breakdown** | ✓ exit_regime (normal 1,728, fire_sale 1,087); block reasons (max_new_positions 1,041, score_floor 357, etc.) |
| **Regime in report** | ✓ MIXED 2,233, UNKNOWN 10 (no BULL/BEAR/RANGE) |
| **entry_score buckets** | ✓ positive 2,233 (-$0.07 avg), near_zero 10 (-$0.67 avg) — only two buckets, not per-signal |
| **regime_signal** | ✓ near_zero for all 2,243 (no variation) |
| **trend_signal** | ✗ **missing** (all 2,243 in “missing” bucket) |
| **momentum_signal** | ✗ **missing** |
| **volatility_signal** | ✗ **missing** |
| **sector_signal** | ✗ **missing** |
| **reversal_signal** | ✗ **missing** |
| **breakout_signal** | ✗ **missing** |
| **mean_reversion_signal** | ✗ **missing** |

So: we have **one** 3g backtest dir (`30d_after_signal_engine_block3g_20260215_155617`), but that run was produced **before** replay-time injection was in the code on the droplet. So the Signal Edge Analysis report has **no per-signal buckets** for trend/momentum/volatility/sector/reversal/breakout/mean_reversion — only “missing.” We **cannot** yet choose which signals to weight up or down from data.

---

## 2. Can we get profitable from the data we have?

**With current data:** Only in a **limited** way.

- **Already done:** Block 3H implemented **conservative** weight tweaks (more trend/momentum, less reversal/mean_reversion) based on 3D design, not on edge tables. That is live in code; P&L impact will show only after the bot runs with 3H for 30 days and we backtest that new window.
- **entry_score:** “positive” has slightly better avg P&L (-$0.07) than “near_zero” (-$0.67), but both are negative and we don’t know which *underlying signals* drive that. So we can’t yet tune individual signals from this.

**To get profitable in a data-driven way we need:**

1. **At least one backtest run with injection** so that:
   - `backtest_trades.jsonl` and `backtest_blocks.jsonl` have **all** signal fields (trend, momentum, volatility, sector, reversal, breakout, mean_reversion) populated at replay time.
   - Signal Edge Analysis then produces **per-signal** buckets (no “missing” for those signals).

2. **Use that report** to set Block 3H (or 3I) weights: 1–3 signals up, 1–3 down, then re-run backtest on **new** 30d logs from the bot running with the new weights.

So: we are **not** yet able to “get profitable from all the data we are gathering” until we have **one successful run with injection** and an edge report with real buckets.

---

## 3. Why don’t we have a 3g run with injection?

- The **only** 3g dir on `main` is `30d_after_signal_engine_block3g_20260215_155617`, generated at **2026-02-15 15:56:17 UTC** on the droplet, **before** the replay-time injection commit was in the code the droplet ran.
- Later droplet runs (full 30d or 7d with `BACKTEST_DAYS=7`) either:
  - **Timed out** (e.g. 1hr SSH limit) before the run finished, or
  - **Failed** (e.g. git pull, Alpaca/bars_loader, or script error), or
  - **Never pushed** (run completed but push failed).

So no **new** 3g dir with injection has ever appeared on `main`.

---

## 4. What to do next (verifiable)

1. **Produce one run with injection**
   - **On droplet:** Run `python scripts/run_backtest_on_droplet_and_push.py` (and optionally `BACKTEST_DAYS=7` for a 7-day window). Ensure the run completes and pushes. If it times out, run the backtest **on the droplet** via SSH and push the new dir manually.
   - **Locally (if you have bars):** If you have `logs/attribution.jsonl` and `state/blocked_trades.jsonl` for the same window **and** Alpaca (or cached) bars, run:
     - `python scripts/run_30d_backtest_droplet.py --out backtests/3g_injection_local`
     - then `python scripts/run_signal_edge_analysis.py --backtest-dir backtests/3g_injection_local`
     - and check that `SIGNAL_EDGE_ANALYSIS_REPORT.md` has real buckets for trend, momentum, etc.

2. **When you have that report**
   - Open the new 3g (or local) dir’s `SIGNAL_EDGE_ANALYSIS_REPORT.md`.
   - Fill **BLOCK_3G_MULTI_AI_REPORT** Section 2: 1–3 signals to weight up, 1–3 to weight down (and regime-specific if BULL/BEAR/RANGE appear).
   - Optionally refine Block 3H weights from those recommendations and redeploy.

3. **Measure profitability**
   - Run the bot with Block 3H (and any refinements) for 30 days.
   - Run the backtest script on that **new** 30d of logs.
   - Compare `total_pnl_usd` and `win_rate_pct` to baseline (-$162.15, 15.16%).

---

## 5. Summary

| Question | Answer |
|----------|--------|
| **Do we have the data?** | We have aggregate backtest and exit/block/regime/entry_score data. We do **not** have per-signal edge (trend, momentum, volatility, etc.) — all show “missing” in the only 3g run. |
| **Can we check the results?** | Yes. The only 3g run is `backtests/30d_after_signal_engine_block3g_20260215_155617`; its `SIGNAL_EDGE_ANALYSIS_REPORT.md` shows “missing” for every raw signal. No newer 3g run has been pushed to `main`. |
| **Can we get profitable from current data?** | Only via the conservative Block 3H tweaks already in code; full data-driven tuning needs **one backtest run with injection** and the resulting edge report. |

**Bottom line:** We are **one successful injection run** away from having the data needed to tune for profitability. Next step is to get that run (on droplet or locally with bars) and then use the new Signal Edge Analysis report to set weights and re-measure P&L.
