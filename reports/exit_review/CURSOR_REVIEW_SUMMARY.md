# Exit Review — Summary for Cursor

This folder is the single place for Cursor to review exit-review and exit-signal tuning outputs.

---

## 1. Historical exit review (legacy harvest)

- **Script (on droplet):** `scripts/CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh`
- **Runner (local → droplet):** `scripts/run_historical_exit_review_on_droplet.py`
- **Local summary for Cursor:** [LATEST_HISTORICAL_RUN_SUMMARY.md](./LATEST_HISTORICAL_RUN_SUMMARY.md)  
  Written automatically after a successful droplet run (run dir, `CURSOR_FINAL_SUMMARY.txt`, `BOARD_DECISION.json`).
- **Artifacts on droplet:** `reports/exit_review/historical_historical_exit_review_<timestamp>/`

---

## 2. Exit grid search (find best exit params)

- **Script (on droplet):** `scripts/CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh`
- **Runner (local -> droplet):** `scripts/run_exit_grid_search_on_droplet.py`
- **What it does:** Runs many exit-rule variations (trailing_stop_pct, profit_target_pct, stop_loss_pct, time_stop_minutes) on historical exits using bar-based simulation; ranks configs by simulated PnL; **multi-persona adversarial board review** (prosecutor, defender, quant, SRE, board) recommends top config.
- **Local summary for Cursor:** [LATEST_GRID_SEARCH_SUMMARY.md](./LATEST_GRID_SEARCH_SUMMARY.md) (written after droplet run).
- **Plan:** [EXIT_IMPROVEMENT_PLAN.md](./EXIT_IMPROVEMENT_PLAN.md) — how we stop bleeding profit and iterate with current data.
- **Alpaca bars final reminder:** `scripts/CURSOR_ALPACA_BARS_FINAL_REMINDER_AND_EXECUTION.sh` — authoritative Data API reminder; grid is unblocked only by setting ALPACA_API_KEY/SECRET on droplet.

---

## 3. Exit signal tune + rerun (config-only)

- **Script (on droplet):** `scripts/CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh`
- **Steps:** Extract tuning from prior run → apply config → re-run historical review with tuned signals → compare baseline vs tuned edge metrics.
- **Artifacts on droplet:** `reports/exit_review/tuned_exit_tune_rerun_<timestamp>/`
  - `tuning_directives.json`
  - `config/exit_candidate_signals.tuned.json`
  - `edge_comparison.json`
  - `CURSOR_FINAL_SUMMARY.txt`
- **Local summary for Cursor:** After running the tune script on the droplet, fetch that run’s `CURSOR_FINAL_SUMMARY.txt` and `edge_comparison.json` into this folder (e.g. `LATEST_TUNE_RERUN_SUMMARY.md`) or open the run dir via your droplet workflow.

---

## 4. Decision flow

| BOARD_DECISION | Next step |
|----------------|-----------|
| **PROMOTE**    | Prepare shadow/paper enablement using CTR. |
| **TUNE**       | Run `CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh`; iterate config and re-run as needed. |
| **HOLD**       | No behavior change; archive findings. |

---

## 5. Key files in repo

| Purpose | Path |
|--------|------|
| Historical harvest + review | `scripts/CURSOR_HISTORICAL_EXIT_TRUTH_HARVEST_AND_REVIEW.sh` |
| Tune + rerun | `scripts/CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh` |
| Extract tuning directives | `scripts/analysis/extract_exit_tuning_directives.py` |
| Apply tuning (config) | `scripts/analysis/apply_exit_signal_tuning.py` |
| Compare baseline vs tuned | `scripts/analysis/compare_exit_edge_runs.py` |
| Replay (optional `--config`) | `scripts/analysis/replay_exits_with_candidate_signals.py` |
| Grid search (bar sim) | `scripts/analysis/exit_param_grid_search.py` |
| Grid board review | `scripts/analysis/exit_grid_board_review.py` |
| Grid orchestration | `scripts/CURSOR_EXIT_GRID_SEARCH_AND_REVIEW.sh` |
| Fetch missing bars + grid rerun | `scripts/CURSOR_FETCH_MISSING_BARS_AND_RERUN_GRID.sh` |
| Find exits missing bars | `scripts/analysis/find_exits_missing_bars.py` |
| Fetch bars from Alpaca | `scripts/analysis/fetch_missing_bars_from_alpaca.py` |
