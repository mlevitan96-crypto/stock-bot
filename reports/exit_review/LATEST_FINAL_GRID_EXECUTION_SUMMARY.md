# Latest Final Grid Execution (from droplet)

**Run dir (droplet):** `/root/stock-bot/reports/exit_review/exit_grid_with_bars_20260224T005443Z`

## Summary

```
RUN_TAG: exit_grid_with_bars_20260224T005443Z

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
