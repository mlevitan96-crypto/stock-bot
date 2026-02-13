# EOD Consolidated Review — 2026-02-11

## Rolling windows (1/3/5/7 day)

### pnl_by_window
{
  "1_day": -24.86,
  "3_day": -137.15,
  "5_day": -137.15,
  "7_day": -68.36
}

### win_rate_by_window
{
  "1_day": 0.1893,
  "3_day": 0.173,
  "5_day": 0.173,
  "7_day": 0.1977
}

### signal_decay_exit_rate_by_window
{
  "1_day": 0.9624,
  "3_day": 0.9493,
  "5_day": 0.9493,
  "7_day": 0.9504
}

## Missed money (Board-quantified)

{
  "blocked_trade_opportunity_cost": {
    "unknown": true,
    "reason": "Lack of P&L tracking or simulation for blocked trades in the provided EOD bundle. Requires specific instrumentation to simulate P&L of blocked entries.",
    "missing_inputs": [
      "P&L associated with each blocked trade entry (simulated or actual outcome if allowed)"
    ],
    "instrumentation_needed": [
      "Blocked trade P&L simulation engine",
      "Historical data for all blocked symbols to backtest potential outcomes"
    ]
  },
  "early_exit_opportunity_cost": {
    "unknown": true,
    "reason": "Quantifying early exit opportunity cost (holding longer to gain more P&L) requires counterfactual simulation of how much P&L would have been gained by holding positions longer past their 'signal_decay' exits. The current data only shows realized P&L at exit.",
    "missing_inputs": [
      "Counterfactual P&L paths for exited trades"
    ],
    "instrumentation_needed": [
      "Counterfactual P&L simulation engine for trade exits",
      "Historical price and signal data for exited symbols post-exit"
    ]
  },
  "correlation_concentration_cost": {
    "unknown": true,
    "reason": "The correlation cache is missing, making it impossible to assess or quantify the cost of concentration. Without correlation data, we cannot identify clustered losses.",
    "missing_inputs": [
      "Correlation matrix or pairwise correlations for all traded and universe symbols"
    ],
    "instrumentation_needed": [
      "Correlation calculation and caching service",
      "P&L attribution by correlated clusters"
    ]
  }
}
