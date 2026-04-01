# ALPACA_PROFIT_ACTION_PLAN

## Ranked actions

### Rank 1: Shadow-test direction filter per regime
- **expected_impact:** Reduce drawdown if one direction is systematically negative in specific regimes
- **risk:** Miss winners; sample split instability
- **confidence:** LOW-MEDIUM (tail-only evidence)
- **verification:** 30d shadow ledger; compare realized vs baseline per regime cell
- **rollback:** Disable shadow flag; no production gate

### Rank 2: Replay exit timing with bars artifact
- **expected_impact:** Quantify minute-level opportunity cost vs realized
- **risk:** Look-ahead if bars misaligned
- **confidence:** MEDIUM when bars present
- **verification:** Run replay_exit_timing_counterfactuals; compare distributions
- **rollback:** Discard scenario JSON changes

### Rank 3: Deepen blocked-trade forward PnL lab
- **expected_impact:** Estimate opportunity cost of gates
- **risk:** Survivorship in manual labels
- **confidence:** LOW without price path
- **verification:** Replay blocked symbols with stored bars
- **rollback:** N/A read-only

### Rank 4: Prune or downweight low-delta signals (from ranking tail)
- **expected_impact:** Lower noise; faster decisions
- **risk:** Remove hidden nonlinear value
- **confidence:** LOW (median split ≠ causal)
- **verification:** Shadow portfolio with component ablation
- **rollback:** Restore weights from git

