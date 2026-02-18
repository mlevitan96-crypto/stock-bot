# EOD Board — 2026-02-18

**Verdict:** NO_GO

## Summary

The system experienced a negative P&L of -131.84 USD over the 3, 5, and 7-day rolling windows, with a significantly low win rate of 0.1313 for the 1-day window. The primary exit reason is signal decay, and a substantial number of trades were blocked due to low scores and expectancy breaches, indicating fundamental issues with signal quality and trade selection.

## Canary rollback

{
  "triggered": false,
  "reason": "",
  "canary_disabled": false,
  "pnl_1d": -61.63,
  "win_rate_1d": 0.1313
}

## CEO

- **convergence_oscillation**
  Across the 1/3/5/7 day windows, the P&L indicates a consistent negative trend, with a slight convergence from -61.63 USD (1-day) to -131.84 USD (3, 5, 7-day). This suggests sustained losses rather than oscillation around a mean, indicating a systemic issue. (Citation: pnl_by_window)

- **changes_impact**
  Based on the rolling window data, no recent change has improved metrics; rather, the win rate has remained consistently low (around 0.13), and P&L is negative across all observed windows. This suggests that implemented changes, if any, have failed to improve profitability. (Citation: pnl_by_window, win_rate_by_window)

- **single_decision_live_tomorrow**
  The single decision to go live tomorrow is to implement an A/B test for adjusted UW `quality_score` and `edge_suppression` thresholds, targeting a minimum 10% improvement in total P&L. This aims to immediately address the core issue of poor signal quality and suppressed edge. (Citation: proactive_insights, root_cause)

## CTO_SRE

- **systems_blocked_trades_most**
  Over the last 7 days, the primary systems blocking trades are those related to `score_below_min` and `expectancy_blocked:score_floor_breach`, accounting for 1039 and 961 blocks respectively. These constraints are severely limiting trade execution. (Citation: blocked_trade_counts_by_window, proactive root-cause)

- **constraints_suppressing_edge**
  Yes, constraints are definitely suppressing edge. The constraint root cause shows a suppression cost of 3937.24 USD, explicitly from `expectancy_blocked:score_floor_breach` and `score_below_min`. This indicates that potentially profitable trades are being filtered out. (Citation: proactive root-cause, missed_money_numeric)

- **instrumentation_missing**
  The primary missing instrumentation is a granular breakdown of P&L by sector and market regime within the EOD bundle. This prevents a detailed analysis of performance in different market conditions and asset classes. Additionally, a clear attribution for the 2000 'unknown' exits in the `exit_attribution.jsonl` is missing, which is critical for understanding exit performance. (Citation: sector_context, Exit attribution)

## Head_of_Trading

- **exit_reasons_costing_most**
  Over the 5/7 days, 'signal_decay' reasons (e.g., 'signal_decay(0.96)', 'signal_decay(0.91)', 'signal_decay(0.90)') are consistently the most frequent exit reasons after 'unknown', strongly suggesting they are costing the most money through suboptimal exits as signals weaken, rather than for profit-taking. (Citation: exit_reason_counts_by_window)

- **holding_longer_outcomes**
  There is no direct evidence that holding longer improved outcomes. The pervasive 'signal_decay' as an exit reason implies that holding through decay is leading to losses. The 'FIRE_SALE' and 'LET-IT-BREATHE' levers are active, but the current P&L suggests 'LET-IT-BREATHE' might be too permissive or not adequately counterbalanced. (Citation: exit_reason_counts_by_window, Tightened profitability levers)

- **signals_deserve_relaxed_decay**
  The data does not clearly point to specific signals deserving relaxed decay. Given the low win rate and negative P&L across all windows, the current focus should be on tightening exit criteria and improving signal quality overall, rather than relaxing decay. If any, signals with consistently high quality scores and strong edge realization that are being prematurely exited by decay could be candidates for future review. (Citation: win_rate_by_window, proactive root-cause)

## Risk_CRO

- **losses_clustered_by_correlation**
  While no specific symbols are currently on the 'correlation concentration watchlist', the 'Max |corr| pair' identified as HOOD–MRNA with a correlation of 0.97 indicates a high potential for clustered losses if positions were held in both. The `correlation_score` of 0.9742 from `missed_money_numeric` further supports this risk, even if not directly linked to current losses. (Citation: Wheel Daily Review section 3.4b, missed_money_numeric)

- **over_concentrated**
  The wheel strategy has a dominant blocker 'allocation_exceeded' (63 skips), suggesting potential over-concentration in capital allocation, even if not by symbol count. The presence of highly correlated pairs like HOOD–MRNA (corr=0.97) also highlights a risk of concentration, even if positions are not currently active in both. (Citation: Wheel governance badge, Wheel Daily Review section 3.4b)

- **risk_not_being_priced**
  The significant opportunity cost from blocked trades (3937.24 USD) due to `score_below_min` and `expectancy_blocked:score_floor_breach` suggests that the risk of missing valid opportunities, or mispricing the true expectancy of certain signals, is not adequately priced or factored into the current system. (Citation: missed_money_numeric, Constraint root cause)

## Customer Advocate challenge

