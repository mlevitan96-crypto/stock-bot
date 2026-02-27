# Change Proposal: [TITLE]

**Change ID:** `[e.g. exit_flow_weight_20260217]`  
**Date:** YYYY-MM-DD  
**Author:**  
**Status:** draft | in_review | approved | applied | reverted

---

## 1. What is changing (exact config diff)

Describe the exact parameter(s) and before/after values. Prefer showing the tuning overlay (e.g. `config/tuning/active.json` or a named overlay).

**Before (baseline):**
```json
{
  "exit_weights": {
    "flow_deterioration": 0.20
  }
}
```

**After (proposed):**
```json
{
  "exit_weights": {
    "flow_deterioration": 0.22
  }
}
```

**Files touched:** e.g. `config/tuning/active.json` or `GOVERNED_TUNING_CONFIG=config/tuning/proposed_xxx.json`

---

## 2. Why (Phase 5 evidence)

Which Phase 5 metrics justify this change? Reference reports (signal_effectiveness, exit_effectiveness, entry_vs_exit_blame, counterfactual_exit).

- **Source report:** e.g. `reports/effectiveness_2026-02-17/signal_effectiveness.json` or `exit_effectiveness.json`
- **Observation:** e.g. "exit.flow_deterioration exits have 12% higher avg_profit_giveback than average; increasing weight slightly to exit earlier when flow deteriorates."
- **Evidence snippet:** (paste relevant metric or table row)

---

## 3. Expected impact

Which metrics should **improve** after this change?

| Metric | Expected direction | How to measure |
|--------|--------------------|----------------|
| e.g. avg_profit_giveback for profit exits | Decrease | Compare before/after effectiveness report |
| e.g. win_rate | Maintain or improve | Backtest comparison |

---

## 4. Falsification criteria

What would **prove this change failed**? (So we can revert.)

- e.g. "If win_rate drops by more than 2% in the next 7 days of paper trading."
- e.g. "If exit_quality_metrics.avg_profit_giveback increases by more than 0.05."
- e.g. "If regression guards fail (attribution invariant or exit quality check)."

---

## 5. Rollback

- **How to revert:** Remove overlay or restore previous `config/tuning/active.json`; restart (or set `GOVERNED_TUNING_CONFIG` to baseline).
- **Verification:** Re-run effectiveness report and regression guards on same data.

---

## 6. Before/after backtest comparison (attach or link)

- Baseline run: `reports/effectiveness_baseline_YYYY-MM-DD/` or backtest dir
- Proposed run: `reports/effectiveness_proposed_YYYY-MM-DD/` or backtest dir
- Comparison artifact: output of `scripts/governance/compare_backtest_runs.py`
