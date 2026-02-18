# Weekly Review — week ending 2026-02-18

## PnL and win rate trend by day

| Date | PnL 1d | Win rate 1d |
|------|--------|-------------|
| 2026-02-12 | 0.00 | 0.00% |
| 2026-02-13 | -162.15 | 15.16% |
| 2026-02-14 | 0.00 | 0.00% |
| 2026-02-15 | 0.00 | 0.00% |
| 2026-02-16 | 0.00 | 0.00% |
| 2026-02-17 | -76.43 | 13.13% |
| 2026-02-18 | -61.63 | 13.13% |

## Top exit reasons by day

## Top blockers by day

## Recurring failures (top 5)
- No metrics have shown clear improvement; instead, P&L remains negative and win rates are low. The high signal decay exit rate (95.51% over 3 days) suggests that previous adjustments to exit logic, if 
- The single decision that goes live tomorrow is to **immediately establish clear ownership and process for board action closure (action_id: new-action-1)**. This critical governance failure is blocking
- Over the last 7 days (and 3 days where data is available, with 950 and 767 respectively), the primary systems blocking trades are related to 'displacement_blocked' (1223 today) and 'max_positions_reac
- Yes, constraints are clearly suppressing edge. The high counts of 'displacement_blocked' (1223) and 'max_positions_reached' (488) directly imply that potential trades are being identified but not exec
- The single decision that goes live tomorrow is to establish clear ownership and process for board action closure. This is paramount to unblock all other proposed improvements and ensure accountability

## Recurring blockers (top 5)

## Exit reason trends (week)

## Customer Advocate recurring critiques (top 5 themes)
- System oscillating negatively; no metrics improved.
- Single decision for tomorrow: Fix Board action closure.
- Systems blocked trades most due to displacement and max positions.
- Missing instrumentation: Correlation cache.
- Signal decay exit reasons cost the most money.

## What to double down on
- No metrics have shown clear improvement; instead, P&L remains negative and win rates are low. The high signal decay exit rate (95.51% over 3 days) sug
- The single decision that goes live tomorrow is to **immediately establish clear ownership and process for board action closure (action_id: new-action-
- Based on the dominant 'signal_decay' exit reason, it is highly probable that holding positions longer, especially those with initial positive P&L befo
- No clear metrics improved; instead, the system is consistently underperforming. The tightened profitability levers (FIRE SALE, LET-IT-BREATHE, Survivo
- The single decision that goes live tomorrow is to establish clear ownership and process for board action closure. This is paramount to unblock all oth

## What to kill immediately
- blocked_trade_opportunity_cost: instrumentation needed
- early_exit_opportunity_cost: instrumentation needed
- early_exit_opportunity_cost: instrumentation needed
- early_exit_opportunity_cost: instrumentation needed

## Changes deployed and outcomes
Review daily eod_board.json wheel_actions and recommendations for what was deployed.