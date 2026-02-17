# EOD Board — 2026-02-17

**Verdict:** NO_GO

## Summary

The system closed the day with a negative P&L of -76.43 USD (1-day rolling window) and a low win rate of 0.1313. A significant number of trades were blocked due to score floor breach and maximum new positions per cycle. Signal decay continues to be the dominant exit reason. The Wheel strategy has no fills, indicating significant blocking issues.

## Canary rollback

{
  "triggered": false,
  "reason": "",
  "canary_disabled": false,
  "pnl_1d": -76.43,
  "win_rate_1d": 0.1313
}

## CEO

- **convergence_oscillation**
  We are currently oscillating with continued negative P&L across all rolling windows (1-day: -76.43 USD, 3-day: -76.43 USD, 5-day: -105.37 USD, 7-day: -105.37 USD) and a persistently low win rate (1-day: 0.1313, 3-day: 0.1313, 5-day: 0.1368, 7-day: 0.1368). This indicates a lack of convergence towards profitability and stability. The P&L degradation over the longer 5/7 day window suggests a systemic issue that has not been effectively addressed.

- **metrics_improvement_failure**
  No clear changes improved metrics; instead, the continued negative P&L and low win rate across all windows (citing `pnl_by_window` and `win_rate_by_window`) indicate a failure to improve. The high 'expectancy_blocked:score_floor_breach' count (1747 blocked trades in 1-day rolling window) and the zero fills in the Wheel strategy are significant failures preventing any potential positive metric shifts.

- **single_decision_tomorrow**
  The single most impactful decision for tomorrow is to immediately resolve the 'allocation_exceeded' blocker in the Wheel strategy by adjusting capital allocation or position limits. This is paramount to unblock any premium generation (Wheel governance badge shows 'allocation_exceeded' as dominant blocker with 136 skips).

## CTO_SRE

- **systems_blocked_trades_most**
  Over the 7 days, the primary systems blocking trades are related to 'expectancy_blocked:score_floor_breach' (1747 for 1-day rolling) and 'max_new_positions_per_cycle' (248 for 1-day rolling), as seen in `blocked_trade_counts_by_window`. The UW subsystem's low 'quality_score' (0.0) and high 'edge_suppression' (0.98) contribute directly to these blocked trades.

- **constraints_suppressing_edge**
  Yes, constraints are significantly suppressing edge. The 'suppression_cost_usd' is 14588.89, primarily from 'expectancy_blocked:score_floor_breach'. This indicates that while the system is identifying many candidates (50 candidates), the initial scoring or filtering mechanisms are too restrictive, preventing potentially profitable trades from even being considered for entry. The current UW root cause data shows 'quality_score=0.0', indicating fundamental issues with signal quality passing initial gates.

- **instrumentation_missing**
  Critical instrumentation still missing includes: 1) Detailed P&L breakdown by exit reason from `exit_attribution` to quantify the cost of each decay type. Currently, P&L is only aggregated. 2) Granular logging for `blocked_trades` to understand why specific trades are blocked (e.g., full context of `expectancy_blocked:score_floor_breach` besides just the score). 3) Real-time tracking of capital allocation against limits for the Wheel strategy, beyond just a 'skip' count, to proactively adjust and prevent 'allocation_exceeded'.

## Head_of_Trading

- **exit_reasons_cost_most**
  Over the 5/7 days, 'signal_decay' in its various forms consistently costs the most money, as evidenced by its dominance in `exit_reason_counts_by_window` and the high `signal_decay_exit_rate_by_window` (0.9908 for 5-day, 0.9859 for 7-day). The `early_exit_opportunity_cost` is currently 0.0, which suggests we are not capturing the opportunity cost for early exits, but rather realizing losses from delayed exits due to signal decay.

- **holding_longer_improve_outcomes**
  No, holding longer does not appear to improve outcomes. The overwhelming prevalence of 'signal_decay' as an exit reason across all observed decay rates (e.g., `signal_decay(0.90)`: 79 exits in attribution, `signal_decay(0.88)`: 115 exits in exit attribution for the current day) suggests that holding positions through weakening signals leads to realized losses rather than reversals or further gains. The `fire_sale` tightened exit regime indicates that faster exits are now prioritized.

