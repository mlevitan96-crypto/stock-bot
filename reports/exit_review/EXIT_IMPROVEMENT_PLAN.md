# Exit Improvement Plan — Stop Bleeding Profit

When the board decision stays **TUNE**, we need a concrete path to better exits and more profit. This plan uses the data we already have, runs on the droplet, and iterates over many exit-rule variations to find the best combinations.

**Exit attribution schema:** Records in `logs/exit_attribution.jsonl` use `attribution_components` where every component has `signal_id` starting with **`exit_`** (e.g. exit_flow_deterioration, exit_score_deterioration). Effectiveness and board review rely on this canonical naming.

---

## 1. What we do with current data

- **Historical exit truth** — Already harvested (2,700+ exits) from `logs/exit_attribution.jsonl`, `exit_truth.jsonl`, etc. Each record has symbol, entry/exit timestamps, entry/exit price, PnL, close_reason.
- **Bar-based simulation** — For each exit we can load OHLC bars (from `data/bars/` or `data/bars/alpaca_daily.parquet` on the droplet) between entry and exit. We then **simulate** alternative exit rules bar-by-bar: profit target, stop loss, trailing stop, time stop. That gives us a **simulated PnL** for each (exit, param set). No new data needed for the logic; more bars = better coverage.

---

## 2. How we find “when is the best time to exit”

1. **Parameter grid** — We vary:
   - `trailing_stop_pct` (e.g. 1%, 1.5%, 2%, 2.5%, 3%)
   - `profit_target_pct` (e.g. 1.5%, 2%, 2.5%, 3%)
   - `stop_loss_pct` (e.g. 2%, 3%)
   - `time_stop_minutes` (e.g. 120, 180, 240, 360)
2. **Simulation** — For each exit that has bars, we run each param set: bar-by-bar we check (in order) profit target hit → stop loss hit → trailing stop from high water → time stop. We record simulated PnL% per exit per config.
3. **Ranking** — We sum simulated PnL% over all simulated exits for each param set and rank. Top configs are the ones that would have made the most (or lost the least) with our **current signal set** and that exit rule.
4. **Board review** — Prosecutor / Defender / Quant / SRE / Board review the grid results (coverage, top configs, overfitting risk) and output a **recommended config** and decision (e.g. PROMOTE_TOP_CONFIG or TUNE_OR_GET_MORE_BARS).

So “best time to exit” is answered by: **the combination of (trailing, profit target, stop, time stop) that maximizes simulated total PnL on historical exits that have bars.**

---

## 3. What to run on the droplet (in order)

| Step | Script | What it does |
|------|--------|---------------|
| 1 | **Historical harvest + review** (if not already done) | `run_historical_exit_review_on_droplet.py` → produces `normalized_exit_truth.json` in a `historical_*` run dir. |
| 2 | **Fetch missing bars + grid** (recommended if grid had 0 coverage) | `CURSOR_FETCH_MISSING_BARS_AND_RERUN_GRID.sh` → finds exits missing bars, fetches from Alpaca into `data/bars`, then re-runs grid search + board review. |
| 3 | **Exit grid search + board review** (if bars already present) | `run_exit_grid_search_on_droplet.py` → uses latest `historical_*/normalized_exit_truth.json`, runs many param combos with bar-based simulation, writes `grid_results.json` and `grid_board_review/GRID_RECOMMENDATION.json`. |
| 4 | **Apply top config and validate** | Copy recommended_config from GRID_RECOMMENDATION.json into `config/exit_candidate_signals.tuned.json`, then run `CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh` (or its runner) for apples-to-apples comparison vs baseline. |

---

## 4. Scripts and artifacts

| Purpose | Path |
|--------|------|
| Grid search (bar sim) | `scripts/analysis/exit_param_grid_search.py` |
| Board review of grid | `scripts/analysis/exit_grid_board_review.py` |
| Orchestration (on droplet) | `scripts/CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh` |
| Fetch missing bars + grid rerun | `scripts/CURSOR_FETCH_MISSING_BARS_AND_RERUN_GRID.sh` |
| Find exits missing bars | `scripts/analysis/find_exits_missing_bars.py` |
| Fetch bars from Alpaca | `scripts/analysis/fetch_missing_bars_from_alpaca.py` |
| Run grid on droplet | `scripts/run_exit_grid_search_on_droplet.py` |
| Local summary after run | `reports/exit_review/LATEST_GRID_SEARCH_SUMMARY.md` |

Grid run dir on droplet: `reports/exit_review/exit_grid_<timestamp>/`  
Contains: `grid_results.json`, `grid_board_review/`, `CURSOR_FINAL_SUMMARY.txt`.

---

## 5. Do we need more data?

- **For logic:** No. We iterate with the data we have; bars are used when present.
- **For better answers:** Yes, if **bar coverage** is low (e.g. &lt; 50% of exits have bars). Then:
  - Fetch more bars (Alpaca 1Min/5Min for symbols and dates of our exits) into `data/bars/` or expand `data/bars/alpaca_daily.parquet`.
  - Re-run grid search; more exits will be simulated and rankings will be more reliable.
- **Bigger review of datasets:** Optional. We can later add regime filters (e.g. only high-vol dates), symbol buckets, or time-of-day segments and run separate grids per segment to get “best exit for this regime.”

---

## 6. Multiple models / board review

- **Prosecutor** — Challenges: low bar coverage, overfitting, require paper/shadow before live.
- **Defender** — Argues grid is the right way to compare exit rules; top configs are valid tuning candidates.
- **Quant** — Checks coverage, param set count, and data quality.
- **SRE** — Confirms config-only change; safe to iterate.
- **Board** — Synthesizes PROMOTE_TOP_CONFIG vs TUNE_OR_GET_MORE_BARS and writes `GRID_RECOMMENDATION.json` with `recommended_config` and next steps.

---

## 7. Quick start (run grid on droplet)

From repo root (local):

```bash
python scripts/run_exit_grid_search_on_droplet.py
```

This uploads the grid script and orchestration, runs `CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh` on the droplet (using the latest historical run’s normalized exits), and fetches the summary into `reports/exit_review/LATEST_GRID_SEARCH_SUMMARY.md`. Then apply the recommended config and run tune+rerun to validate.
