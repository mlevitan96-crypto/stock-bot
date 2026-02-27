# Profitability Patterns, Droplet Backtests, and Non–Forward-Biased Evaluation

**Purpose:** Answer (1) what patterns we can see from gathered data, (2) what backtests we can run on the droplet to improve exits/entries, and (3) how to get better with the data we have using non–forward-biased backtests.

---

## 1. New patterns and ways to increase profitability (from existing data)

We already have a full pipeline that turns backtest (or live) data into **actionable levers**. The data you have is:

- **On droplet:** Backtest dirs such as `backtests/30d_baseline_20260218_032951` and `backtests/30d_proposed_20260218_032957` with `backtest_exits.jsonl`, `backtest_trades.jsonl`, `backtest_summary.json`. Phase 9 runs did **not** produce an `effectiveness/` subdir on the droplet (governance/analysis scripts are not present there).

- **Locally:** The same pipeline can be run on any backtest dir once you have it (e.g. by syncing the dir from the droplet or running a backtest locally).

### Pipeline: evidence → patterns → recommendations

| Step | What to run | What you get |
|------|-------------|--------------|
| 1 | `python scripts/analysis/run_effectiveness_reports.py --backtest-dir backtests/30d_XXX --out-dir backtests/30d_XXX/effectiveness` | `signal_effectiveness.json`, `exit_effectiveness.json`, `entry_vs_exit_blame.json`, `counterfactual_exit.json` |
| 2 | `python scripts/governance/profitability_baseline_and_recommend.py --effectiveness-dir backtests/30d_XXX/effectiveness --out backtests/30d_XXX` | `profitability_baseline.json`, baseline metrics |
| 3 | `python scripts/governance/generate_recommendation.py --backtest-dir backtests/30d_XXX` | `profitability_recommendation.md`: top 5 harmful signals, top 3 worst giveback exits, **overlay candidates** (e.g. flow_deterioration +0.02 or entry threshold raise) |

**Where the “patterns” live:**

- **entry_vs_exit_blame:** If most losers are **weak entry** → raise entry bar or down-weight bad signals. If most are **exit timing** (high giveback, had MFE) → tune **exit** weights (e.g. `flow_deterioration`, `score_deterioration`). See `docs/PATH_TO_PROFITABILITY.md`.
- **signal_effectiveness:** Low win_rate / high avg_MAE / high giveback → reduce weight or require stronger confirmation; strong signals → consider boosting carefully.
- **exit_effectiveness:** High avg_profit_giveback or low % left_money on an exit reason → increase that exit weight to exit earlier; reasons that save loss well → keep or slightly reduce.
- **counterfactual_exit:** “hold_longer_would_help” vs “exit_earlier_would_save” → guides exit/trail/stop overlays.

**Practical way to use existing data:** Sync one full backtest dir (e.g. baseline or proposed) from the droplet to your machine, then run the three steps above locally. Use `profitability_recommendation.md` and the JSON reports to pick the **next single overlay** and test it in a governed compare (Phase 9 style).

---

## 2. Backtests on the droplet to improve exits and entries

Yes. The same “baseline vs proposed” pattern you used in Phase 9 is the right way to test exit/entry changes.

### What the droplet can do today

- **Script:** `board/eod/run_30d_backtest_on_droplet.sh`
- **Controls:**
  - `OUT_DIR_PREFIX=30d_baseline` → baseline (no overlay).
  - `OUT_DIR_PREFIX=30d_proposed` and `GOVERNED_TUNING_CONFIG=config/tuning/overlays/your_overlay.json` → proposed run with that overlay.
  - `BACKTEST_DAYS=7` → 7-day window (faster); omit for 30 days.

### Improving exits

1. From effectiveness (or recommendation), identify an exit lever (e.g. `flow_deterioration`, `score_deterioration`).
2. Create a small overlay that changes only that lever (e.g. +0.02).
3. On droplet:
   - Run baseline: `OUT_DIR_PREFIX=30d_baseline BACKTEST_DAYS=7 bash board/eod/run_30d_backtest_on_droplet.sh`
   - Run proposed: `OUT_DIR_PREFIX=30d_proposed GOVERNED_TUNING_CONFIG=config/tuning/overlays/exit_flow_phase10.json BACKTEST_DAYS=7 bash board/eod/run_30d_backtest_on_droplet.sh`
4. Compare (see below): PnL, win rate, giveback. If better or no material regression and guards pass → paper/canary then lock.

### Improving entries

