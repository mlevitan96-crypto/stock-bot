# Phase 9 acceleration — Gate 50 multi-model (droplet)
**Date:** 20260218

## Adversarial
- **Recommendation:** REVERT
- **Why this could be wrong:** Sample may be regime-specific; one-day paper window (2026-02-18) may not represent future. Variance in 305 trades.
- **Verify:** (1) Paper window is overlay start → end (confirm state file). (2) Same metric definitions for baseline vs paper. (3) Next 50 trades or next week re-check.

## Quant
- **Recommendation:** REVERT
- **Why this could be wrong:** 305 trades gives ~2.8% SE on win_rate; small deltas could be noise. Giveback weighted by exit mix.
- **Verify:** (1) Win-rate delta within sampling error. (2) Giveback computed identically for both dirs. (3) Blame percentages from JSON (not summary) if used later.

## Product
- **Recommendation:** REVERT
- **Why this could be wrong:** Operators may treat LOCK as permanent; overlay may need re-validation.
- **Verify:** (1) State file reflects overlay. (2) Paper run doc has exact restart command if REVERT. (3) Post-LOCK validation planned.

## Final committee decision
- **FINAL: REVERT**
- **Rationale:** Criteria win_rate Δ ≥ -2% and giveback Δ ≤ +0.05: win_rate FAIL, giveback PASS. Risks acknowledged; verification checks above.
