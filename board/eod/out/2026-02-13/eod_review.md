# EOD Consolidated Review — 2026-02-13

## Rolling windows (1/3/5/7 day)

### pnl_by_window
{
  "1_day": -162.15,
  "3_day": -162.15,
  "5_day": -162.15,
  "7_day": -162.15
}

### win_rate_by_window
{
  "1_day": 0.1516,
  "3_day": 0.1516,
  "5_day": 0.1516,
  "7_day": 0.1516
}

### signal_decay_exit_rate_by_window
{
  "1_day": 0.9924,
  "3_day": 0.9844,
  "5_day": 0.975,
  "7_day": 0.975
}

## Missed money (Board-quantified)

{
  "blocked_trade_opportunity_cost": {
    "unknown": false,
    "total_expected_value_usd": 18590.23,
    "by_reason": {
      "order_validation_failed": 1176.59,
      "max_new_positions_per_cycle": 10209.11,
      "expectancy_blocked:score_floor_breach": 4635.45,
      "symbol_on_cooldown": 1087.06,
      "displacement_blocked": 531.34,
      "max_positions_reached": 950.68
    }
  },
  "early_exit_opportunity_cost": {
    "unknown": true,
    "reason": "exit_hold_longer lacks pnl_delta_15m/60m for signal_decay exits",
    "missing_inputs": [
      "exit_hold_longer.jsonl marks for signal_decay exits"
    ]
  },
  "correlation_concentration_cost": {
    "unknown": false,
    "correlation_cache_present": true,
    "concentration_risk_score": 5.8284,
    "top_pairs_count": 5
  }
}
