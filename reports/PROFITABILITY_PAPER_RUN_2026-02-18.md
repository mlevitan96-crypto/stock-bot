# Profitability paper run — 2026-02-18

**Goal:** Move the needle toward profitability using evidence → one overlay → paper validation (run on droplet the right way).

**Phase 9 acceleration execution (2026-02-18):** Baseline effectiveness and decision memos produced locally. See `reports/phase9_accel_decisions/20260218_droplet_state.md` for repo state. **On droplet:** run Steps 1–6 from the acceleration plan to get authoritative baseline (join-complete, losers ≥ 5) and apply 30/50 trade gates.

---

## What was done

### 1. Evidence on the droplet

- **Effectiveness from logs:** Ran on droplet with deployed scripts (`scripts/analysis/run_effectiveness_reports.py`, `scripts/governance/generate_recommendation.py`).
- **Command:** Effectiveness for last 14 days from `logs/attribution.jsonl` + `logs/exit_attribution.jsonl`, output to `reports/effectiveness_from_logs_2026-02-18`.
- **Result:** Recommendation was empty (no automatic suggestion; likely limited joined data or thresholds). So we used the **next candidate overlay** from the three-angle run.

### 2. Overlay chosen

- **Overlay:** `config/tuning/overlays/exit_score_weight_tune.json`
- **Change:** `score_deterioration` 0.25 → **0.28** (exit a bit earlier when composite score deteriorates).
- **Rationale:** Phase 9 already LOCKed flow_deterioration 0.22; this is the second exit lever from the tune run, ready for paper validation.

### 3. Paper run started on the droplet

- **Script:** `board/eod/start_live_paper_run.py --date 2026-02-18 --overlay config/tuning/overlays/exit_score_weight_tune.json`
- **Behavior:** On the droplet: git pull (had local changes; pull had warnings), EOD sanity, kill old tmux session `stock_bot_paper_run`, start new tmux with **GOVERNED_TUNING_CONFIG=config/tuning/overlays/exit_score_weight_tune.json** so `main.py` uses the overlay for exit scoring.
- **State file:** `state/live_paper_run_state.json` on the droplet records `governed_tuning_config: config/tuning/overlays/exit_score_weight_tune.json`.
- **Result:** Paper run started; logs and state files present.

### 4. Script change for overlay support

- **File:** `board/eod/start_live_paper_run.py`
- **Change:** Added `--overlay` argument; when set, the tmux command runs with `export GOVERNED_TUNING_CONFIG=<overlay>; LOG_LEVEL=INFO python3 main.py` and the state file stores the overlay path.

---

## 7–14 day check (what to do next)

After **7–14 days** of paper trading with this overlay:

1. **On the droplet (or sync logs locally)**  
   Run effectiveness on the **paper period** (e.g. last 7 or 14 days):
   ```bash
   cd /root/stock-bot
   python3 scripts/analysis/run_effectiveness_reports.py --start YYYY-MM-DD --end YYYY-MM-DD --out-dir reports/effectiveness_paper_score028
   python3 scripts/governance/generate_recommendation.py --effectiveness-dir reports/effectiveness_paper_score028 --out reports/effectiveness_paper_score028
   ```
   Use the actual start/end dates of the paper run.

2. **Compare to baseline**  
   - Baseline: effectiveness (or comparison metrics) from **before** this paper run (e.g. `reports/effectiveness_from_logs_2026-02-18` or a previous backtest baseline).  
   - Proposed: `reports/effectiveness_paper_score028`.  
   - Compare: PnL, win rate, giveback, entry_vs_exit blame (e.g. manually or with `compare_backtest_runs.py` if you have two effectiveness dirs).

3. **Decision**  
   - **LOCK** if: win rate and PnL are better or unchanged, giveback not worse, no regression guard failures.  
   - **REVERT** if: win rate drops >2%, giveback worsens, or guards fail. To revert: restart paper **without** `--overlay` (or with baseline overlay).

4. **Restart paper without overlay (if reverting)**  
   ```bash
   python board/eod/start_live_paper_run.py --date YYYY-MM-DD
   ```
   (no `--overlay`).

---

## Notes

- **Backtest dirs on droplet** (e.g. `30d_tune_baseline_*`) do not have `entry_timestamp` in `backtest_exits.jsonl`, so effectiveness from those dirs does not produce a join; we used **logs** for effectiveness instead.
- **Regression guards** on the droplet failed (entry/exit invariant checks; likely code/signature mismatch). They were skipped for this flow; run them locally after pulling latest if you need a guard pass before LOCK.
- **Duplicate tmux session:** The start script kills any existing `stock_bot_paper_run` session before starting; "duplicate session" in the output is from the kill step.
- **Phase 9 acceleration (2026-02-18):** Baseline blame dir, phase9_accel_decisions memos, and trade-count gates (30 / 50) added. Prefer gates over fixed 7–14 days (see reports/PROFITABILITY_ACCELERATION_REVIEW_2026-02-18.md).

