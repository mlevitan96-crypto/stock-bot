# Dashboard Route Map — 2026-03-06

## Route → Template → Loader → Data Source

| Route | Handler | Tab | Data source |
|-------|---------|-----|-------------|
| `/` | index() | (full page) | Banner: state/direction_readiness, state/direction_replay_status; Situation: direction_readiness + reports/{date}_stock-bot_combined; Learning: _get_learning_readiness_payload → direction_readiness, direction_replay_status, exit_attribution, visibility_matrix |
| `/health` | health() | — | sre_monitoring.get_sre_health(), pgrep main.py |
| `/api/ping` | api_ping() | — | None |
| `/api/version` | api_version() | Version badge | Git rev-parse |
| `/api/versions` | api_versions() | — | Git, process |
| `/api/direction_banner` | api_direction_banner() | Banner | state/direction_readiness.json, direction_banner_state |
| `/api/situation` | api_situation() | Situation strip | state/direction_readiness.json, reports/{today}_stock-bot_combined.json, state/internal_positions, position_metadata |
| `/api/telemetry_health` | api_telemetry_health() | Telemetry Health | Log paths, direction_readiness, gate_status, last_droplet_analysis |
| `/api/learning_readiness` | api_learning_readiness() | Learning & Readiness | state/direction_readiness.json, state/direction_replay_status.json, logs/exit_attribution.jsonl, reports/{today}_stock-bot_combined.json |
| `/api/governance/status` | api_governance_status() | — | reports/equity_governance/*, reports/effectiveness_* |
| `/api/positions` | api_positions() | Positions | Alpaca API, state/position_metadata.json, data/uw_flow_cache.json, data/live_orders.jsonl |
| `/api/pnl/reconcile` | api_pnl_reconcile() | — | Alpaca, state/daily_start_equity.json, logs/attribution.jsonl |
| `/api/stockbot/closed_trades` | api_stockbot_closed_trades() | Closed Trades | logs/attribution.jsonl, logs/exit_attribution.jsonl, logs/telemetry.jsonl |
| `/api/stockbot/wheel_analytics` | api_stockbot_wheel_analytics() | Wheel Strategy | Same + reports/*_stock-bot_wheel.json, state/wheel_state.json |
| `/api/closed_positions` | api_closed_positions() | — | state/closed_positions.json |
| `/api/system/health` | api_system_health() | — | state/health.json |
| `/api/system-events` | api_system_events() | — | logs/system_events.jsonl |
| `/api/sre/health` | api_sre_health() | SRE Monitoring | localhost:8081 or data/health_status.json, state/health.json |
| `/api/sre/self_heal_events` | api_sre_self_heal_events() | — | data/self_heal_events.jsonl |
| `/api/xai/auditor` | api_xai_auditor() | Natural Language Auditor | data/explainable_logs.jsonl, logs/attribution.jsonl |
| `/api/xai/health` | api_xai_health() | — | data/explainable_logs.jsonl |
| `/api/xai/export` | api_xai_export() | — | data/explainable_logs.jsonl |
| `/api/executive_summary` | api_executive_summary() | Executive Summary | executive_summary_generator → logs/attribution.jsonl, logs/master_trade_log.jsonl |
| `/api/health_status` | api_health_status() | — | Alpaca, data/live_orders.jsonl, logs/orders.jsonl, state/bot_heartbeat.json |
| `/api/scores/distribution` | api_scores_distribution() | — | telemetry.score_telemetry |
| `/api/scores/components` | api_scores_components() | — | telemetry.score_telemetry |
| `/api/scores/telemetry` | api_scores_telemetry() | — | telemetry.score_telemetry |
| `/api/failure_points` | api_failure_points() | Trading Readiness | SRE/failure_point_monitor |
| `/api/signal_history` | api_signal_history() | Signal Review | signal_history_storage |
| `/api/wheel/universe_health` | api_wheel_universe_health() | Wheel | state/wheel_universe_health.json, config/universe_wheel.yaml, state/daily_universe_v2.json |
| `/api/strategy/comparison` | api_strategy_comparison() | Strategy Comparison | reports/{date}_stock-bot_combined.json, reports/*_weekly_promotion_report.json |
| `/api/regime-and-posture` | api_regime_and_posture() | — | state/market_context_v2.json, state/regime_posture_state.json |
| `/api/telemetry/latest/index` | api_telemetry_latest_index() | Telemetry | telemetry/YYYY-MM-DD/computed/ |
| `/api/telemetry/latest/computed` | api_telemetry_latest_computed() | — | telemetry/YYYY-MM-DD/computed/{name}.json |
| `/api/telemetry/latest/health` | api_telemetry_latest_health() | — | telemetry/..., logs/master_trade_log.jsonl |
| `/api/paper-mode-intel-state` | api_paper_mode_intel_state() | — | telemetry/paper_mode_intel_state.json |
| `/reports/board/<path>` | serve_board_report() | (links) | reports/board/<filename> |
| `/sre` | (SRE page) | SRE | Same as /api/sre/health |

## Added (Phase 5)

- `/api/profitability_learning` — **Added.** Serves Profitability & Learning tab: cockpit markdown, CSA verdict, trade state (PROFITABILITY_COCKPIT.md, CSA_VERDICT_LATEST.json, TRADE_CSA_STATE.json). Tab in More dropdown.

## Broken or stale

- `/api/positions`: 8s timeout; may show error if Alpaca slow.
- SRE: fallback to file if localhost:8081 times out.
- Learning & Readiness: includes all_time_exits, last_csa_mission_id, trades_until_next_csa, link to Profitability & Learning.
