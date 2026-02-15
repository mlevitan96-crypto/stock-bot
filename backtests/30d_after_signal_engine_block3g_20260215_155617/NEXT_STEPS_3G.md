# Block 3G — Next steps when new run (with injection) is available

This dir (`155617`) was produced **before** replay-time injection was merged. Raw signals in the Signal Edge Analysis report show as "missing".

## When the next 3g run is pushed to main

1. **Pull**
   ```bash
   git pull origin main
   ```

2. **Find the new 3g dir**
   - Look for `backtests/30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS/` with a **newer** timestamp than `20260215_155617`.

3. **Run Signal Edge Analysis** (if not already in that dir)
   ```bash
   python scripts/run_signal_edge_analysis.py --backtest-dir backtests/30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS/
   ```

4. **Confirm** `SIGNAL_EDGE_ANALYSIS_REPORT.md` in that dir has per-signal edge tables with **no "missing"** buckets for trend_signal, momentum_signal, volatility_signal, sector_signal, reversal_signal, breakout_signal, mean_reversion_signal.

5. **Add/update reports in the new dir**
   - **BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md** — Window, aggregate results, note that this run has full injected signals.
   - **BLOCK_3G_MULTI_AI_REPORT.md** — Fill in **Section 2** with:
     - **1–3 signals to weight UP** (from buckets with better win rate or expectancy).
     - **1–3 signals to weight DOWN or gate harder** (from buckets with worse expectancy).
     - **Regime-specific adjustments** (if BULL/BEAR/RANGE appear in the report).

6. **Commit and push**
   ```bash
   git add backtests/30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS/
   git commit -m "Block 3G: full signal edge report and recommendations for 3g run with injection"
   git push origin main
   ```

## Generating the next 3g run

To produce a new 3g run **with** injection on the droplet:

```bash
python scripts/run_backtest_on_droplet_and_push.py
```

This uses `OUT_DIR_PREFIX=30d_after_signal_engine_block3g`. The run can take 20–60 minutes because it computes signals at replay time for every trade and block (4k+ events). When it finishes, the droplet commits and pushes the new backtest dir to main.