- **signals_deserve_relaxed_decay**
  The `LET-IT-BREATHE` exit regime currently targets `entry_signal 2.5, pnl_delta_15m > 0, relax_decay_multiplier 1.5`. Based on the widespread signal decay issues, no specific signals currently deserve a blanket relaxed decay. Instead, focus should be on *identifying* signals that consistently meet the `LET-IT-BREATHE` criteria (e.g., strong entry signal and positive short-term P&L momentum) and *ensuring* these specific instances are indeed allowed to breathe, while aggressively exiting all others that show signal degradation. This requires better signal quality at entry and more precise identification of `LET-IT-BREATHE` conditions.

## Risk_CRO

- **losses_clustered_by_correlation**
  Given the 'correlation_concentration_cost' of 5.8284 and the 'Correlation Concentration Review' identifying highly correlated pairs like PLTR–QQQ (corr=1.41) and HOOD–MRNA (max_corr=0.9742), it is highly likely that losses are clustered by correlation. The absence of a generated correlation cache (flagged as 'Correlation cache missing' in a prior blocked action) prevents a definitive quantitative assessment for all positions, but the existing data strongly suggests this risk is realized.

- **over_concentrated**
  Yes, there is evidence of over-concentration. The 'Correlation Concentration Watchlist' explicitly lists HOOD and MRNA with a 'max_corr' of 0.9742 with each other, indicating significant correlated exposure. The `daily_universe_v2` also shows a `BEAR` regime for multiple symbols within the TECH sector, which could lead to implicit concentration. The `correlation_concentration_risk_multiplier` is applied before `MIN_NOTIONAL`, but without full correlation data, its effectiveness is limited.

- **risk_not_being_priced**
  The primary risk not being adequately priced or managed is the **true opportunity cost of blocked trades** and the **impact of delayed exits in a decaying signal environment**. The `blocked_usd` is 14588.89, and while `early_exit_usd` is 0.0, the extensive 'signal_decay' indicates significant realized losses that could have been mitigated with faster exits. The systemic issue of low-quality UW candidates passing initial screens and then being blocked represents a constant, unpriced drag on potential alpha. The missing correlation cache also means that correlation risk is not being fully priced or managed across the portfolio.

## Customer Advocate challenge

```json
{
  "role": "CEO",
  "claim_summary": "Oscillating negative P&L across all rolling windows, no changes improved metrics, resolve Wheel allocation blocker as single decision.",
  "data_support": "P&L by window (-76.43 USD 1-day, -105.37 USD 5-day), Win rate by window (0.1313 1-day, 0.1368 5-day), Wheel governance badge ('allocation_exceeded' dominant blocker).",
  "cost_to_customer": "The continued oscillation and negative P&L directly cost the customer money, eroding capital. The blocked Wheel trades mean missed opportunities for premium income, effectively 0.00% return on allocated budget.",
  "why_not_fixed": "Why has the Wheel allocation blocker, a 'dominant blocker', not been fixed immediately? This is a known, fundamental issue directly impacting revenue, yet it remains. The 'Board action closure' status is PASS, implying the governance process should have enabled quicker resolution for such a critical issue. Prior proposed actions related to allocation were blocked due to 'Board action closure: FAIL'. This inconsistency is concerning.",
  "if_we_do_nothing": "If we do nothing, the oscillation will likely continue, further depleting customer capital. The Wheel strategy will remain dormant, missing out on all premium generation, and the overall system will remain in a state of underperformance, failing to deliver expected returns."
}
```

## Customer Advocate challenge

