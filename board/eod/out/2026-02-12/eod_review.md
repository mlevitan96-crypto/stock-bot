# EOD Consolidated Review — 2026-02-12

## Rolling windows (1/3/5/7 day)

### pnl_by_window
{
  "1_day": 0,
  "3_day": -67.75,
  "5_day": -137.15,
  "7_day": -98.26
}

### win_rate_by_window
{
  "1_day": 0.0,
  "3_day": 0.19,
  "5_day": 0.173,
  "7_day": 0.1895
}

### signal_decay_exit_rate_by_window
{
  "1_day": 0.0,
  "3_day": 0.9551,
  "5_day": 0.9493,
  "7_day": 0.9608
}

## Missed money (Board-quantified)

{
  "blocked_trade_opportunity_cost": {
    "unknown": true,
    "reason": "Opportunity cost cannot be precisely quantified without knowing the average P&L of similar unblocked trades. The high volume of blocked trades (1223 'displacement_blocked', 488 'max_positions_reached' today) suggests a significant but unquantified amount of missed P&L.",
    "missing_inputs": [
      "Simulated P&L of blocked trades",
      "Average P&L per trade for unblocked trades in similar regimes/sectors"
    ],
    "instrumentation_needed": [
      "A simulation framework to backtest blocked trades under prevailing conditions",
      "Enhanced logging of expected P&L for blocked trades"
    ]
  },
  "early_exit_opportunity_cost": {
    "unknown": true,
    "reason": "Opportunity cost from early exits (signal decay) cannot be quantified without knowing the P&L trajectory if trades were held longer. Over 95% of exits are due to signal decay, implying this is a substantial but unquantified cost.",
    "missing_inputs": [
      "P&L of 'signal_decay' exited trades if held for an additional x minutes/hours",
      "Alternative exit P&L comparison data"
    ],
    "instrumentation_needed": [
      "Post-trade analysis tool to simulate alternative exit scenarios for signal-decay trades",
      "Tracking of P&L at time of initial signal decay vs. subsequent price action"
    ]
  },
  "correlation_concentration_cost": {
    "unknown": false,
    "correlation_cache_present": true,
    "message": "insufficient open symbols for correlation",
    "concentration_risk_score": null
  }
}
