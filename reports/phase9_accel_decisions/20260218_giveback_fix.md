# Giveback N/A — root cause and fix (2026-02-18)

## Root cause

- **avg_profit_giveback** in effectiveness reports comes from **exit_quality_metrics.profit_giveback** on joined rows (entry ↔ exit attribution join).
- Giveback is computed in `src/exit/exit_quality_metrics.py` from MFE/high_water and realized PnL; it is written in **exit_attribution** when `exit_quality_metrics` is present.
- On the droplet, many exit_attribution log lines lack **exit_quality_metrics** (or MFE/high_water), so **profit_giveback** is null for those trades.
- Aggregation in `build_exit_effectiveness` and in the overall summary only averages over trades that have giveback; when no trades have giveback (or too few), the reported value is **N/A** (null).
- So N/A is primarily **upstream data availability**: logs often don’t contain `exit_quality_metrics` / MFE, not a bug in the effectiveness aggregation logic.

## Fix

1. **Report-side (done):**
   - **Overall aggregates** section in `EFFECTIVENESS_SUMMARY.md`: overall win_rate and overall avg_profit_giveback (from exit reasons), so when data exists it’s visible in one place.
   - **effectiveness_aggregates.json** written by `run_effectiveness_reports.py` with `joined_count`, `total_losing_trades`, `win_rate`, `avg_profit_giveback` so gate-50/close-loop can read one file; when no giveback data, `avg_profit_giveback` is null.
2. **Upstream (recommended):** Ensure `main.py` passes **high_water** (and MFE where used) into exit attribution so `exit_quality_metrics` and `profit_giveback` are populated when possible.

## How to verify

- **File:** `reports/effectiveness_*\/effectiveness_aggregates.json` or `EFFECTIVENESS_SUMMARY.md` section "## 0. Overall aggregates".
- **Field:** `avg_profit_giveback` (or "Overall avg_profit_giveback" in MD).
- **Expectation:** Non-null when logs contain giveback for a sufficient set of joined trades; N/A (null) when no giveback data in logs. Regression test: `validation/scenarios/test_effectiveness_reports.py` — when joined rows have `profit_giveback`, `build_exit_effectiveness` returns a reason with non-null `avg_profit_giveback`.
