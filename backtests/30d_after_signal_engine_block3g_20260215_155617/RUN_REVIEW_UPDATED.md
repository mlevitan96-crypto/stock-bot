# Block 3G — Updated Run Review and Next Steps

**Review date:** After follow-up pull and check for new 3g run.  
**Backtest dir:** `backtests/30d_after_signal_engine_block3g_20260215_155617`

---

## 1. Current run results (this dir)

| Metric | Value |
|--------|--------|
| **Window** | 2026-01-15 → 2026-02-14 (30 days) |
| **Trades** | 2,243 |
| **Exits** | 2,815 |
| **Blocks** | 2,000 |
| **Total P&L (USD)** | -$162.15 |
| **Winning trades** | 340 |
| **Losing trades** | 650 |
| **Win rate (%)** | 15.16 |

**Regime breakdown (from Signal Edge Analysis):**

| Regime | Trades | Win rate (%) | Avg P&L ($) | Total P&L ($) |
|--------|--------|--------------|-------------|---------------|
| MIXED | 2,233 | 15.09 | -0.07 | -155.48 |
| UNKNOWN | 10 | 30.0 | -0.67 | -6.67 |

**Signal data in this run:** Only **regime_signal** (near_zero) and **entry_score** (positive / near_zero) have non-missing buckets. All other raw signals (trend, momentum, volatility, sector, reversal, breakout, mean_reversion) show as **"missing"** because this run was produced on the droplet **before** the Block 3G replay-time injection code was merged.

---

## 2. Status of the “next” 3g run (with injection)

- **Pulled latest** from `origin/main`. No **new** 3g backtest dir has been pushed (no `30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS` with timestamp **newer** than `20260215_155617`).
- So the **first** 3g run with **replay-time injection** (and thus full per-signal edge data) is **not yet on main**. Possible reasons:
  - The droplet run with injection was very slow (4k+ events × bar loading) and may have timed out or not completed.
  - The run was not re-triggered after the injection code was merged.
  - Network or API limits on the droplet (e.g. Alpaca bar fetches) could have caused failures.

---

## 3. Next steps

### A. Produce a 3g run with injection

1. **On your machine**, run:
   ```bash
   python scripts/run_backtest_on_droplet_and_push.py
   ```
   This uses `OUT_DIR_PREFIX=30d_after_signal_engine_block3g`. The droplet will pull latest (with injection), run the 30-day backtest (computing signals at replay for every trade and block), run Signal Edge Analysis, then commit and push the **new** backtest dir to main.

2. **Allow 20–60 minutes.** If the run times out or fails, consider:
   - Running the backtest **on the droplet** via SSH and then pushing the new dir manually, or
   - Reducing the replay window or sampling for a faster test run (would require a small script change).

### B. After the new 3g dir is on main

1. **Pull:**
   ```bash
   git pull origin main
   ```

2. **Find the new dir:**  
   `backtests/30d_after_signal_engine_block3g_YYYYMMDD_HHMMSS/` (timestamp > 20260215_155617).

3. **Confirm** `SIGNAL_EDGE_ANALYSIS_REPORT.md` in that dir has per-signal buckets (negative / near_zero / positive) for trend, momentum, volatility, sector, reversal, breakout, mean_reversion — **no "missing"** for those signals.

4. **Add/update in that new dir:**
   - **BACKTEST_REVIEW_SUMMARY_FOR_EXTERNAL_REVIEWER.md** — Note that this run has full injected signals.
   - **BLOCK_3G_MULTI_AI_REPORT.md** — Fill **Section 2** with:
     - 1–3 signals to **weight UP** in Block 3H (from better win rate or expectancy),
     - 1–3 signals to **weight DOWN** or gate harder (from worse expectancy),
     - Any **regime-specific** adjustments (if BULL/BEAR/RANGE appear).

5. **Commit and push** the new dir and reports.

Detailed checklist: **NEXT_STEPS_3G.md** in this dir.

---

## 4. Summary

- **Current 3g run (155617):** Aggregate results and regime breakdown are as above; raw signal buckets are missing in the report because injection was not in the code at run time.
- **Next 3g run:** Not yet on main. Trigger it with `run_backtest_on_droplet_and_push.py`, then pull and complete the reports in the new dir using **NEXT_STEPS_3G.md** and the updated Signal Edge Analysis report.
