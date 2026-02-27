# First summary (2026-02-20)

## What was done

1. **Deploy to droplet**  
   - Pushed commit (data-driven scoring only + today backtest summary script).  
   - Ran `DropletClient().deploy()`: git pull + restart stock-bot. **Live on droplet.**

2. **Today backtest summary (run on droplet, fetched)**  
   - Ran `scripts/today_signal_backtest_summary_on_droplet.py` on the droplet for **2026-02-20**.  
   - Fetched:  
     - `reports/investigation/fetched/today_backtest_SUMMARY_20260220.md`  
     - `reports/investigation/fetched/today_backtest_summary_20260220.json`

3. **1-day backtest on droplet**  
   - Ran `BACKTEST_DAYS=1` with `board/eod/run_30d_backtest_on_droplet.sh`.  
   - Output dir: `backtests/1d_signal_summary_20260220_222408/`  
   - Artifacts: `backtest_trades.jsonl`, `backtest_exits.jsonl`, `backtest_blocks.jsonl`, `backtest_summary.json`, `backtest_pnl_curve.json`, `SIGNAL_EDGE_ANALYSIS_REPORT.md`, `backtest_run_summary.json`.

---

## First summary numbers (2026-02-20, from droplet)

| Metric | Value |
|--------|--------|
| Date | 2026-02-20 |
| MIN_EXEC_SCORE | 2.5 |
| Candidates at expectancy gate | 2,000 |
| Entered (attribution) | 0 |
| Blocked | 0 |
| Composite ≥ MIN_EXEC_SCORE | 0 |
| Direction long | 1,933 |
| Direction short | 0 |
| Direction neutral | 67 |

**Signals fired:** All 22 signals had **0** candidates with non-zero contribution in the summary.  
**Per-candidate:** Composite scores ~1.055 or 0.575; composite_gate=pass, expectancy_gate=fail; all signal values 0 in the report.

**Note:** The summary is built from `logs/score_snapshot.jsonl`. On the droplet, snapshot records have `weighted_contributions` (component breakdown) empty or not written, so the report shows zeros for every signal. Once the live path writes full component breakdown into the snapshot, future runs of `today_signal_backtest_summary_on_droplet.py` will show per-signal values and which signals fired.

---

## How to re-run

- **Today summary (on droplet):**  
  `python3 scripts/today_signal_backtest_summary_on_droplet.py [--date YYYY-MM-DD]`

- **From local (run on droplet + fetch):**  
  `python scripts/run_today_backtest_summary_on_droplet.py [--date YYYY-MM-DD]`

- **1-day backtest on droplet:**  
  `export BACKTEST_DAYS=1 && bash board/eod/run_30d_backtest_on_droplet.sh`
