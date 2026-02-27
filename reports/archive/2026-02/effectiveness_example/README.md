# Example effectiveness report outputs (Phase 5)

This folder contains **example** machine-readable (JSON/CSV) and human-readable (MD) outputs from the Phase 5 effectiveness analysis.

- **signal_effectiveness.json** / **.csv** — Per signal_id: trade_count, win_rate, avg_pnl, avg_MFE, avg_MAE, avg_profit_giveback.
- **exit_effectiveness.json** / **.csv** — Per exit_reason_code: frequency, avg_realized_pnl, avg_profit_giveback, % saved_loss, % left_money.
- **entry_vs_exit_blame.json** — For losing trades: % weak entry vs % exit timing; example trades.
- **counterfactual_exit.json** — Hold-longer vs exit-earlier counterfactual counts and examples.
- **EFFECTIVENESS_SUMMARY.md** — Human-readable summary.

**How to interpret:** See `docs/ATTRIBUTION_EFFECTIVENESS_REPORTS.md`.

**Reproduce from live or backtest:**

```bash
python scripts/analysis/run_effectiveness_reports.py [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--out-dir PATH]
python scripts/analysis/run_effectiveness_reports.py --backtest-dir backtests/30d_xxx [--out-dir PATH]
```
