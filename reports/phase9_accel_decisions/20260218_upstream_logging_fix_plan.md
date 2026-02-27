# Upstream logging fix plan — giveback + classifiable blame (2026-02-18)

## Problem

- **Giveback N/A:** Logs often lack `exit_quality_metrics` (or MFE/high_water), so `profit_giveback` is null.
- **Blame 100% unclassified:** Blame classifier needs `entry_score`, `exit_quality_metrics.profit_giveback` (or MFE), and optionally MFE on joined rows. Many joined rows lack these (entry attribution or exit attribution).

## 1. Who should emit exit_quality_metrics (MFE/MAE/giveback inputs)

- **Log writer:** Exit attribution is written in `main.py` inside `log_exit_attribution()` (around 2145–2226). It calls `compute_exit_quality_metrics()` from `src/exit/exit_quality_metrics.py` and passes the result to `build_exit_attribution_record(..., exit_quality_metrics=...)`, which is appended via `append_exit_attribution(rec)` to **logs/exit_attribution.jsonl**.
- **Inputs for giveback:** `compute_exit_quality_metrics()` needs `high_water_price` (or bars for MFE/MAE). In `main.py`, `high_water = (info.get("high_water") or entry_price)`. So **info** passed to `log_exit_attribution(symbol, info, ...)` must include **high_water** when the position was tracked (e.g. from `self.high_water[symbol]` or equivalent). If `info["high_water"]` is missing, the code falls back to `entry_price`, so MFE becomes 0 and giveback is not computed.

**Files to change:**

- **main.py** (call sites of `log_exit_attribution`): Before calling `log_exit_attribution(symbol, info, ...)`, ensure `info` includes `high_water` when available. For example: if the executor holds `self.high_water` (or equivalent), set `info["high_water"] = self.high_water.get(symbol, info.get("high_water", entry_price))` (or the executed exit price as fallback) so that `compute_exit_quality_metrics` receives a non-trivial high_water when the position had upside. Exact location: wherever `info` is built/updated before the two call sites (~5545 displacement exit, ~7227 time/trail exit).

**Fields already written:** `exit_quality_metrics` is written by `build_exit_attribution_record` when `exit_quality_metrics` is not None; it includes `mfe`, `mae`, `time_in_trade_sec`, `profit_giveback`, `exit_efficiency`. So the only missing piece is ensuring **high_water** (or bars) is available so that `compute_exit_quality_metrics` can set MFE and thus profit_giveback.

## 2. Fields blame classifier requires

- **build_entry_vs_exit_blame** (in `scripts/analysis/run_effectiveness_reports.py`) uses joined rows (attribution + exit_attribution join). It needs:
  - **entry_score** (from entry attribution or joined row): for weak_entry (score &lt; 3).
  - **exit_quality_metrics.profit_giveback** and **exit_quality_metrics.mfe**: for exit_timing (giveback ≥ 0.3 or MFE &gt; 0 with loss).
- **Entry attribution** (logs/attribution.jsonl): Must expose **entry_score** (or equivalent) on the record that joins to exit_attribution so that the loader puts it on the joined row. If entry_score is computed at entry but not stored in attribution.jsonl, add it to the attribution record written at entry (or to the exit record if that’s where the join key lives).

**Files to check/change:**

- **Attribution writer (entry):** Identify where logs/attribution.jsonl is appended (entry fill or decision). Ensure the written record includes **entry_score** (or the field name the join/loader uses) so that `load_joined_closed_trades` produces rows with `entry_score`. If the loader expects a specific key (e.g. `entry_score`), add that key to the attribution record.
- **Exit side:** Already covered above (exit_quality_metrics via high_water).

## 3. Smallest upstream change summary

| File(s) | Change |
|--------|--------|
| main.py | Before each `log_exit_attribution(..., info=info, ...)`, set `info["high_water"] = self.high_water.get(symbol, info.get("high_water") or entry_price)` (or equivalent) so high_water is present when the executor tracked it. |
| Entry attribution writer | Ensure the attribution record written at entry (or the record that joins to exit) includes **entry_score** so joined rows have it. |

## 4. How to verify after change

1. **Giveback:** After deploying and running paper (or backtest) for some trades: `grep -o '"exit_quality_metrics":[^}]*' logs/exit_attribution.jsonl | head -20` — should see `profit_giveback` non-null when MFE was positive. Run effectiveness; **effectiveness_aggregates.json** or SUMMARY should show **avg_profit_giveback** non-null when data exists.
2. **Blame:** Re-run effectiveness; **entry_vs_exit_blame.json** should have **unclassified_pct** &lt; 100 (and weak_entry_pct / exit_timing_pct non-zero when data allows), and joined rows should have entry_score and exit_quality_metrics where we added the fields.
