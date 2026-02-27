# Blame split 0.0 / 0.0 — root cause and fix (2026-02-18)

## Root cause

- **weak_entry_pct** and **exit_timing_pct** were 0.0 with 2808 joined trades because:
  - **Weak entry** requires `entry_score` present and **&lt; 3.0**; many joined rows lack `entry_score` (join/attribution pipeline or missing in entry attribution).
  - **Exit timing** requires `exit_quality_metrics.profit_giveback ≥ 0.3` or (MFE &gt; 0 and PnL &lt; 0); many rows lack `exit_quality_metrics` / giveback / MFE.
- So most losers were **unclassified** (neither weak_entry nor exit_timing), but the report did not surface that; it only showed weak_entry_pct and exit_timing_pct, which were 0/0 and looked like a broken or degenerate split.

## Fix

- **build_entry_vs_exit_blame** in `scripts/analysis/run_effectiveness_reports.py` now:
  - Uses index sets for weak_entry and exit_timing as before.
  - Computes **unclassified_count** = losers not in (weak_entry ∪ exit_timing) and **unclassified_pct** = 100 * unclassified_count / total_losing_trades.
  - Return dict includes **unclassified_count** and **unclassified_pct**.
- **EFFECTIVENESS_SUMMARY.md** section "Entry vs exit blame" now includes a line: "% unclassified (neither): {unclassified_pct}".

## Verification

- **File:** `reports/effectiveness_*\/entry_vs_exit_blame.json`.
- **Fields:** `weak_entry_pct`, `exit_timing_pct`, **unclassified_pct**, **unclassified_count**.
- **Expectation:** When many losers lack entry_score/giveback/MFE, unclassified_pct is high and explicit; weak_entry_pct and exit_timing_pct may remain low. Regression test: `validation/scenarios/test_effectiveness_reports.py` — `build_entry_vs_exit_blame` includes `unclassified_pct` and `unclassified_count`.