Same idea with entry overlays: e.g. `entry_thresholds` or `entry_weights_v3` (down-weight a bad signal or raise bar). Run baseline once, then one or more proposed runs with different entry overlays and compare.

### Comparing results (droplet vs local)

- **On droplet:** `scripts/governance/compare_backtest_runs.py` is not on the droplet. You can either add it (and `regression_guards.py`) to the repo and pull on the droplet, or run comparison **locally** after syncing the two backtest dirs (baseline + proposed) and use:
  - `python scripts/governance/compare_backtest_runs.py --baseline backtests/30d_baseline_... --proposed backtests/30d_proposed_... --out reports/governance_comparison/your_label`
- **Regression guards:** Run locally: `python scripts/governance/regression_guards.py` (same as in Phase 9 evidence recovery).

So: **yes, we can run backtests on the droplet to figure out how exits/entries can be improved** by running baseline + one or more overlay-backed proposed runs and comparing (locally if needed).

---

## 3. Non–forward-biased backtests with the data we have

### What is already unbiased

- The 30d backtest replays **in time order** from logs (attribution + exit_attribution). It does not use future information for past decisions; it’s “no look-ahead” in that sense.
- So a single run is already **temporally consistent**. The main risk is **overfitting to the same period** when we choose levers (e.g. which overlay is “best”) and then treat that same period as proof.

### What would make it more robust: a holdout period

- **Idea:** Reserve the **last N days** of the backtest window as a “test” set. Choose levers (or overlay) using only the **train** period (e.g. first 23 days); evaluate **only on the holdout** (e.g. last 7 days) to decide what to lock.
- That way we don’t “peek” at the holdout when deciding; we only use it for final evaluation.

### How to do it with current artifacts

1. **Run backtests as today** (e.g. baseline + proposed with overlay A, overlay B), each for the same 30d (or 7d) window.
2. **When comparing,** compute metrics **only on exits in the last 7 days** (or your chosen holdout):
   - Each backtest dir has `backtest_exits.jsonl` with timestamps.
   - Filter lines to `exit_date in [last_7_days]`, then compute total PnL, win rate, (and giveback if present) on that subset.
3. **Decision rule:** Pick the overlay that wins on **holdout** (or ties with no regression), not on the full window. That is a simple, non–forward-biased use of the same data.

A small script does step 2: **`scripts/governance/holdout_metrics.py`**. Given a backtest dir and `--holdout-days 7`, it aggregates only exits in the last 7 days and outputs total_pnl_usd, win_rate, total_trades, avg_profit_giveback. Run it on each backtest dir (baseline, proposed_A, proposed_B), then compare those outputs to pick the best overlay without using the holdout for tuning.

```bash
python scripts/governance/holdout_metrics.py --backtest-dir backtests/30d_baseline_XXX --holdout-days 7
python scripts/governance/holdout_metrics.py --backtest-dir backtests/30d_proposed_XXX --holdout-days 7 --out-json
```

### Optional: train-window-only “tuning” run

If you want to be strict, you could:

- Run a backtest with `--end-date YYYY-MM-DD` so the window ends at “train end” (e.g. 23 days before “today”).
- Use that run only to generate effectiveness and recommendations (pattern discovery).
- Then run **separate** backtest(s) for the **holdout window only** (e.g. last 7 days) with baseline vs chosen overlay, and evaluate only on that. That would require the backtest script to support a window that is only the holdout period (it already supports `--start-date` / `--end-date` / `--days`), so it’s feasible.

**Summary:** We can get better with the same data by (1) not tuning on the holdout, and (2) evaluating only on the holdout when comparing overlays. The current backtest is already time-ordered; adding a holdout evaluation step makes the **choice** of overlay non–forward-biased.

---

## Quick reference

| Goal | Action |
|------|--------|
| See patterns from existing data | Sync a backtest dir from droplet → run `run_effectiveness_reports.py` → run `profitability_baseline_and_recommend.py` + `generate_recommendation.py` locally. Read `effectiveness/` + `profitability_recommendation.md`. |
| Test exit/entry changes on droplet | Run baseline and proposed(s) with different overlays via `run_30d_backtest_on_droplet.sh`; sync dirs; run `compare_backtest_runs.py` and `regression_guards.py` locally. |
| Reduce forward bias | Run `scripts/governance/holdout_metrics.py --backtest-dir <dir> --holdout-days 7` on each run; compare holdout PnL/win_rate/giveback when choosing overlay. |

See also: `docs/PATH_TO_PROFITABILITY.md`, `reports/phase9_droplet_runbook.md`, and `scripts/governance/compare_backtest_runs.py`.
