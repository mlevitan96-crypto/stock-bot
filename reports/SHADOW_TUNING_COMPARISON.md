# Shadow Tuning Comparison

**Generated:** paper simulation only. NOT LIVE — no trading logic or config changed.

## Profile results (hypothetical PnL vs baseline)

| Profile | Hypothetical PnL (USD) | Δ vs baseline |
|---------|-------------------------|--------------|
| baseline | -23.64 | +0.00 |
| relaxed_displacement | -23.64 | +0.00 |
| higher_min_exec_score | -23.64 | +0.00 |
| exit_tighten | -23.64 | +0.00 |

## Summary

- **Best expectancy (hypothetical):** baseline (PnL -23.64 USD)

- **Relaxed displacement:** Adds counterfactual PnL from blocked trades; improves if blocks were costly.
- **Higher MIN_EXEC_SCORE:** Fewer trades (not simulated here); compare baseline vs fewer-entry scenario separately.
- **Exit tighten:** Adds heuristic savings from reduced left-on-table; improves if exits were late.

## NOT LIVE YET

Any config change (displacement, MIN_EXEC_SCORE, trailing-stop, time-exit) must be:
- CONFIG ONLY,
- DISABLED by default,
- Documented and applied only after human review.
