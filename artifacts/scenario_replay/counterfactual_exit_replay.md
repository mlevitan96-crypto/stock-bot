# Counterfactual exit timing replay (exit-only)

## Baseline realized exits (as logged)

| bucket | pnl | exits |
|---|---:|---:|
| UNKNOWN:UNKNOWN | -280.39 | 2578 |

## Scenario results (counterfactual P&L model)

### baseline_current

No additional hold floor; preserve existing behavior (control).

| bucket | pnl | exits | rows_used | rows_skipped |
|---|---:|---:|---:|---:|
| UNKNOWN:UNKNOWN | -823.23 | 156 | 156 | 2422 |

### live_50pct_push

Mild anti-churn: slightly longer holds + slightly reduced decay/displacement sensitivity.

| bucket | pnl | exits | rows_used | rows_skipped |
|---|---:|---:|---:|---:|
| UNKNOWN:UNKNOWN | -823.23 | 156 | 156 | 2422 |

### paper_150pct_push

Meaningful patience: multi-hour holds; materially reduced decay/displacement sensitivity.

| bucket | pnl | exits | rows_used | rows_skipped |
|---|---:|---:|---:|---:|
| UNKNOWN:UNKNOWN | -823.23 | 156 | 156 | 2422 |

### shadow_250pct_push

Aggressive exploration: long holds (24h default) and very low decay/displacement sensitivity.

| bucket | pnl | exits | rows_used | rows_skipped |
|---|---:|---:|---:|---:|
| UNKNOWN:UNKNOWN | -823.23 | 156 | 156 | 2422 |

### shadow_3day_hold

Explicit 72h hold exploration for longer-horizon mean reversion / drift capture.

| bucket | pnl | exits | rows_used | rows_skipped |
|---|---:|---:|---:|---:|
| UNKNOWN:UNKNOWN | -823.23 | 156 | 156 | 2422 |

### bear_regime_patience

Regime-aware: in BEAR, require longer holds (helps avoid chopping mean reversion).

| bucket | pnl | exits | rows_used | rows_skipped |
|---|---:|---:|---:|---:|
| UNKNOWN:UNKNOWN | -823.23 | 156 | 156 | 2422 |

## Skips (why rows could not be replayed)

- **missing_bars_for_symbol:** 14370
- **missing_entry_or_exit_fields:** 108
- **no_bar_after_target_exit:** 54
