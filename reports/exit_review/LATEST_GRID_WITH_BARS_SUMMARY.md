# Latest Fetch Missing Bars + Grid (from droplet)

**Run dir (droplet):** `/root/stock-bot/reports/exit_review/exit_grid_with_bars_20260223T235915Z`

## Summary

```
RUN_TAG: exit_grid_with_bars_20260223T235915Z

INPUT:
- normalized_exit_truth.json (historical)
- Missing bars fetched from Alpaca into data/bars

OUTPUT:
- grid_results.json (ranked exit configs)
- grid_board_review/
- grid_board_review/GRID_RECOMMENDATION.json

NEXT:
- If PROMOTE_TOP_CONFIG -> copy recommended_config into exit_candidate_signals.tuned.json
- Then run CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh for apples-to-apples validation
- If TUNE_OR_GET_MORE_BARS -> expand bar window or timeframe and re-run

LOG: /tmp/cursor_exit_grid_with_bars.log

```

## GRID_RECOMMENDATION.json

```json
{
  "generated_utc": "2026-02-23T23:59:44.586377+00:00",
  "decision": "TUNE_OR_GET_MORE_BARS",
  "rationale": "Top config: trailing_stop_pct=0.01, profit_target_pct=0.015, stop_loss_pct=0.02, time_stop_minutes=120; simulated total PnL%=0.0 over 0 exits.",
  "coverage_pct": 0.0,
  "n_exits_with_bars": 0,
  "n_exits_total": 2712,
  "top_configs": [
    {
      "trailing_stop_pct": 0.01,
      "profit_target_pct": 0.015,
      "stop_loss_pct": 0.02,
      "time_stop_minutes": 120,
      "total_pnl_pct": 0.0,
      "n_simulated": 0
    },
    {
      "trailing_stop_pct": 0.01,
      "profit_target_pct": 0.015,
      "stop_loss_pct": 0.02,
      "time_stop_minutes": 180,
      "total_pnl_pct": 0.0,
      "n_simulated": 0
    },
    {
      "trailing_stop_pct": 0.01,
      "profit_target_pct": 0.015,
      "stop_loss_pct": 0.02,
      "time_stop_minutes": 240,
      "total_pnl_pct": 0.0,
      "n_simulated": 0
    },
    {
      "trailing_stop_pct": 0.01,
      "profit_target_pct": 0.015,
      "stop_loss_pct": 0.02,
      "time_stop_minutes": 360,
      "total_pnl_pct": 0.0,
      "n_simulated": 0
    },
    {
      "trailing_stop_pct": 0.01,
      "profit_target_pct": 0.015,
      "stop_loss_pct": 0.03,
      "time_stop_minutes": 120,
      "total_pnl_pct": 0.0,
      "n_simulated": 0
    }
  ],
  "recommended_config": {
    "trailing_stop_pct": 0.01,
    "profit_target_pct": 0.015,
    "stop_loss_pct": 0.02,
    "time_stop_minutes": 120,
    "total_pnl_pct": 0.0,
    "n_simulated": 0
  }
}
```