```json
{
  "role": "CEO",
  "claim_summary": "P&L indicates a consistent negative trend with slight convergence; no change improved metrics, instead sustained losses; single decision to go live is an A/B test for UW thresholds.",
  "data_support": "The P&L for 1-day (-61.63), 3-day (-131.84), 5-day (-131.84), and 7-day (-131.84) windows confirms a consistently negative P&L. The win rate across all windows is also consistently low (around 0.13). (Citation: pnl_by_window, win_rate_by_window)",
  "cost_to_customer": "The customer has incurred consistent losses, totaling at least 131.84 USD over the last 3-7 days. The failure to improve metrics means a continued drain on capital without positive returns. The proposed A/B test, while necessary, implies further experimentation with customer capital rather than an immediate fix.",
  "why_not_fixed": "Why has the system been allowed to operate with consistent losses and a low win rate for days without a more decisive intervention? The root causes (poor signal quality, suppressed edge, and blocked trades) appear to be fundamental, yet a 'single decision' to run an A/B test feels like a delayed response to a persistent problem.",
  "if_we_do_nothing": "If we do nothing, the system will continue to generate consistent losses, eroding customer capital. The low win rate will persist, and the identified root causes will remain unaddressed, leading to further P&L degradation and missed opportunities."
}
```

## Customer Advocate challenge

```json
{
  "role": "CTO/SRE",
  "claim_summary": "Systems blocking trades most over 7 days are related to `score_below_min` and `expectancy_blocked:score_floor_breach`; constraints are suppressing edge costing 3937.24 USD; primary missing instrumentation is granular P&L by sector/regime and exit attribution.",
  "data_support": "Blocked trade counts by window show 'score_below_min' (1039) and 'expectancy_blocked:score_floor_breach' (961) as dominant reasons for blocking. Missed money numeric quantifies `blocked_usd` at 3937.24. Sector and regime P&L is noted as 'null' in sector_context, and exit_attribution has 2000 'unknown' exits. (Citation: blocked_trade_counts_by_window, missed_money_numeric, sector_context, Exit attribution)",
  "cost_to_customer": "The customer is directly losing out on 3937.24 USD in opportunity cost from blocked trades. Additionally, the lack of detailed P&L by sector/regime and clear exit attribution means we cannot pinpoint where money is being lost or gained effectively, leading to continued suboptimal performance and further customer losses.",
  "why_not_fixed": "Why have these known blocking constraints not been adjusted or refined when they are costing thousands in missed opportunities? Why is critical instrumentation for P&L analysis and exit attribution still missing when it's vital for understanding and improving performance? These are systemic failures that impact customer profitability daily.",
  "if_we_do_nothing": "If we do nothing, the system will continue to block potentially profitable trades, incurring significant opportunity costs. The inability to analyze performance by sector/regime or understand exit causality will prevent any meaningful improvements, ensuring continued P&L degradation for the customer."
}
```

## Customer Advocate challenge

```json
{
  "role": "Head of Trading",
  "claim_summary": "Signal decay reasons costing the most money over 5/7 days; no direct evidence holding longer improved outcomes; no specific signals deserve relaxed decay.",
  "data_support": "The `exit_reason_counts_by_window` for 3-day (which covers 5 and 7-day as the data is identical) shows 'signal_decay' as the dominant non-unknown exit reason (e.g., signal_decay(0.96) is 245 in 1-day, 245 in 3-day). P&L is consistently negative across all windows. (Citation: exit_reason_counts_by_window, pnl_by_window)",
  "cost_to_customer": "The persistent 'signal_decay' exits indicate that trades are being held through periods of signal weakening, leading to realized losses or reduced profits. The overall negative P&L directly impacts the customer's account. The lack of clarity on holding periods means we're potentially missing out on better exits.",
  "why_not_fixed": "Given that 'signal decay' is the primary explicit exit reason and contributes to negative P&L, why hasn't a more aggressive or dynamic exit strategy been implemented to cut losses sooner or capture profits more effectively? Why are we waiting for signals to decay rather than acting proactively?",
  "if_we_do_nothing": "If we do nothing, trades will continue to suffer from 'signal decay' exits, contributing to ongoing losses. Without a refined exit strategy, the customer will continue to experience suboptimal trade management and eroded capital."
}
```

## Customer Advocate challenge

```json
{
  "role": "Risk/CRO",
  "claim_summary": "Potential for clustered losses from highly correlated pairs like HOOD\u2013MRNA (corr=0.97); potential over-concentration due to 'allocation_exceeded' and highly correlated pairs; risk of missing valid opportunities or mispricing expectancy not adequately priced.",
  "data_support": "Wheel Daily Review section 3.4b identifies HOOD\u2013MRNA with a correlation of 0.97. The `correlation_score` from `missed_money_numeric` is 0.9742. 'allocation_exceeded' is the 'Dominant blocker' in the Wheel governance badge. (Citation: Wheel Daily Review section 3.4b, missed_money_numeric, Wheel governance badge)",
  "cost_to_customer": "The high correlation between HOOD and MRNA, if traded, exposes the customer to magnified losses in adverse market conditions due to concentration risk. The 'allocation_exceeded' blocker, while not directly a loss, represents missed opportunities that could have generated P&L, effectively costing the customer potential gains. The mispricing of expectancy through blocked trades directly results in missed profitable trades.",
  "why_not_fixed": "Why is the system allowing highly correlated pairs to be identified as a risk without a direct, enforceable mechanism to manage or avoid such concentration? Why are capital allocation constraints leading to 'allocation_exceeded' being the dominant blocker, effectively limiting trading activity and potential P&L? These are critical risk management gaps.",
  "if_we_do_nothing": "If we do nothing, the system will continue to be exposed to concentration risk from highly correlated assets, potentially leading to significant clustered losses. The 'allocation_exceeded' blocker will continue to prevent trading activity, and the mispricing of expectancy will lead to ongoing missed opportunities, all contributing to negative customer outcomes."
}
```

## Unresolved disputes

