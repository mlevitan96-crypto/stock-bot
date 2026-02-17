# Weekly Review — week ending 2026-02-17

## PnL and win rate trend by day

| Date | PnL 1d | Win rate 1d |
|------|--------|-------------|
| 2026-02-11 | -24.86 | 18.93% |
| 2026-02-12 | 0.00 | 0.00% |
| 2026-02-13 | -162.15 | 15.16% |
| 2026-02-14 | 0.00 | 0.00% |
| 2026-02-15 | 0.00 | 0.00% |
| 2026-02-16 | 0.00 | 0.00% |
| 2026-02-17 | -76.43 | 13.13% |

## Top exit reasons by day

## Top blockers by day

## Recurring failures (top 5)
- Based on the available data, no specific changes that demonstrably improved metrics are evident. The win rate has remained low (e.g., 0.1893 for 1-day, 0.173 for 3-day, citing `win_rate_by_window`), s
- Over the last 7 days, 'displacement_blocked' (950 trades for 1-day and 3-day, citing `blocked_trade_counts_by_window`) and 'max_positions_reached' (767 trades for 1-day and 3-day, citing `blocked_trad
- Yes, constraints are very likely suppressing edge. The high counts of 'displacement_blocked' and 'max_positions_reached' indicate that the system is frequently unable to take trades that meet entry cr
- It is unknown if we are over-concentrated due to the missing correlation cache (citing Section 3.4b). However, the high number of 'max_positions_reached' blocked trades (767 for 1-day, citing `blocked
- The most significant unpriced risk is the lack of a proper correlation assessment due to the missing correlation cache (citing Section 3.4b). This means the system cannot accurately identify or price 

## Recurring blockers (top 5)

## Exit reason trends (week)

## Customer Advocate recurring critiques (top 5 themes)
- System oscillating negatively, no changes improving metrics.
- Single decision is to implement aggressive 'fire sale' exit.
- Systems blocked trades most by 'displacement_blocked' and 'max_positions_reached'.
- Critical missing instrumentation is a robust classification system for 'unknown' exit reasons and a functional correlation cache.
- 'Unknown' exit reasons and 'signal_decay' cost the most money.

## What to double down on
- Based on the available data, no specific changes that demonstrably improved metrics are evident. The win rate has remained low (e.g., 0.1893 for 1-day
- No, the data does not suggest that holding longer improved outcomes. The 'Weakening Signal Watchlist' (Section 3.4a) shows numerous positions with sig
- No metrics have shown clear improvement; instead, P&L remains negative and win rates are low. The high signal decay exit rate (95.51% over 3 days) sug
- The single decision that goes live tomorrow is to **immediately establish clear ownership and process for board action closure (action_id: new-action-
- Based on the dominant 'signal_decay' exit reason, it is highly probable that holding positions longer, especially those with initial positive P&L befo

## What to kill immediately
- blocked_trade_opportunity_cost: instrumentation needed
- early_exit_opportunity_cost: instrumentation needed
- correlation_concentration_cost: instrumentation needed
- blocked_trade_opportunity_cost: instrumentation needed
- early_exit_opportunity_cost: instrumentation needed

## Changes deployed and outcomes
Review daily eod_board.json wheel_actions and recommendations for what was deployed.