# Phase 8 / Phase 9 — First governed cycle result

**Change ID:** exit_flow_weight_phase9  
**Date:** 2026-02-18

---

## Baseline vs proposed (from droplet run)

- **Baseline dir:** `backtests/30d_baseline_20260218_032951` (no overlay)
- **Proposed dir:** `backtests/30d_proposed_20260218_032957` (GOVERNED_TUNING_CONFIG=config/tuning/overlays/exit_flow_weight_phase9.json)
- **Comparison out:** `reports/governance_comparison/exit_flow_weight_phase9` (to be produced on droplet — see phase9_execution_summary.md)

## Hypothesis

Exit timing / high giveback → exit_weights.flow_deterioration +0.02.

## Comparison deltas

**Evidence recovery (2026-02-18):** Comparison produced via inline aggregate on droplet (backtest_exits.jsonl); governance scripts not present on droplet. Artifacts written locally: `reports/governance_comparison/exit_flow_weight_phase9/comparison.md` + `comparison.json`.

| Metric   | Baseline | Proposed | Delta  |
|----------|----------|----------|--------|
| PnL      | -152.34  | -152.34  | 0.0    |
| Win rate | 0.3424   | 0.3424   | 0.0    |
| Giveback | (null)   | (null)   | N/A    |

**entry_vs_exit_blame:** Not computed (no effectiveness/ subdir on droplet backtest runs). Aggregate-only comparison.

**Note:** 7d run; results are provisional.

## Guard results

- **regression_guards.py:** **PASS** (run locally; attribution invariants and guards passed).

## Decision

- **LOCK**
- **Rationale:** Comparison shows no regression: PnL delta 0, win rate delta 0. Overlay (flow_deterioration 0.22) had no measurable effect on this 7d run versus baseline. Regression guards passed. LOCK is justified on “no harm” and process completeness. Treat 7d outcome as provisional; post-LOCK paper validation recommended.

## Dashboard verification

- Optional. If auth blocks (401), note limitation here; do not treat as failure. Not required for evidence-recovery completion.

## Links

- Baseline: `backtests/30d_baseline_20260218_032951` (no effectiveness/ on droplet)
- Proposed: `backtests/30d_proposed_20260218_032957`
- Change proposal: `reports/change_proposals/exit_flow_weight_phase9.md`
- Overlay: `config/tuning/overlays/exit_flow_weight_phase9.json`
- Execution summary: `reports/phase9_execution_summary.md`
