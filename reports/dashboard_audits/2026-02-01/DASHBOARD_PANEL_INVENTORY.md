# Dashboard Panel Inventory

**Generated:** 2026-02-01T02:00:13.619527+00:00

---

## Tabs and panels

## Tab: Positions

### Positions stats + table
- **Endpoints:**
  - `/api/positions` (GET)
  - `/api/health_status` (GET)
- **Evidence sources:** Alpaca API, state/position_metadata.json, data/uw_flow_cache.json, state/bot_heartbeat.json, data/live_orders.jsonl
- **Freshness SLA:** 120 sec

## Tab: Signal Review

### Signal history (last 50)
- **Endpoints:**
  - `/api/signal_history` (GET)
- **Evidence sources:** signal_history_storage, shadow_tracker
- **Freshness SLA:** 300 sec

## Tab: SRE Monitoring

### SRE health + funnel + ledger
- **Endpoints:**
  - `/api/sre/health` (GET)
  - `/api/sre/self_heal_events` (GET)
- **Evidence sources:** data/health_status.json, sre_monitoring, data/self_heal_events.jsonl, logs/run.jsonl, logs/attribution.jsonl
- **Freshness SLA:** 120 sec

## Tab: Executive Summary

### Executive summary
- **Endpoints:**
  - `/api/executive_summary` (GET)
- **Evidence sources:** executive_summary_generator, logs/attribution.jsonl, reports
- **Freshness SLA:** 86400 sec

## Tab: Natural Language Auditor (XAI)

### XAI auditor
- **Endpoints:**
  - `/api/xai/auditor` (GET)
  - `/api/xai/export` (GET)
- **Evidence sources:** xai/explainable_logger, data/explainable_logs.jsonl, logs/attribution.jsonl
- **Freshness SLA:** 600 sec

## Tab: Trading Readiness

### Failure points
- **Endpoints:**
  - `/api/failure_points` (GET)
- **Evidence sources:** failure_point_monitor
- **Freshness SLA:** 300 sec

## Tab: Telemetry

### Telemetry latest index + computed + health
- **Endpoints:**
  - `/api/telemetry/latest/index` (GET)
  - `/api/telemetry/latest/computed` (GET)
  - `/api/telemetry/latest/health` (GET)
- **Evidence sources:** telemetry/YYYY-MM-DD/computed/*.json, telemetry/YYYY-MM-DD/computed/live_vs_shadow_pnl.json, telemetry/YYYY-MM-DD/computed/signal_performance.json
- **Freshness SLA:** 86400 sec
