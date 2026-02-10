# EOD Consolidated Review — 2026-02-10

## Rolling windows (1/3/5/7 day)

### pnl_by_window
{
  "1_day": -42.89,
  "3_day": -112.29,
  "5_day": -73.4,
  "7_day": -43.5
}

### win_rate_by_window
{
  "1_day": 0.1907,
  "3_day": 0.1657,
  "5_day": 0.1896,
  "7_day": 0.1995
}

### signal_decay_exit_rate_by_window
{
  "1_day": 0.9476,
  "3_day": 0.9434,
  "5_day": 0.9604,
  "7_day": 0.9477
}

## Missed money (Board-quantified)

{
  "blocked_trade_opportunity_cost": {
    "unknown": true,
    "reason": "Opportunity cost cannot be precisely quantified without knowing the expected P&L of each blocked trade and the frequency with which these trades would have been profitable. Historical win rates of similar trades would be needed.",
    "missing_inputs": [
      "expected P&L per blocked trade",
      "historical win rate of blocked trade types"
    ],
    "instrumentation_needed": [
      "logging of expected P&L for blocked trades",
      "post-hoc analysis framework for blocked trade performance"
    ]
  },
  "early_exit_opportunity_cost": {
    "unknown": true,
    "reason": "This requires a counterfactual analysis of how much more P&L would have been realized if trades exited by signal decay were held longer. This is not available in the current EOD bundle.",
    "missing_inputs": [
      "counterfactual P&L for extended hold periods",
      "average P&L of trades with relaxed decay"
    ],
    "instrumentation_needed": [
      "simulated P&L for alternative exit strategies",
      "A/B testing framework for exit parameters"
    ]
  },
  "correlation_concentration_cost": {
    "unknown": true,
    "reason": "The correlation cache is missing, making it impossible to identify and quantify any losses specifically attributable to correlated exposures.",
    "missing_inputs": [
      "correlation matrix",
      "P&L attribution by correlated groups"
    ],
    "instrumentation_needed": [
      "correlation cache generation and storage",
      "P&L attribution by correlation clusters"
    ]
  }
}
