# ALPACA_PROFIT_DISCOVERY_FINAL_VERDICT

- **Structurally profitable (tail, realized sum > 0, n≥20)?** **YES**
  - sum_pnl LONG+SHORT in tail ≈ **+11.40 USD**, n ≈ **432** (full `exit_attribution.jsonl` on droplet at run time; tail = full file)

- **If NO:** losses concentrated per exit-reason buckets and/or negative expectancy direction; **not** proven "broken" without full history and holdout.

- **Shortest path to profitability:** improve **exit timing replay** (bars) + **gate opportunity lab** (blocked forward path) + **shadow ablation** on bottom-ranked signals.

- **First shadow experiment:** Shadow direction/regime gate with paper-only sizing; log counterfactual entry/exit from same signals; compare 30d to baseline without changing live gates.

## Evidence index

- `ALPACA_PROFIT_INTEL_DATA_INVENTORY.md`
- `ALPACA_DIRECTIONAL_PNL_ANALYSIS.md`
- `ALPACA_SIGNAL_CONTRIBUTION_MATRIX.md` + `ALPACA_SIGNAL_RANKING.json`
- `ALPACA_EXIT_CAUSAL_ANALYSIS.md`
- `ALPACA_TIME_COUNTERFACTUALS.md`
- `ALPACA_BLOCKED_MISSED_INTEL.md`
- `ALPACA_SPI_ORTHOGONALITY_ANALYSIS.md`
- `ALPACA_PROFIT_WHY_SYNTHESIS.md`
- `ALPACA_PROFIT_ACTION_PLAN.md` + `.json`
- Board: `BOARD_*_PROFIT_VERDICT.md`

