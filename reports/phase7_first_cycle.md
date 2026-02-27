# Phase 7 — First governed tuning cycle

**Date:** 2026-02-18  
**Status:** Template / one-time execution log.

## 4.1 Generate baseline effectiveness (last 30d)

**Command:**
```bash
python scripts/analysis/run_effectiveness_reports.py --backtest-dir backtests/<latest_30d_dir> --out-dir reports/effectiveness_baseline
```
Or from logs:
```bash
python scripts/analysis/run_effectiveness_reports.py --start 2026-01-18 --end 2026-02-18 --out-dir reports/effectiveness_baseline
```

**Output:** `reports/effectiveness_baseline/signal_effectiveness.json`, `exit_effectiveness.json`, `entry_vs_exit_blame.json`, `counterfactual_exit.json`.

## 4.2 Pick ONE hypothesis (smallest change)

Based on baseline numbers (fill after running):

- If **exit_timing_pct** is high and profit exits show high giveback → increase one exit weight (e.g. flow_deterioration +0.02).
- If one UW micro-signal has **low win_rate + high MAE** → reduce its weight or raise entry threshold.

**Chosen hypothesis:** _e.g. "Exit timing dominates; increase exit_weights.flow_deterioration by 0.02"._

## 4.3 Create change proposal + overlay

- Proposal: `reports/change_proposals/<change_id>.md` (use `docs/templates/change_proposal.md`).
- Overlay: `config/tuning/overlays/<change_id>.json` (e.g. `{"version": "...", "exit_weights": {"flow_deterioration": 0.22}}`).

## 4.4 Run baseline vs proposed backtest compare + guards

```bash
# Run baseline backtest (no overlay), then proposed (GOVERNED_TUNING_CONFIG=config/tuning/overlays/<change_id>.json)
python scripts/governance/compare_backtest_runs.py --baseline backtests/baseline_dir --proposed backtests/proposed_dir --out reports/governance_comparison/<change_id>
python scripts/governance/regression_guards.py
```

**Output:** `reports/governance_comparison/<change_id>/comparison.md`, `comparison.json`. Decision: lock overlay if comparison improves and guards pass; else revert.

## 4.5 Paper/canary plan (document only)

Add `reports/change_proposals/<change_id>_paper_plan.md`:

- Duration (e.g. 7 days)
- Symbols / scope (e.g. all equity)
- Rollback trigger (e.g. win rate drop >2%, or guards fail)
- Metrics to watch (win_rate, avg_profit_giveback, PnL)

---

**First cycle result (fill after execution):**

- Baseline metrics: _…_
- Hypothesis: _…_
- Comparison result: _improved / no material change / regressed_
- Decision: _lock / revert_
