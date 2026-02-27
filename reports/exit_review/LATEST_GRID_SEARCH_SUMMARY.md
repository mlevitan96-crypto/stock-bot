# Latest Exit Grid Search (from droplet)

**Run dir (droplet):** `/root/stock-bot/reports/exit_review/exit_grid_20260223T224113Z`

## Summary

```
RUN_TAG: exit_grid_20260223T224113Z
NORMALIZED_SOURCE: /root/stock-bot/reports/exit_review/historical_historical_exit_review_20260223T222935Z/normalized_exit_truth.json

ARTIFACTS:
- grid_results.json (all param sets, ranked by simulated PnL)
- grid_board_review/ (prosecutor, defender, quant, sre, board)
- grid_board_review/GRID_RECOMMENDATION.json

NEXT:
- Apply recommended_config to config/exit_candidate_signals.tuned.json
- Run CURSOR_EXIT_SIGNAL_TUNE_AND_RERUN.sh for apples-to-apples validation
- If bar coverage was low, fetch more bars (data/bars or parquet) and re-run grid

LOG: /tmp/cursor_exit_grid.log

```

## GRID_RECOMMENDATION.json

```json
{
  "generated_utc": "2026-02-23T22:41:42.853755+00:00",
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
