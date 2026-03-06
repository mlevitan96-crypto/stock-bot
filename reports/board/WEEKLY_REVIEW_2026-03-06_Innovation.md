# Weekly Review — Innovation (Crazy Angles)
**Date:** 2026-03-06

## 3 strongest findings
1. Current pipeline is stock-only; options/wheel could capture theta or hedge delta.
2. Universe and regime are levers; time-of-day and volatility regime switching under-explored.
3. Radical simplification (kill weak signals, single exit rule) could improve clarity and reduce leakage.

## 3 biggest risks
1. Pivoting to options before stock edge is proven adds complexity and cost.
2. Structural changes (universe, time gating) may invalidate existing backtests.
3. Over-simplification could remove the only edge we have.

## 3 recommended actions (ranked)
1. Complete pivot analysis (stocks vs options/wheel) with evidence; stay course unless bottleneck is structural.
2. Run one minimum viable experiment per crazy angle (see below) only if capacity allows.
3. Do not change trading logic in this mission; document angles for future board.

## 5 crazy angles

| Angle | Expected upside | Key risk | Minimum viable experiment | Data needed |
|-------|-----------------|----------|----------------------------|-------------|
| **1. Options/wheel pivot** | Theta capture; defined risk | Assignment, liquidity, monitoring | Paper trade 1 name wheel 30d; compare PnL vs stock-only | Options chain, assignment log, margin |
| **2. Universe change** | Better edge concentration | Regime shift in new names | Backtest last387 with narrowed universe (e.g. top 20 by volume) | Universe history, volume |
| **3. Time-of-day gating** | Avoid low-liquidity or mean-reversion hours | Miss morning momentum | Log entry time; compare win rate 10–11 vs 14–15 | entry_timestamp in ledger |
| **4. Volatility regime switching** | Size down or pause in high vol | Lag in regime detection | Tag regime (e.g. VIX bucket) per exit; compare PnL by regime | VIX or proxy in attribution |
| **5. Kill/keep radical simplification** | Single exit rule, single signal group; easier to tune | Lose edge from variety | Shadow: only decay exit + one signal group vs current | Shadow comparison with reduced config |

## What evidence would change my mind?
Quantified bottleneck (signal vs execution vs exits vs sizing); proof that options improve edge capture without unacceptable complexity; and one positive MVP result per angle.
