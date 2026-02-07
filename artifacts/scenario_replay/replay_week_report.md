# Scenario replay week report (diagnostics-only)

## Baseline realized exits by mode:strategy

| bucket | pnl | exits | wins | losses | win_rate |
|---|---:|---:|---:|---:|---:|
| UNKNOWN:UNKNOWN | 63000.00 | 35 | 14 | 0 | 0.400 |

## Scenarios defined

- **baseline_current:** No additional hold floor; preserve existing behavior (control).
- **live_50pct_push:** Mild anti-churn: slightly longer holds + slightly reduced decay/displacement sensitivity.
- **paper_150pct_push:** Meaningful patience: multi-hour holds; materially reduced decay/displacement sensitivity.
- **shadow_250pct_push:** Aggressive exploration: long holds (24h default) and very low decay/displacement sensitivity.
- **shadow_3day_hold:** Explicit 72h hold exploration for longer-horizon mean reversion / drift capture.
- **bear_regime_patience:** Regime-aware: in BEAR, require longer holds (helps avoid chopping mean reversion).

## What's missing for full counterfactual replay

- A canonical replay runner that can re-simulate exits using historical price/position timelines.
- A retained market data timeline (bars/quotes) or an internal price cache used at decision-time.
- A retained position timeline (entry time, size, symbol, mode, strategy, regime) to apply hold floors.
