# Dashboard Data Source Validation

**Date:** 2026-03-06  
**Scope:** Data sources required by `dashboard.py` routes (state, logs, reports, data, config, telemetry).  
**Existence/readability:** To be validated on droplet in Phase 2. This document defines the checklist.

Format: **Source path | Exists (Y/N) | Readable | Notes**

---

## State

| Source path | Exists (Y/N) | Readable | Notes |
|-------------|--------------|----------|--------|
| state/direction_readiness.json | To be validated on droplet in Phase 2 | — | Direction banner, situation, learning readiness |
| state/direction_replay_status.json | To be validated on droplet in Phase 2 | — | Direction banner (RUNNING/SUCCESS/BLOCKED) |
| state/health.json | To be validated on droplet in Phase 2 | — | /api/system/health, SRE merge |
| state/last_droplet_analysis.json | To be validated on droplet in Phase 2 | — | Telemetry health, governance status |
| state/daily_start_equity.json | To be validated on droplet in Phase 2 | — | P&L reconcile, positions day_pnl |
| state/position_metadata.json | To be validated on droplet in Phase 2 | — | Positions tab, entry scores |
| state/internal_positions.json | To be validated on droplet in Phase 2 | — | Situation open count fallback |
| state/wheel_state.json | To be validated on droplet in Phase 2 | — | Positions strategy_id, wheel analytics |
| state/closed_positions.json | To be validated on droplet in Phase 2 | — | /api/closed_positions |
| state/wheel_universe_health.json | To be validated on droplet in Phase 2 | — | /api/wheel/universe_health primary |
| state/daily_universe_v2.json | To be validated on droplet in Phase 2 | — | Wheel universe fallback |
| state/market_context_v2.json | To be validated on droplet in Phase 2 | — | /api/regime-and-posture |
| state/regime_posture_state.json | To be validated on droplet in Phase 2 | — | /api/regime-and-posture |
| state/bot_heartbeat.json | To be validated on droplet in Phase 2 | — | /api/health_status Doctor |
| state/doctor_state.json | To be validated on droplet in Phase 2 | — | /api/health_status fallback |
| state/system_heartbeat.json | To be validated on droplet in Phase 2 | — | /api/health_status fallback |
| state/heartbeat.json | To be validated on droplet in Phase 2 | — | /api/health_status fallback |
| state/regime_detector.json | To be validated on droplet in Phase 2 | — | Positions current score (registry) |
| state/regime_detector_state.json | To be validated on droplet in Phase 2 | — | Positions current score |
| state/signal_strength_cache.json | To be validated on droplet in Phase 2 | — | Positions current_score, signal trend |
| state/signal_correlation_cache.json | To be validated on droplet in Phase 2 | — | Positions signal_correlation |

---

## Logs

| Source path | Exists (Y/N) | Readable | Notes |
|-------------|--------------|----------|--------|
| logs/master_trade_log.jsonl | To be validated on droplet in Phase 2 | — | Telemetry health, telemetry/latest/health |
| logs/attribution.jsonl | To be validated on droplet in Phase 2 | — | Situation closed count, closed trades, XAI auditor, P&L reconcile |
| logs/exit_attribution.jsonl | To be validated on droplet in Phase 2 | — | Telemetry health, learning readiness, closed trades, visibility matrix |
| logs/exit_event.jsonl | To be validated on droplet in Phase 2 | — | Telemetry health canonical list |
| logs/intel_snapshot_entry.jsonl | To be validated on droplet in Phase 2 | — | Telemetry health |
| logs/intel_snapshot_exit.jsonl | To be validated on droplet in Phase 2 | — | Telemetry health |
| logs/direction_event.jsonl | To be validated on droplet in Phase 2 | — | Telemetry health |
| logs/telemetry.jsonl | To be validated on droplet in Phase 2 | — | Closed trades (wheel), wheel analytics |
| logs/system_events.jsonl | To be validated on droplet in Phase 2 | — | /api/system-events |
| logs/orders.jsonl | To be validated on droplet in Phase 2 | — | /api/health_status last order fallback |
| logs/trading.jsonl | To be validated on droplet in Phase 2 | — | /api/health_status last order fallback |

---

## Data

