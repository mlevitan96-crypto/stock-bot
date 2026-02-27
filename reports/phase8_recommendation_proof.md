# Phase 8 — Recommendation generation proof

**Date:** Fill after pipeline run.

## Pipeline wiring

- **Script:** board/eod/run_30d_backtest_on_droplet.sh
- **Step 4.6:** Runs generate_recommendation.py --backtest-dir OUT_DIR after profitability_baseline_and_recommend.
- **Output file:** backtest_dir/profitability_recommendation.md

## Generated recommendation path

- **Path:** (e.g. backtests/30d_xxx/profitability_recommendation.md)

## Excerpt

Fill with excerpt from profitability_recommendation.md: baseline blame, top harmful signal_id, worst exit_reason_code, overlay suggestion, "suggestion only - no auto-apply" banner.

## Definition of done

- Pipeline runs effectiveness, guards, profitability_baseline_and_recommend, generate_recommendation.
- profitability_recommendation.md exists in backtest dir.
- Recommendation includes harmful signal_ids, worst exit_reason_code, overlay suggestion, suggestion-only banner.
