# EOD Consolidated Review — 2026-02-18

## Rolling windows (1/3/5/7 day)

### pnl_by_window
{
  "1_day": -61.63,
  "3_day": -131.84,
  "5_day": -131.84,
  "7_day": -131.84
}

### win_rate_by_window
{
  "1_day": 0.1313,
  "3_day": 0.1265,
  "5_day": 0.1265,
  "7_day": 0.1265
}

### signal_decay_exit_rate_by_window
{
  "1_day": 1.0,
  "3_day": 0.9921,
  "5_day": 0.9921,
  "7_day": 0.991
}

## Missed money (Board-quantified)

{
  "blocked_trade_opportunity_cost": {
    "unknown": false,
    "total_expected_value_usd": 3937.24,
    "by_reason": {
      "expectancy_blocked:score_floor_breach": 1889.45,
      "score_below_min": 2047.79
    }
  },
  "early_exit_opportunity_cost": {
    "unknown": true,
    "reason": "The raw P&L from early exits due to signal decay is not explicitly quantified as 'opportunity cost' in the provided `missed_money_numeric` data. While `signal_decay` is a dominant exit reason, calculating the exact missed profit from holding longer would require a counterfactual analysis not present.",
    "missing_inputs": [
      "historical counterfactual P&L for signal decay exits",
      "average profit potential of trades exited due to signal decay"
    ],
    "instrumentation_needed": [
      "A simulation engine to quantify opportunity cost for various exit strategies.",
      "Detailed logging of potential P&L if a trade was held for X more minutes after exit."
    ]
  },
  "correlation_concentration_cost": {
    "unknown": false,
    "correlation_cache_present": true,
    "message": "insufficient pairs",
    "concentration_risk_score": null
  }
}
