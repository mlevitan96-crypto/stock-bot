# Trade Designation for Multi-Scenario Replay

## Goal

Designate trades in a way that allows replay in **multiple scenarios** so we can test different improvements (entry rules, exit rules, universe filters, sizing) without losing the link to real outcomes.

## Current State

- **Attribution** (`logs/attribution.jsonl`): each executed trade has `trade_id`, `symbol`, `timestamp`/`ts`, `context`, `pnl_usd`, `hold_minutes`, `close_reason`.
- **Exit attribution** (`logs/exit_attribution.jsonl`): each exit has `symbol`, `exit_ts`, `exit_reason`, `time_in_trade_minutes`, `pnl`, v2 components.
- **Master trade log** (`logs/master_trade_log.jsonl`): entry/exit pairs with `trade_id`, `entry_ts`, `exit_ts`, `entry_v2_score`, `realized_pnl_usd`.
- **30-day backtest** (`scripts/run_30d_backtest_droplet.py`): loads attribution + exit_attribution + blocked_trades for a date window; replays with config flags (exit_regimes, UW, survivorship, etc.); writes `backtest_trades.jsonl`, `backtest_exits.jsonl`, `backtest_summary.json`.

Replay is already **date-window based**: we filter by `_day_utc(ts) in window_days`. So the natural designation is **cohort by time window** (e.g. "2026-02-01 to 2026-03-01").

## Designation Scheme

1. **Cohort ID**  
   - Use a **replay_cohort** label per run, e.g. `30d_2026-02-01_2026-03-01` or `last_30d`.  
   - Stored in backtest config and output artifacts, not required in each attribution line (we derive from timestamp).

2. **Per-trade identity**  
   - **trade_id** (already in attribution / master_trade_log): unique per trade.  
   - For replay inputs, keep: `trade_id`, `symbol`, `entry_ts`, `exit_ts`, `entry_score`, `context` (signals, regime), `pnl_usd`, `exit_reason`, `time_in_trade_minutes`.  
   - Optional: add `replay_cohort` to each record when writing backtest inputs so downstream can filter by cohort without date parsing.

3. **Scenarios to test**  
   - **Exit scenarios:** same entries, different exit rules (e.g. hold longer, tighter trail, different signal_decay threshold).  
   - **Entry scenarios:** same universe + bars, different entry gates (e.g. higher score floor, different expectancy gate).  
   - **Universe scenarios:** restrict or expand symbols (e.g. sector filter, liquidity filter).  
   - **Sizing scenarios:** same entries/exits, different position size.

4. **Implementation**  
   - **Backtest config** (`backtests/config/30d_backtest_config.json` or CLI): already has `start_date`, `end_date`; add optional `replay_cohort` string.  
   - **Backtest output:** in `backtest_summary.json` (and optionally in each `backtest_trades.jsonl` line), set `replay_cohort` and `scenario_id` (e.g. `baseline`, `exit_hold_longer`, `universe_tight`).  
   - **Comparison:** run multiple scenarios with the same `start_date`/`end_date` (same cohort), different scenario params; compare `backtest_summary.json` (total PnL, win rate, drawdown) and exit_reason distribution.

## Summary

- **Designation:** cohort = date range (+ optional label). Trade identity = `trade_id` + existing fields.  
- **Replay:** use existing 30d backtest pipeline; add `replay_cohort` and `scenario_id` to config and outputs so we can compare scenarios.  
- **Realistic backtest:** use real attribution + exit_attribution from droplet; run `scripts/run_30d_backtest_droplet.py` with different exit/entry/universe configs and compare results.
