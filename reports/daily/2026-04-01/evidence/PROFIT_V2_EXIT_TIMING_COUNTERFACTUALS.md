# PROFIT_V2_EXIT_TIMING_COUNTERFACTUALS
- **Exit rows:** 432
- **Replay rows written:** 432
- **Skipped:** `{}`
- **Bars symbols loaded:** 49

## Horizon definitions
Mark-to-market PnL at first 1Min bar at or after entry + offset (long: (px-entry)*qty; short: (entry-px)*qty).

## Aggregate: horizon PnL minus realized (same trade, n=432)

Mechanistic mark-to-market; not an executable exit policy.

| Horizon | Mean (horizon_pnl - realized_pnl) USD |
|---------|---------------------------------------|
| +1m | -0.0490 |
| +5m | -0.0484 |
| +15m | -0.0116 |
| +30m | -0.0247 |
| +60m | +0.1517 |

Interpretation: on average, **early** (+1m–+30m) marks are slightly **below** realized exit PnL; **+60m** is slightly **above**. This is descriptive only (path-dependent, no fill model).
