# Phase 2 — Dashboard and Data Correctness Audit

**Audit date:** 2026-02-27  
**Source:** reports/DASHBOARD_ENDPOINT_MAP.md, dashboard.py routes, config/registry paths.

---

## Panel → Endpoint → File → Schema → Verification

| Panel / Endpoint | Data location (code) | Schema / expected keys | Verification result |
|------------------|----------------------|------------------------|----------------------|
| `/api/ping` | None | — | OK (health only) |
| `/api/version` | Git, process | — | OK |
| `/api/positions` | Alpaca API, `state/position_metadata.json`, `data/uw_flow_cache.json`, `state/wheel_state.json`, regime/registry paths | positions[], total_value, unrealized_pnl, day_pnl; per-position: symbol, entry_score, strategy_id | Paths use _DASHBOARD_ROOT; OK. Cross-check with Alpaca when live. |
| `/api/pnl/reconcile` | Alpaca API, `state/daily_start_equity.json`, `logs/attribution.jsonl` (LogFiles.ATTRIBUTION) | broker_day_pnl, window_pnl, attribution_closed_pnl_sum, date | OK. daily_start_equity must have date + equity for window_pnl. |
| `/api/stockbot/closed_trades` | `logs/attribution.jsonl`, `logs/exit_attribution.jsonl`, `logs/telemetry.jsonl` via _load_stock_closed_trades | closed_trades[], count; per trade: strategy_id, wheel fields, pnl, exit_reason | Deduped join; exit_attribution = v2 equity exits. Verify logs exist on droplet. |
| `/api/stockbot/wheel_analytics` | Same as closed_trades + `reports/*_stock-bot_wheel.json`, `state/wheel_state.json` | premium_sum, assigned_count, called_away_count, pnl_sum, total | Fallback when no wheel in logs. OK. |
| `/api/closed_positions` | `state/closed_positions.json` | Last 50 closed | OK. File may be missing → empty list. |
| `/api/system/health` | `state/health.json` | Supervisor health | OK. |
| `/api/system-events` | `logs/system_events.jsonl` | Event lines | OK. |
| `/api/sre/health` | localhost:8081 or `data/health_status.json`, `state/health.json` | Fallback on timeout | OK. |
| `/api/sre/self_heal_events` | `data/self_heal_events.jsonl` (CacheFiles.SELF_HEAL_EVENTS) | Event lines | OK. |
| `/api/xai/auditor` | `data/explainable_logs.jsonl`, `logs/attribution.jsonl` | Max 10k attr lines | OK. |
| `/api/xai/health`, `/api/xai/export` | `data/explainable_logs.jsonl` | Tail 500 / full | OK. |
| `/api/executive_summary` | executive_summary_generator → attribution, master_trade_log | Timeframe query | OK. |
| `/api/health_status` | Alpaca API, `data/live_orders.jsonl`, `logs/orders.jsonl`, `logs/trading.jsonl`, `state/bot_heartbeat.json` | Last order + heartbeat | OK. |
| `/api/scores/distribution`, `/api/scores/components`, `/api/scores/telemetry` | telemetry.score_telemetry | Lookback param | OK. |
| `/api/failure_points` | SRE/failure_point_monitor | — | OK. |
| `/api/signal_history` | signal_history_storage | — | OK. |
| `/api/wheel/universe_health` | `state/wheel_universe_health.json`; fallback: `config/universe_wheel.yaml`, `state/daily_universe_v2.json` | — | OK. |
| `/api/strategy/comparison` | `reports/{date}_stock-bot_combined.json`, `reports/*_weekly_promotion_report.json` | — | OK. Reports may be missing → empty or error. |
| `/api/regime-and-posture` | `state/market_context_v2.json`, `state/regime_posture_state.json` | — | OK. |
| `/api/telemetry/latest/*`, `/api/paper-mode-intel-state`, `/api/telemetry/latest/health` | telemetry/YYYY-MM-DD/computed/, paper_mode_intel_state.json, master_trade_log | — | OK. |

---

## Path resolution rule

**Verified:** Dashboard uses `(_DASHBOARD_ROOT / path).resolve()` for relative paths (`_DASHBOARD_ROOT = Path(__file__).resolve().parent`). Cwd-independent.

---

## Cross-check: key metrics vs canonical sources

| Metric | Canonical source | Dashboard source | Note |
|--------|------------------|------------------|------|
| P&L (closed) | effectiveness_aggregates.json, attribution sum | /api/executive_summary, /api/stockbot/closed_trades | Reconcile with effectiveness_aggregates.total_pnl when run. |
| Win rate | effectiveness_aggregates.win_rate | From closed_trades aggregation or executive_summary | Run effectiveness report; compare. |
| Trade count | effectiveness_aggregates.joined_count, attribution + exit_attribution join | closed_trades count | joined_count = joined closed trades; dashboard may cap lines (max_attribution_lines=10000). |
| Giveback | effectiveness_aggregates.avg_profit_giveback, exit_effectiveness | Not directly on dashboard | Dashboard does not expose giveback; use effectiveness reports. |

**Recommendation:** Add a single “Governance / effectiveness” panel or link that shows path to latest effectiveness_aggregates.json and key fields (joined_count, win_rate, expectancy_per_trade, avg_profit_giveback) when file exists, or “Run effectiveness report” hint.

---

## Mismatches / stale panels

- **strategy/comparison:** Depends on generate_daily_strategy_reports; if not run, panel may be empty or stale. Mark as “depends on daily report job.”
- **giveback:** Not on dashboard; stopping condition uses giveback. Document that giveback is in effectiveness reports only.

---

## Recommendations

1. **Canonical:** Treat `logs/attribution.jsonl` + `logs/exit_attribution.jsonl` as canonical for closed equity trades; dashboard closed_trades is derived from these.
2. **Deprecate:** None identified; keep all endpoints but document dependencies (reports, state files).
3. **Non-canonical:** `state/closed_positions.json` is “last 50” only; for full history use attribution + exit_attribution.
4. **DROPLET_REQUIRED:** Confirm presence and freshness of state/*.json and logs/*.jsonl on droplet for each endpoint that reads files.
