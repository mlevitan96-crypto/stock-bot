# ALPACA_BLOCKED_MISSED_INTEL

- **Blocked rows (tail):** 6052

## Reasons (top)

- `displacement_blocked`: **3704**
- `max_positions_reached`: **1418**
- `order_validation_failed`: **553**
- `expectancy_blocked:score_floor_breach`: **237**
- `max_new_positions_per_cycle`: **140**

## Net opportunity cost

- **Not computed** without forward price path per blocked symbol/time (would be replay).

## Gates strict vs loose

- Use reason counts above + `run.jsonl` blocked intents for ops review; causal "too strict" needs A/B shadow.

