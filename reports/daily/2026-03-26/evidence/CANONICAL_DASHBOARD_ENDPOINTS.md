# Canonical Dashboard Endpoints

**Source of truth: reports/DASHBOARD_ENDPOINT_MAP.md + config.registry.** This doc is the cleanup-audit snapshot. Generated 2026-02-27.

## Rule

All file reads MUST use `(_DASHBOARD_ROOT / path).resolve()` for relative paths. No hardcoded absolute paths.

## API → data location (canonical)

| Endpoint | Data location |
|----------|----------------|
| `/api/ping` | None |
| `/api/governance/status` | `reports/equity_governance/equity_governance_*/lock_or_revert_decision.json`, `reports/effectiveness_*/effectiveness_aggregates.json` |
| `/api/version` | Git, process |
| `/api/positions` | Alpaca API, state/position_metadata.json, data/uw_flow_cache.json, data/live_orders.jsonl |
| `/api/pnl/reconcile` | Alpaca API, state/daily_start_equity.json, logs/attribution.jsonl |
| `/api/stockbot/closed_trades` | logs/attribution.jsonl, logs/exit_attribution.jsonl, logs/telemetry.jsonl (equity cohort in response) |
| `/api/closed_positions` | state/closed_positions.json |
| `/api/system/health` | state/health.json |
| `/api/sre/health` | localhost:8081 or data/health_status.json, state/health.json |
| `/api/sre/self_heal_events` | data/self_heal_events.jsonl |
| `/api/xai/auditor` | data/explainable_logs.jsonl, logs/attribution.jsonl |
| `/api/executive_summary` | executive_summary_generator → logs/attribution.jsonl, logs/master_trade_log.jsonl |
| `/api/health_status` | Alpaca, data/live_orders.jsonl, logs/orders.jsonl, logs/trading.jsonl, state/bot_heartbeat.json |
| `/api/scores/*` | telemetry.score_telemetry |
| `/api/regime-and-posture` | state/market_context_v2.json, state/regime_posture_state.json |
| `/api/telemetry/latest/*` | telemetry/YYYY-MM-DD/computed/ |

After cleanup: ensure no endpoint points to removed or moved paths. Dashboard MUST keep using only these canonical paths.
