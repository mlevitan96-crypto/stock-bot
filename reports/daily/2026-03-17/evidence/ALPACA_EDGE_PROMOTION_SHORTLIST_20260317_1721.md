# Alpaca edge promotion shortlist (mechanism-level)

- **Source:** alpaca_edge_2000_20260317_1721

## Mechanism-level candidates

- **Entry score threshold:** See studies/entry_weight_threshold_sweeps/sweep.csv; rank by mean_pnl stability.
- **Exit component / pressure:** See studies/exit_component_sweeps; rank by winner expectancy.
- **Gate effectiveness:** See studies/gate_effectiveness; protective gates = high pass_total_pnl, low fail_total_pnl.
- **Hold-duration / signal-score:** See studies/hold_duration_surfaces, signal_score_gating (legacy).

## Classification

- **PROMOTABLE (paper-only):** Only if CSA APPROVE and mechanism-level evidence (entry/exit/gate studies) supports.
- **PAPER-ONLY CANDIDATE:** Entry threshold, exit pressure, or gate effectiveness with stable expectancy.
- **RESEARCH-ONLY:** Regime-conditioned policies; stability TBD.
- **DISCARD:** No candidate discarded by default.
