# Weekly Review — Risk Officer
**Date:** 2026-03-06

## 3 strongest findings
1. Executed count 0 in 7d; blocked 0 — concentration and max_positions pressure inferred from board review.
2. Board review blocked_trade_distribution and counter_intelligence (if present) inform downside of current gating.
3. No real-money exposure; paper/live paper only — tail risk is operational and reputational.

## 3 biggest risks
1. Regime shift (vol spike, drawdown) without regime-specific sizing or pause.
2. Concentration in single name or sector if universe narrows.
3. Displacement blocks masking opportunity cost; unknown correlation of blocked vs. would-be losers.

## 3 recommended actions (ranked)
1. Add regime tag to ledger events where available; report concentration by symbol/sector in summary.
2. Require risk sign-off before B2 live paper or real money; document max drawdown and position limits.
3. Track tail scenarios (e.g. 2σ move) in backtest or shadow before enabling larger size.

## What evidence would change my mind?
Concentration and regime metrics in the ledger; explicit max_positions and displacement block counts; and a risk checklist for real-money readiness.
