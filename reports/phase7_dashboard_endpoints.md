# Phase 7 — Dashboard endpoints (attribution + effectiveness)

**Date:** 2026-02-18

## New endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/attribution/trade/<trade_id>` | GET | Per-trade joined view: entry snapshots (decision/fill), exit snapshots, exit_quality_metrics. Read-only from logs. |
| `/api/effectiveness/signals` | GET | Per signal_id: trade_count, win_rate, avg_pnl, avg_MFE, avg_MAE, avg_giveback. From latest effectiveness dir. |
| `/api/effectiveness/exits` | GET | Per exit_reason_code: frequency, avg_pnl, avg_giveback, pct_saved_loss, pct_left_money. |
| `/api/effectiveness/blame` | GET | weak_entry_pct, exit_timing_pct, example trades. |
| `/api/effectiveness/counterfactual` | GET | hold_longer_would_help, exit_earlier_would_save, examples. |

## Source of truth

- Attribution trade: logs/attribution.jsonl, logs/exit_attribution.jsonl (last 5k / 3k lines).
- Effectiveness: Latest dir from state/latest_backtest_dir.json then backtests/<path>/effectiveness, else newest reports/effectiveness_*. Results cached by dir mtime.

## Frontend

Attribution & Effectiveness tab loads all four effectiveness APIs and shows Blame KPIs, Signal Effectiveness table, Exit Effectiveness table, Counterfactual summary.
