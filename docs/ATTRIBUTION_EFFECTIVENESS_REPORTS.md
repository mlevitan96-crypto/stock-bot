# Phase 5 — Signal & Exit Effectiveness Reports: How to Interpret

**Purpose:** Turn attribution data into decision-grade intelligence. No tuning yet — analysis only.

---

## Data source

Reports are generated from **joined closed trades**: each row is one exit record matched to its entry (by `symbol` + `entry_timestamp`). Data can come from:

- **Live logs:** `logs/attribution.jsonl` + `logs/exit_attribution.jsonl`
- **Backtest:** `backtest_trades.jsonl` + `backtest_exits.jsonl` in a backtest output dir
- **Lab:** Same schema in synthetic run outputs

Run:

```bash
python scripts/analysis/run_effectiveness_reports.py [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--base-dir PATH] [--out-dir PATH]
python scripts/analysis/run_effectiveness_reports.py --backtest-dir backtests/30d_xxx [--out-dir PATH]
```

Output directory (default `reports/effectiveness_<date>`) contains:

- `signal_effectiveness.json` / `.csv`
- `exit_effectiveness.json` / `.csv`
- `entry_vs_exit_blame.json`
- `counterfactual_exit.json`
- `EFFECTIVENESS_SUMMARY.md` (human-readable)

---

## 1. Signal effectiveness report

**What it is:** For each `signal_id` (from **entry** `attribution_components`), aggregates over all trades that had that signal present (with non-zero contribution or any presence, depending on implementation).

**Fields:**

| Field | Meaning |
|-------|--------|
| **trade_count** | Number of closed trades where this signal appeared in entry attribution. |
| **win_rate** | Fraction of those trades with positive realized P&L. |
| **avg_pnl** | Average realized P&L (USD) for those trades. |
| **avg_MFE** | Average max favorable excursion (from exit_quality_metrics); null if not computed. |
| **avg_MAE** | Average max adverse excursion; null if not computed. |
| **avg_profit_giveback** | Average (MFE − realized) / MFE when MFE > 0; higher = more “left on table.” |
| **breakdown_by_regime** | Same metrics broken down by entry_regime (if available). |
| **breakdown_by_hour** | Same metrics by hour of day (if available). |

**How to use:**

- **Signals that help:** High win_rate, high avg_pnl, low avg_profit_giveback → keep or increase weight.
- **Signals that hurt:** Low win_rate, negative avg_pnl → consider down-weighting or gating.
- **Regime/hour breakdown:** Use to see if a signal works only in certain regimes or times; supports regime-aware tuning later.

**Caveat:** A signal “present” in attribution means it had a non-zero contribution in the entry composite. Correlation vs causation: strong signals may correlate with better entries; the report does not prove causality.

---

## 2. Exit effectiveness report

**What it is:** For each **exit_reason_code** (and optionally per exit component), aggregates frequency and outcomes.

**Fields:**

| Field | Meaning |
|-------|--------|
| **frequency** | Number of exits with this reason. |
| **frequency_pct** | Percentage of all exits. |
| **avg_realized_pnl** | Average realized P&L (USD) for those exits. |
| **avg_profit_giveback** | Average profit giveback (from exit_quality_metrics). |
| **avg_post_exit_excursion** | Average post_exit_excursion when available (how much price moved after exit). |
| **pct_saved_loss** | % of those exits where exit_efficiency.saved_loss is true (exited before loss grew). |
| **pct_left_money** | % where exit_efficiency.left_money is true (exited with profit but left significant upside). |

**How to use:**

- **Exits that save loss:** High pct_saved_loss, negative avg_realized_pnl but less bad than holding → exit rule is doing its job.
- **Exits that leave money:** High pct_left_money, high avg_profit_giveback → consider holding longer or adjusting targets (in a later tuning phase).
- **Frequency:** Identifies dominant exit reasons; combine with avg_pnl to see which reasons are associated with better/worse outcomes.

---

## 3. Entry vs exit blame report

**What it is:** Focus on **losing trades** only. Splits blame into “weak entry” vs “exit timing.”

**Definitions (current logic):**

- **Weak entry:** entry_score < 3.0 (configurable in script).
- **Exit timing:** high profit_giveback (≥ 0.3) or had positive MFE but realized loss (exited too late into drawdown).

**Fields:**

| Field | Meaning |
|-------|--------|
| **total_losing_trades** | Number of closed trades with realized P&L < 0. |
| **weak_entry_pct** | % of those with entry_score below threshold. |
| **exit_timing_pct** | % with high giveback or MFE-but-loss. |
| **examples_good_entry_bad_exit** | Sample trades: decent entry score but loss / high giveback → exit timing likely at fault. |
| **examples_bad_entry** | Sample trades: low entry score and loss → entry likely at fault. |

**How to use:**

- **High weak_entry_pct:** Losses are mostly from bad entries → improve entry filters/signals before changing exits.
- **High exit_timing_pct:** Losses are mostly from exit timing (gave back gains or held into drawdown) → focus on exit rules / targets / stops later.
- Use **examples_*** for manual review and to validate the thresholds.

---

## 4. Counterfactual exit analysis

**What it is:** Uses **exit_quality_metrics** only. No behavior change — identifies trades where a different exit would likely have improved outcome.

**Two buckets:**

1. **Hold longer would have helped:** profit_giveback ≥ 0.25 and (left_money or realized > 0). Suggests these trades exited too early relative to available upside.
2. **Exit earlier would have saved loss:** realized P&L < 0 and MAE > 0. Suggests these trades stayed in while price went against them; earlier exit would have cut the loss.

**Fields:**

- **hold_longer_would_help_count** / **hold_longer_examples**
- **exit_earlier_would_save_count** / **exit_earlier_examples**

**How to use:**

- **Hold-longer list:** Candidates for looser profit targets or longer holds (future tuning).
- **Exit-earlier list:** Candidates for tighter stops or earlier exit triggers (future tuning).
- Examples are for spot-checking and building intuition; do not auto-apply logic changes.

---

## Reproducibility

- **Live:** Run the script with `--start` / `--end` over a date range where logs exist.
- **Backtest:** Run with `--backtest-dir backtests/<run_dir>` after a 30d (or other) backtest.
- **Lab:** Point `--base-dir` at a directory that contains `logs/attribution.jsonl` and `logs/exit_attribution.jsonl` (or use backtest-style outputs).

Same script, same schema; only the data source path changes.
