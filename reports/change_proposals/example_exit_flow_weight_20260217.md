# Change Proposal: Slight increase in exit flow_deterioration weight

**Change ID:** `example_exit_flow_weight_20260217`  
**Date:** 2026-02-17  
**Author:** Phase 6 example  
**Status:** draft

---

## 1. What is changing (exact config diff)

**Before (baseline):** built-in `exit_score_v2.EXIT_WEIGHTS.flow_deterioration = 0.20`

**After (proposed):** overlay sets `exit_weights.flow_deterioration = 0.22`

**Overlay file:** `config/tuning/examples/exit_flow_weight_plus_0.02.json`

```json
{
  "version": "2026-02-17_exit_flow_plus_0.02",
  "exit_weights": {
    "flow_deterioration": 0.22
  }
}
```

**Apply:** Copy to `config/tuning/active.json` or set `GOVERNED_TUNING_CONFIG=config/tuning/examples/exit_flow_weight_plus_0.02.json`

---

## 2. Why (Phase 5 evidence)

- **Source report:** `reports/effectiveness_<date>/exit_effectiveness.json` (or from backtest effectiveness subdir)
- **Observation:** Exits with high flow_deterioration component show higher avg_profit_giveback; slight weight increase may encourage earlier exit when flow deteriorates and reduce giveback.
- **Evidence snippet:** (fill from your exit_effectiveness report, e.g. profit exits with flow_deterioration contribution > 0.15 and avg_profit_giveback)

---

## 3. Expected impact

| Metric | Expected direction | How to measure |
|--------|--------------------|----------------|
| avg_profit_giveback (profit exits) | Decrease | Phase 5 exit_effectiveness report |
| win_rate | Maintain or improve | Backtest comparison |
| PnL | Maintain or improve | Backtest comparison |

---

## 4. Falsification criteria

- Win rate drops by more than 2% over 7 days paper vs baseline.
- avg_profit_giveback increases by more than 0.05.
- Regression guards fail (attribution invariant or exit quality).

---

## 5. Rollback

- Remove overlay or restore previous `config/tuning/active.json`; or unset `GOVERNED_TUNING_CONFIG`.
- Re-run regression guards and effectiveness report on same data.

---

## 6. Before/after backtest comparison

- Baseline run: (your baseline effectiveness dir or backtest dir)
- Proposed run: (your proposed run with overlay applied)
- Comparison: `python scripts/governance/compare_backtest_runs.py --baseline <baseline> --proposed <proposed> --out reports/governance_comparison`
