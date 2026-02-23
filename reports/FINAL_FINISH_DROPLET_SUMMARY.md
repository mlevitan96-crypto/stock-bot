# Final Finish Droplet Run — Summary

**Date:** 2026-02-23  
**Droplet:** /root/stock-bot (alpaca / 104.236.102.57 per MEMORY_BANK §6.3)

---

## What Was Run

1. **Scripts pushed to GitHub** and pulled on droplet: `run_final_finish_on_droplet.sh`, `run_push_with_plugins_on_droplet.sh`, `run_finalize_push_on_droplet.sh`.
2. **First final_finish run failed** because the scripts were not executable on the droplet (`[ -x ... ]` failed). Error written to `reports/backtests/final_finish_20260223T001946Z/ERROR.txt`.
3. **Scripts made executable on droplet** (`chmod +x`), then **final_finish was started again** in background (`nohup ... >> /tmp/final_finish_run.log`).
4. **push_with_plugins (and thus finalize_push) completed** inside the second final_finish run. **Targeted sweeps and final multi-model** were started; when we last checked, only one targeted sweep dir existed (`flow_x_0.5`), so the remainder of the pipeline may still be running or output may be buffered.

---

## Completed Artifacts (Verified)

### Push-with-plugins run: `push_with_plugins_20260223T003321Z`

- **Paper overlay** applied: `configs/overlays/paper_lock_overlay.json` (min_exec_score=1.8, shadow_min_exec_score=1.5) copied to run patches.
- **Evidence bundle** built from base run `alpaca_monday_final_20260222T174120Z` (backtest_summary, backtest_trades, uw_flow_cache, uw_expanded_intel, metrics).
- **Multi-model adversarial** ran with prosecutor, defender, SRE, board; outputs copied to `multi_model/`.
- **Board verdict:** **ACCEPT** — run produced trades; governance and artifacts complete.
- **Customer advocate** and **PROMOTION_CANDIDATES** generated/copied into the run dir and evidence.

### Finalize_push run: `finalize_push_20260223T003322Z`

- **Exec sensitivity:** No pre-existing exec_sensitivity summary was found in the follow-up dir, so the script reported “consider re-running exec sensitivity separately.” No re-run was triggered in this pass.
- **Exit sweep:** Best-effort MFE/MAE from baseline trades was computed and written to `exit_sweep/exit_sweep_summary.json`:
  - **Status:** `computed_from_trades`
  - **MFE:** `count: 0`, `mean: null`
  - **MAE:** `count: 0`, `mean: null`  
  (Baseline trades do not contain `exit_quality_metrics.mfe_pct` / `mae_pct`, so no MFE/MAE could be derived.)
- **Targeted sweeps:** Started; at least `targeted_sweeps/flow_x_0.5` was present. Remaining sweeps (other signals and multipliers) may still be running or pending.

### Baseline (canonical)

- **Run:** `alpaca_monday_final_20260222T174120Z`
- **Metrics:** net_pnl **$18,811.44**, trades_count **10,715**, win_rate_pct **51.18%** (5,484 wins / 5,123 losses).

---

## Local Copies of Key Artifacts

Fetched from droplet into `reports/final_finish_artifacts/`:

- `run_meta.txt` (finalize_push RUN_ID)
- `exit_sweep_summary.json` (MFE/MAE from trades; 0 counts)
- `baseline_metrics.json` (Monday final baseline)
- `final_finish_run_meta.txt` (final_finish RUN_ID + FOLLOWUP_DIR)
- `push_with_plugins.log` (push_with_plugins/finalize/multi-model copy log)
- `board_verdict.md` (ACCEPT; from push_with_plugins multi_model run)

---

## Fix Applied for Future Runs

- **Executable bit:** Scripts were made executable on the droplet for this run. **In the repo**, `git update-index --chmod=+x` was run for:
  - `scripts/run_final_finish_on_droplet.sh`
  - `scripts/run_push_with_plugins_on_droplet.sh`
  - `scripts/run_finalize_push_on_droplet.sh`  
  So after the next pull, the scripts should be executable and the first final_finish run should not hit “script missing” (the failure was due to `-x` check, not missing file).

---

## What to Do Next

1. **If the droplet is still running final_finish:** Check `/tmp/final_finish_run.log` and `reports/backtests/finalize_push_20260223T003322Z/` for:
   - More `targeted_sweeps/*` dirs (flow_x_0.75, flow_x_1.0, dark_pool_x_*, freshness_factor_x_*).
   - `multi_model/out_final/` and `multi_model/board_verdict.md` (final multi-model run).
   - `PROMOTION_CANDIDATES.md` and `ARTIFACT_INDEX.md` under `finalize_push_20260223T003322Z/`.
2. **Exec sensitivity:** To get slippage sensitivity, run exec sensitivity separately (e.g. `run_finalize_push_on_droplet.sh` or the exec-sensitivity block in `run_final_finish_on_droplet.sh`) so that an `exec_sensitivity/exec_sensitivity.json` exists in the follow-up dir before or during final_finish.
3. **MFE/MAE:** For real exit sweep MFE/MAE, either:
   - Emit `exit_quality_metrics` (mfe_pct, mae_pct) on each trade in the simulation/backtest, or
   - Implement a full exit optimization that computes MFE/MAE from bar data and write `exit_sweep_summary.json` accordingly.
4. **Commit and push** the executable-bit change for the three scripts so future droplet pulls get executable scripts by default.

---

## One-Line Summary

**Droplet run executed:** push_with_plugins and finalize_push completed; multi-model board verdict **ACCEPT**; baseline **$18,811 net PnL, 10,715 trades, 51.18% win rate**; exit_sweep MFE/MAE computed from trades (0 values — no exit_quality_metrics on baseline); targeted sweeps and final multi-model started (at least one sweep dir present; rest may still be running). Scripts set executable on droplet and in git for future runs.
