# Weekly Review — week ending 2026-02-13

## PnL and win rate trend by day

| Date | PnL 1d | Win rate 1d |
|------|--------|-------------|
| 2026-02-07 | 0.00 | 0.00% |
| 2026-02-08 | 0.00 | 0.00% |
| 2026-02-09 | 0.00 | 0.00% |
| 2026-02-10 | -42.89 | 19.07% |
| 2026-02-11 | -24.86 | 18.93% |
| 2026-02-12 | 0.00 | 0.00% |
| 2026-02-13 | -162.15 | 15.16% |

## Top exit reasons by day

## Top blockers by day

## Recurring failures (top 5)
- No clear improvements are observed in key metrics across the rolling windows; all metrics indicate a failing state. The consistent low win rate and negative P&L across all lookback periods highlight a
- Over the past 7 days, 'displacement_blocked' (1135 in 1-day window) and 'max_positions_reached' (634 in 1-day window) are the systems blocking the most trades. The rolling window data for blocked trad
- Yes, constraints are very likely suppressing edge. The high volume of blocked trades (2000 total in the 1-day window) due to 'displacement_blocked' and 'max_positions_reached' suggests that a large nu
- Based on the available data, no specific changes that demonstrably improved metrics are evident. The win rate has remained low (e.g., 0.1893 for 1-day, 0.173 for 3-day, citing `win_rate_by_window`), s
- Over the last 7 days, 'displacement_blocked' (950 trades for 1-day and 3-day, citing `blocked_trade_counts_by_window`) and 'max_positions_reached' (767 trades for 1-day and 3-day, citing `blocked_trad

## Recurring blockers (top 5)

## Exit reason trends (week)

## Customer Advocate recurring critiques (top 5 themes)
- System oscillating around negative P&L and low win rate; no clear convergence to profitability.
- No clear improvements in metrics; all indicate failing state.
- Prioritize fixing 'unknown' exit reason classification.
- Systems blocking most trades over 7 days are 'displacement_blocked' and 'max_positions_reached'.
- Constraints are very likely suppressing edge.

## What to double down on
- No clear improvements are observed in key metrics across the rolling windows; all metrics indicate a failing state. The consistent low win rate and ne
- The single most impactful decision for tomorrow is to prioritize fixing the 'unknown' exit reason classification. Without understanding why a signific
- There is no direct data to confirm if holding longer would have improved outcomes. However, the consistently high 'signal_decay_exit_rate_by_window' (
- Based on the available data, no specific changes that demonstrably improved metrics are evident. The win rate has remained low (e.g., 0.1893 for 1-day
- No, the data does not suggest that holding longer improved outcomes. The 'Weakening Signal Watchlist' (Section 3.4a) shows numerous positions with sig

## What to kill immediately
- blocked_trade_opportunity_cost: instrumentation needed
- early_exit_opportunity_cost: instrumentation needed
- correlation_concentration_cost: instrumentation needed
- blocked_trade_opportunity_cost: instrumentation needed
- early_exit_opportunity_cost: instrumentation needed

## Changes deployed and outcomes
Review daily eod_board.json wheel_actions and recommendations for what was deployed.