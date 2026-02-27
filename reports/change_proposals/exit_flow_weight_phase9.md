# Change Proposal: First governed cycle — exit flow_deterioration +0.02

**Change ID:** `exit_flow_weight_phase9`  
**Date:** 2026-02-18  
**Author:** Phase 9 first cycle  
**Status:** draft → fill Section 2 after Step 2 (baseline); update cited metrics after Step 5 (decision)

**Runbook:** reports/phase9_droplet_runbook.md (Steps 1–7)

---

## 1. What is changing (exact config diff)

**Before (baseline):** built-in `exit_score_v2.EXIT_WEIGHTS.flow_deterioration = 0.20`

**After (proposed):** overlay sets `exit_weights.flow_deterioration = 0.22`

**Overlay file:** `config/tuning/overlays/exit_flow_weight_phase9.json`

```json
{
  "version": "2026-02-18_phase9_exit_flow_plus_0.02",
  "exit_weights": {
    "flow_deterioration": 0.22
  }
}
```

**Apply:** Set `GOVERNED_TUNING_CONFIG=config/tuning/overlays/exit_flow_weight_phase9.json` for proposed backtest only. Do not auto-apply to live.

---

## 2. Why (Phase 5/7 evidence)

- **Baseline path:** `backtests/30d_baseline_20260218_032951` (no overlay)
- **Proposed path:** `backtests/30d_proposed_20260218_032957` (overlay `exit_flow_weight_phase9.json`)
- **Comparison artifact:** `reports/governance_comparison/exit_flow_weight_phase9/comparison.md` + `comparison.json`
- **Cited metrics (7d run):** total_pnl_usd baseline -152.34 / proposed -152.34 (delta 0); win_rate 0.3424 both (delta 0); total_trades 1618 both. entry_vs_exit_blame not computed (no effectiveness/ on droplet).
- **Final decision:** LOCK — see `reports/phase8_first_cycle_result.md`. No regression; overlay had no measurable effect on this provisional 7d run; guards passed.

---

## 3. Expected impact

| Metric | Expected direction | How to measure |
|--------|--------------------|----------------|
| avg_profit_giveback (profit exits) | Decrease | compare_backtest_runs → effectiveness |
| win_rate | Maintain or improve | comparison.md |
| PnL | Maintain or improve | comparison.md |

---

## 4. Falsification criteria

- Win rate drops by more than 2% (vs baseline) in comparison.
- avg_profit_giveback increases by more than 0.05.
- Regression guards fail (attribution invariant or exit quality).

---

## 5. Rollback

- **How to revert:** Do not set GOVERNED_TUNING_CONFIG (or set to empty). Re-run backtest without overlay.
- **Verification:** compare_backtest_runs baseline vs reverted; regression_guards.py.

---

## 6. Before/after backtest comparison

- **Baseline run:** _e.g. `backtests/30d_baseline_YYYYMMDD_HHMMSS`_
- **Proposed run:** _e.g. `backtests/30d_proposed_YYYYMMDD_HHMMSS`_ (with GOVERNED_TUNING_CONFIG=config/tuning/overlays/exit_flow_weight_phase9.json)
- **Comparison artifact:** `python scripts/governance/compare_backtest_runs.py --baseline <baseline_dir> --proposed <proposed_dir> --out reports/governance_comparison/exit_flow_weight_phase9`
- **Output:** `reports/governance_comparison/exit_flow_weight_phase9/comparison.md` + `comparison.json`