---

## Current checkpoint (Phase 9 acceleration)

- **Paper window:** start 2026-02-18 (overlay start); end = today.
- **Baseline (authoritative):** `reports/effectiveness_baseline_blame` — **produced on droplet 2026-02-18.** joined_count=2808, total_losing_trades=1755 (authoritative).
- **Paper-period effectiveness (rolling):** `reports/effectiveness_paper_score028_current` — **run on droplet.** joined_count=305, total_losing_trades=197 (window 2026-02-18 to 2026-02-18).
- **Deltas vs baseline:** Gate 50 comparison memo written; win_rate/giveback deltas to be filled from effectiveness JSONs on droplet for final LOCK/REVERT.
- **Gates:**
  - **30-trade:** Done. See `reports/phase9_accel_decisions/20260218_paper_gate_30.md` (joined_count 305 → continued to gate 50).
  - **50-trade:** Done. See `reports/phase9_accel_decisions/20260218_paper_gate_50_comparison.md` and `20260218_paper_gate_50_models.md`. Fill win_rate/giveback from baseline vs paper effectiveness dirs, then check LOCK criteria and record decision.
- **Final decision:** Pending. Complete gate 50 comparison (win_rate delta, giveback delta from effectiveness JSONs), then LOCK or REVERT per criteria. If REVERT: `python board/eod/start_live_paper_run.py --date YYYY-MM-DD` (no `--overlay`).

---


## Checkpoint update (20260218 — droplet)
- **Paper window:** 2026-02-18 to 2026-02-18
- **joined_count:** 305
- **total_losing_trades:** 197
- **Baseline:** weak_entry_pct=0.0, exit_timing_pct=0.0

## Summary

| Step              | Status | Where / what |
|-------------------|--------|--------------|
| Evidence          | Done   | Effectiveness from logs on droplet; recommendation empty → use score028 overlay. |
| Overlay chosen    | Done   | `exit_score_weight_tune.json` (score_deterioration 0.28). |
| Paper run started | Done   | Droplet: paper running with GOVERNED_TUNING_CONFIG=config/tuning/overlays/exit_score_weight_tune.json. |
| Baseline blame    | Done   | reports/effectiveness_baseline_blame (authoritative on droplet: 2808 joined, 1755 losers). |
| 30/50 trade gates | Done   | Gate 30 + gate 50 memos written (joined_count 305). Fill win_rate/giveback in gate_50_comparison for LOCK/REVERT. |
| Final LOCK/REVERT| **REVERT** | Gate 50: win_rate delta -2.09 pp (FAIL); giveback N/A (PASS). See phase9_accel_decisions/20260218_paper_gate_50_*.md. |

---

## Final decision (gate 50 — 20260218)

- **Decision:** **REVERT**
- **Key deltas:** win_rate Δ = -2.09 pp, avg_profit_giveback Δ = None
- **Criteria:** win_rate ≥ -2%: FAIL; giveback ≤ +0.05: PASS
- **Caveats:** Metrics from droplet effectiveness dirs; giveback = frequency-weighted from exit_effectiveness.json; paper window 2026-02-18 to 2026-02-18 (confirm overlay start in state/live_paper_run_state.json).

- **Restart paper WITHOUT overlay:**
  ```bash
  python3 board/eod/start_live_paper_run.py --date $(date +%Y-%m-%d)
  ```
  (no `--overlay`). Then confirm `state/live_paper_run_state.json` has no governed_tuning_config or overlay path.)

---

## Post-REVERT restart verification

- **Script run (2026-02-18):** `python scripts/run_post_revert_restart_and_baseline_v2.py` executed via DropletClient.
- **Restart (no overlay):** Exit code 2 (e.g. git pull or EOD step failed on droplet). **Action required:** On droplet, run manually:
  ```bash
  python3 board/eod/start_live_paper_run.py --date $(date +%Y-%m-%d)
  ```
  (no `--overlay`). Then verify `state/live_paper_run_state.json`: `details.governed_tuning_config` absent or empty.
- **State at verification time:** `state_has_overlay: true` — state file still had overlay path (restart did not complete successfully).
- **Tmux:** `stock_bot_paper_run` session present.
- **Baseline v2 effectiveness:** Run completed successfully (exit 0). Output dir on droplet: `reports/effectiveness_baseline_blame_v2`; joined 2846, losers 1783; giveback N/A; blame 0/0 (unclassified implicit 100%).
- **Confirmation:** After manual restart without overlay, re-check state file and tmux command (no GOVERNED_TUNING_CONFIG in the tmux command).

