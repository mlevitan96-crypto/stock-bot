# EOD Consolidated Review — 2026-02-17

## Rolling windows (1/3/5/7 day)

### pnl_by_window
{
  "1_day": -76.43,
  "3_day": -76.43,
  "5_day": -105.37,
  "7_day": -105.37
}

### win_rate_by_window
{
  "1_day": 0.1313,
  "3_day": 0.1313,
  "5_day": 0.1368,
  "7_day": 0.1368
}

### signal_decay_exit_rate_by_window
{
  "1_day": 0.9887,
  "3_day": 0.9887,
  "5_day": 0.9908,
  "7_day": 0.9859
}

## Missed money (Board-quantified)

{
  "blocked_trade_opportunity_cost": {
    "unknown": false,
    "total_expected_value_usd": 14588.89,
    "by_reason": {
      "expectancy_blocked:score_floor_breach": 5984.25,
      "max_new_positions_per_cycle": 8426.11,
      "order_validation_failed": 137.09,
      "symbol_on_cooldown": 41.44
    }
  },
  "early_exit_opportunity_cost": {
    "value": 0.0,
    "unit": "USD",
    "reason": "The provided data for 'early_exit_usd' is 0.0. However, the prevalence of 'signal_decay' exits suggests that while explicit 'early exit' opportunity cost is not tracked as such, there is a significant realized loss from *delayed* exits that could be considered a form of 'missed money' from not exiting earlier.",
    "instrumentation_needed": [
      "Quantification of P&L saved by hypothetical earlier exits on decaying signals."
    ]
  },
  "correlation_concentration_cost": {
    "unknown": false,
    "correlation_cache_present": true,
    "concentration_risk_score": 0.9742,
    "top_pairs_count": 1
  }
}
