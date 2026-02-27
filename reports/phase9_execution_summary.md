# Phase 9 first cycle — execution summary

**Started:** 2026-02-18T03:29:47+00:00 | **BACKTEST_DAYS:** 7 | **Completed:** 2026-02-18T03:30:09+00:00

## What ran on the droplet

| Step | Result | Notes |
|------|--------|--------|
| 1 Deploy | Exit 127 | deploy_on_droplet.sh not found on droplet. Commit: 88e121c9. |
| 2 Baseline | Success | Dir: backtests/30d_baseline_20260218_032951 |
| 3 Proposed | Success | Dir: backtests/30d_proposed_20260218_032957 |
| 4 Compare + guards | Exit 2 | Dir parsing bug + compare_backtest_runs.py not found at expected path on droplet. |
| 5 Decision | REVERT | No comparison artifact; REVERT by default. Process validated. |
| 6 Dashboard | 401 | Curl 401 (auth). API samples saved to reports/phase7_proof/. |

## Actual baseline and proposed dirs (on droplet)

- Baseline: backtests/30d_baseline_20260218_032951
- Proposed: backtests/30d_proposed_20260218_032957

## Recommendations

1. On droplet (SSH): git pull origin main; then run compare_backtest_runs.py with baseline backtests/30d_baseline_20260218_032951 and proposed backtests/30d_proposed_20260218_032957; run regression_guards.py. Pull comparison artifacts to local and update phase8_first_cycle_result.md with deltas and final LOCK/REVERT.
2. Confirm deploy script path on droplet (board/eod/deploy_on_droplet.sh) or run deploy manually.
3. Runner script fixed (ls -td for dir detection) for next run.
4. For full 30d evidence, re-run with BACKTEST_DAYS=30.

**Decision:** REVERT for this cycle. Set final LOCK/REVERT after compare + guards run on droplet.