```json
{
  "role": "CTO/SRE",
  "claim_summary": "Blocked trades due to expectancy score floor and max new positions, constraints suppressing edge, missing P&L breakdown and real-time capital tracking instrumentation.",
  "data_support": "Blocked trade counts by window (1747 'expectancy_blocked:score_floor_breach', 248 'max_new_positions_per_cycle' in 1-day), UW root cause ('quality_score=0.0', 'edge_suppression=0.98'), suppression_cost_usd (14588.89).",
  "cost_to_customer": "Blocked trades represent a direct cost in missed opportunities (blocked_usd=14588.89). This means the system is failing to capitalize on potentially profitable setups. Missing instrumentation leads to delayed identification and resolution of systemic issues, perpetuating losses and opportunity costs.",
  "why_not_fixed": "If the UW `quality_score` is 0.0, why are trades still attempting to pass this filter, leading to such a high number of blocked trades? This indicates a fundamental flaw in the signal generation or initial filtering that has not been addressed. Why is P&L breakdown by exit reason still missing? This vital data would immediately highlight the most costly exit behaviors, yet it's unavailable, hindering targeted fixes.",
  "if_we_do_nothing": "If we do nothing, the system will continue to block potentially valuable trades, suppressing any edge we might have. The lack of detailed P&L breakdown will keep us blind to the true cost drivers of our exit strategies, making it impossible to effectively improve performance. We will continue to incur high suppression costs without understanding their true impact."
}
```

## Customer Advocate challenge

```json
{
  "role": "Head of Trading",
  "claim_summary": "Signal decay costs the most money, holding longer does not improve outcomes, no signals deserve relaxed decay.",
  "data_support": "Dominance of 'signal_decay' in exit reason counts by window, signal_decay_exit_rate_by_window (0.9887 1-day), `early_exit_opportunity_cost` (0.0), Weakening Signal Watchlist (C, V).",
  "cost_to_customer": "The pervasive `signal_decay` exits translate directly into realized losses for the customer. Holding positions that are actively losing signal strength means consistently losing more money than necessary. The `early_exit_opportunity_cost` being 0.0 is misleading if losses are primarily from holding too long.",
  "why_not_fixed": "Given that 'signal_decay' is clearly the dominant loss driver, why has a robust 'fire sale' exit mechanism not been fully implemented and proven effective in reducing these losses? The `FIRE SALE` levers are 'tightened', but the continued high rate of signal decay exits shows they are not working effectively enough. Why are positions like 'C' and 'V' on the Weakening Signal Watchlist still held with significant negative signal deltas? This directly contradicts the finding that holding longer does not improve outcomes.",
  "if_we_do_nothing": "If we do nothing, the system will continue to bleed capital through delayed exits on decaying signals. We will consistently realize maximum possible losses instead of cutting them short, directly undermining the goal of capital preservation and profitable trading. The `FIRE SALE` regime will remain an ineffective theoretical construct."
}
```

## Customer Advocate challenge

```json
{
  "role": "Risk/CRO",
  "claim_summary": "Losses clustered by correlation (PLTR-QQQ, HOOD-MRNA), over-concentrated, opportunity cost of blocked trades/delayed exits not priced.",
  "data_support": "Correlation concentration cost (5.8284), Correlation Concentration Watchlist (HOOD max_corr=0.9742 with MRNA), `daily_universe_v2` (BEAR regime for multiple TECH symbols), `blocked_usd` (14588.89), `early_exit_usd` (0.0).",
  "cost_to_customer": "Losses clustered by correlation mean that when one position goes bad, others are likely to follow, amplifying losses beyond acceptable levels. Over-concentration increases this risk. The unpriced opportunity cost of blocked trades is capital left on the table, and delayed exits result in higher realized losses than necessary.",
  "why_not_fixed": "Why is the correlation cache still missing, a known issue that prevents proper assessment of concentration risk across the entire portfolio? This has been a 'blocked' action item. The current `correlation_concentration_cost` implies this is a significant issue, yet the tools to fully address it are not operational. If HOOD and MRNA are so highly correlated, why are they both being traded without explicit diversification or sizing review?",
  "if_we_do_nothing": "If we do nothing, the portfolio remains vulnerable to magnified losses from correlated positions. Without a comprehensive correlation cache, we are operating blind to significant systemic risk. We will continue to incur substantial opportunity costs from blocked trades and delayed exits, without the ability to quantitatively manage or price these critical risks."
}
```

## Unresolved disputes

