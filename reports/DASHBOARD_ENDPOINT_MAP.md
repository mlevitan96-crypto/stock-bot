# Dashboard Endpoint → Data Location Map

**Generated:** 2026-02-02 | **Canonical per config.registry + MEMORY_BANK**

All paths resolved against `_DASHBOARD_ROOT` (dashboard.py directory). No engine data modified.

---

## API Endpoints

| Endpoint | Data Location | Notes |
|----------|---------------|-------|
| `/api/ping` | None | Health check |
| `/api/version` | Git, process | Build/version info |
| `/api/positions` | Alpaca API, `state/position_metadata.json`, `data/uw_flow_cache.json`, `data/live_orders.jsonl` | 8s timeout |
| `/api/pnl/reconcile` | Alpaca API, `state/daily_start_equity.json`, `logs/attribution.jsonl` | Date query |
| `/api/stockbot/closed_trades` | `logs/attribution.jsonl`, `logs/telemetry.jsonl` | Max 10k attr lines, 500 telemetry |
| `/api/stockbot/wheel_analytics` | Same as closed_trades | Filtered to strategy_id=wheel |
| `/api/closed_positions` | `state/closed_positions.json` | Last 50 |
| `/api/system/health` | `state/health.json` | Supervisor health |
| `/api/system-events` | `logs/system_events.jsonl` | Via utils.system_events |
| `/api/sre/health` | `http://localhost:8081` or `data/health_status.json`, `state/health.json` | Fallback on timeout |
| `/api/sre/self_heal_events` | `data/self_heal_events.jsonl` (CacheFiles.SELF_HEAL_EVENTS) | Via health.self_heal_events |
| `/api/xai/auditor` | `data/explainable_logs.jsonl`, `logs/attribution.jsonl` | Max 10k lines attr |
| `/api/xai/health` | `data/explainable_logs.jsonl` | Tail 500 |
| `/api/xai/export` | `data/explainable_logs.jsonl` | Full file |
| `/api/executive_summary` | `executive_summary_generator` → `logs/attribution.jsonl`, `logs/master_trade_log.jsonl` | Timeframe query |
| `/api/health_status` | Alpaca API, `data/live_orders.jsonl`, `logs/orders.jsonl`, `logs/trading.jsonl`, `state/bot_heartbeat.json` | Last order + heartbeat |
| `/api/scores/distribution` | `telemetry.score_telemetry` | Lookback param |
| `/api/scores/components` | `telemetry.score_telemetry` | Lookback param |
| `/api/scores/telemetry` | `telemetry.score_telemetry` | Summary |
| `/api/failure_points` | SRE/failure_point_monitor | |
| `/api/signal_history` | signal_history_storage | |
| `/api/wheel/universe_health` | `state/wheel_universe_health.json` | |
| `/api/strategy/comparison` | `reports/{date}_stock-bot_combined.json`, `reports/*_weekly_promotion_report.json` | |
| `/api/regime-and-posture` | `state/market_context_v2.json`, `state/regime_posture_state.json` | |
| `/api/telemetry/latest/index` | `telemetry/YYYY-MM-DD/computed/` | Latest date dir |
| `/api/telemetry/latest/computed` | `telemetry/YYYY-MM-DD/computed/{name}.json` | Query param: name |
| `/api/paper-mode-intel-state` | `telemetry/paper_mode_intel_state.json` | |
| `/api/telemetry/latest/health` | `telemetry/YYYY-MM-DD/computed/`, `logs/master_trade_log.jsonl` | |

---

## Path Resolution Rule

All file reads MUST use `(_DASHBOARD_ROOT / path).resolve()` when path is relative, so dashboard works regardless of cwd.