| Source path | Exists (Y/N) | Readable | Notes |
|-------------|--------------|----------|--------|
| data/explainable_logs.jsonl | To be validated on droplet in Phase 2 | — | XAI auditor, XAI health, XAI export |
| data/health_status.json | To be validated on droplet in Phase 2 | — | SRE health merge (health_subsystem) |
| data/self_heal_events.jsonl | To be validated on droplet in Phase 2 | — | /api/sre/self_heal_events |
| data/live_orders.jsonl | To be validated on droplet in Phase 2 | — | /api/health_status last order fallback |
| data/uw_flow_cache.json | To be validated on droplet in Phase 2 | — | Positions current score (registry CacheFiles.UW_FLOW_CACHE) |

---

## Reports

| Source path | Exists (Y/N) | Readable | Notes |
|-------------|--------------|----------|--------|
| reports/board/DIRECTION_REPLAY_30D_RESULTS.md | To be validated on droplet in Phase 2 | — | Direction banner "View report", RESULTS link |
| reports/board/DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md | To be validated on droplet in Phase 2 | — | Direction banner BLOCKED link |
| reports/board/PROFITABILITY_COCKPIT.md | To be validated on droplet in Phase 2 | — | Board/cockpit summary (consumed by tooling; dashboard may link) |
| reports/board/<path> (generic) | To be validated on droplet in Phase 2 | — | /reports/board/<path> static serve |
| reports/audit/TELEMETRY_CONTRACT_AUDIT.md | To be validated on droplet in Phase 2 | — | Telemetry health gate_status |
| reports/audit/CSA_VERDICT_LATEST.json | To be validated on droplet in Phase 2 | — | CSA/cockpit tooling |
| reports/audit/GOVERNANCE_AUTOMATION_STATUS.json | To be validated on droplet in Phase 2 | — | Governance/cockpit/SRE tooling |
| reports/audit/SRE_STATUS.json | To be validated on droplet in Phase 2 | — | SRE/cockpit/CSA tooling |
| reports/state/TRADE_CSA_STATE.json | To be validated on droplet in Phase 2 | — | CSA trade state (tooling/cockpit) |
| reports/{date}_stock-bot_combined.json | To be validated on droplet in Phase 2 | — | Situation, learning readiness, strategy comparison (date = today / historical) |
| reports/{date}_stock-bot_wheel.json | To be validated on droplet in Phase 2 | — | Wheel analytics fallback |
| reports/{date}_weekly_promotion_report.json | To be validated on droplet in Phase 2 | — | Strategy comparison |
| reports/equity_governance/equity_governance_*/lock_or_revert_decision.json | To be validated on droplet in Phase 2 | — | Governance status, situation |
| reports/effectiveness_*/effectiveness_aggregates.json | To be validated on droplet in Phase 2 | — | Governance status fallback |

---

## Config

| Source path | Exists (Y/N) | Readable | Notes |
|-------------|--------------|----------|--------|
| config/universe_wheel.yaml | To be validated on droplet in Phase 2 | — | Wheel universe health fallback |

---

## Telemetry (bundles)

| Source path | Exists (Y/N) | Readable | Notes |
|-------------|--------------|----------|--------|
| telemetry/paper_mode_intel_state.json | To be validated on droplet in Phase 2 | — | /api/paper-mode-intel-state |
| telemetry/YYYY-MM-DD/ (latest date dir) | To be validated on droplet in Phase 2 | — | /api/telemetry/latest/* |
| telemetry/YYYY-MM-DD/computed/*.json | To be validated on droplet in Phase 2 | — | Index, computed artifact fetch, health |

---

## External / runtime

| Source | Exists (Y/N) | Readable | Notes |
|--------|--------------|----------|--------|
| Alpaca API (positions, account, orders) | To be validated on droplet in Phase 2 | — | Positions, P&L reconcile, health_status last order |
| Main bot http://localhost:8081/api/sre/health | To be validated on droplet in Phase 2 | — | SRE health primary when bot running |
| Git (rev-parse HEAD) | To be validated on droplet in Phase 2 | — | /api/version, learning readiness deployed_commit |
| sre_monitoring.get_sre_health() | To be validated on droplet in Phase 2 | — | /health, /api/sre/health fallback |
| pgrep -f python.*main.py | To be validated on droplet in Phase 2 | — | /health bot_running |

---

## Phase 2 actions

1. On droplet, for each source path above: check **Exists (Y/N)** and **Readable** (dashboard process can open/read).
2. Fill in the table with results (Y/N, and any permission or path errors).
3. Add any additional sources discovered from `executive_summary_generator`, `telemetry.score_telemetry`, `failure_point_monitor`, `signal_history_storage`, or `xai.explainable_logger` if they use paths not listed here.
