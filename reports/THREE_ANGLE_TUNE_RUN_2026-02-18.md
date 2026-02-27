# Three-Angle Tune Run — 2026-02-18

**Objective:** Run the backtest on the droplet three times with different tuning angles to support profitability tuning.

---

## What Was Done

### 1. Three backtest runs (on droplet, 7-day window)

| Run | Angle | Config | Droplet output dir |
|-----|--------|--------|---------------------|
| **1. Baseline** | No overlay | (default exit weights) | `backtests/30d_tune_baseline_20260218_040651` |
| **2. Exit flow** | Exit earlier when flow deteriorates | `flow_deterioration`: 0.20 → **0.22** | `backtests/30d_tune_flow022_20260218_040706` |
| **3. Exit score** | Exit earlier when composite score deteriorates | `score_deterioration`: 0.25 → **0.28** | `backtests/30d_tune_score028_20260218_040930` |

- **Script:** `board/eod/run_30d_backtest_on_droplet.sh`
- **Env used:** `OUT_DIR_PREFIX=30d_tune_*`, `BACKTEST_DAYS=7`, `GOVERNED_TUNING_CONFIG=...` for runs 2 and 3.
- **Overlay for Run 3:** `config/tuning/overlays/exit_score_weight_tune.json` (created on droplet for the run; also added to repo).

### 2. Aggregate metrics (from droplet)

Metrics were computed from `backtest_exits.jsonl` for each run:

| Run       | total_trades | total_pnl_usd | win_rate | avg_profit_giveback |
|-----------|--------------|---------------|----------|----------------------|
| Baseline  | 1618         | -152.34       | 0.3424   | (null)               |
| Flow 0.22 | 1618         | -152.34       | 0.3424   | (null)               |
| Score 0.28| 1618         | -152.34       | 0.3424   | (null)               |

**Why the numbers are the same:** The current 30d backtest **replays** historical data from `logs/attribution.jsonl` and `logs/exit_attribution.jsonl`. It does **not** re-simulate entry or exit decisions using the overlay. So the same trades and exits are written regardless of `GOVERNED_TUNING_CONFIG`. Overlays only affect **live/paper** behavior when the bot actually computes exit scores with the tuned weights.

---

## How This Helps Moving Toward Profitability

1. **Process is in place**  
   We can run baseline vs overlay backtests on the droplet with different `OUT_DIR_PREFIX` and `GOVERNED_TUNING_CONFIG`. The same pattern can be used for future overlays (e.g. entry thresholds, other exit weights).

2. **Two concrete levers are ready to test in paper**  
   - **Flow 0.22:** `config/tuning/overlays/exit_flow_weight_phase9.json` — already used in Phase 9 (LOCK).  
   - **Score 0.28:** `config/tuning/overlays/exit_score_weight_tune.json` — exit a bit earlier when composite score deteriorates.

3. **To see overlay impact in numbers you need one of:**  
   - **Option A — Backtest that uses overlay in the exit path:** Extend the backtest (or add a separate “exit simulation” step) so that for each trade it recomputes exit_score with the overlay and simulates exit time. Then compare PnL/win rate across baseline vs flow022 vs score028.  
   - **Option B — Paper/live comparison:** Run paper (or live) with baseline for N days, then with one overlay for N days, and compare effectiveness (e.g. `run_effectiveness_reports.py` on logs) and PnL.

4. **Next steps that move toward profits**  
   - **Evidence from logs:** Sync one backtest dir (or use existing logs), run `run_effectiveness_reports.py` and `generate_recommendation.py` locally to get entry_vs_exit_blame, worst signals, worst giveback exits, and suggested levers (see `docs/PATH_TO_PROFITABILITY.md`).  
   - **Governed paper test:** Pick one overlay (e.g. score 0.28), run paper with it for 7–14 days, then run the same effectiveness + comparison vs baseline; lock or revert per Phase 9 process.  
   - **Holdout evaluation:** When you have multiple candidate overlays, use `scripts/governance/holdout_metrics.py` on backtest dirs (once backtest output reflects overlay, e.g. after Option A) to compare on a holdout period and reduce forward bias.

---

## Summary

- **Done:** Three droplet backtests ran successfully with three angles (baseline, flow_deterioration 0.22, score_deterioration 0.28).  
- **Result:** Aggregate metrics are identical across runs because the pipeline replays historical logs and does not yet re-apply overlay in the exit path.  
- **To improve profits:** Use the same run pattern for new overlays; add either (A) exit-path simulation in backtest or (B) paper/live A/B comparison; and drive next levers from effectiveness reports and recommendations.

Artifacts on droplet: `backtests/30d_tune_baseline_*`, `backtests/30d_tune_flow022_*`, `backtests/30d_tune_score028_*`.
