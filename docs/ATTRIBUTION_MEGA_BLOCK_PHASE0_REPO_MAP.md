# Phase 0: Repo Map — Granular Intelligence Attribution

**Generated:** 2026-02-17 | **Purpose:** Single reference for scoring, UW, entry/exit, lifecycle, telemetry, backtest, lab mode, dashboards.

---

## 1. UW Ingestion / Parsing / Normalization

| Concern | File Path(s) | Notes |
|--------|--------------|--------|
| **Central UW HTTP client** | `src/uw/uw_client.py` | Rate limit, cache, daily budget; validates endpoints via `uw_spec_loader`. |
| **UW endpoint validation** | `src/uw/uw_spec_loader.py` | Loads API spec; `is_valid_uw_path()` used before any call. |
| **UW attribution helpers** | `src/uw/uw_attribution.py` | Attribution-related UW helpers. |
| **Flow normalization (main)** | `main.py` (class `UWClient`, ~line 2550) | `_normalize_flow_trade()` — direction, bid/ask prem, sweeps. |
| **Legacy UW client** | `main.py` (~2400+) | In-repo `UWClient` with `get_option_flow`, `_normalize_flow_trade`, etc. |
| **Canonical rules** | `docs/uw/README.md` | All UW calls via `src/uw/uw_client.py`; scoring reads only from cached artifacts. |
| **Artifact locations** | `data/uw_flow_cache.json`, `state/premarket_intel.json`, `state/postmarket_intel.json`, `data/uw_expanded_intel.json` | Populated by uw_flow_daemon, premarket/postmarket scripts, intel producers. |

---

## 2. Intelligence Objects & Scoring Pipeline

| Concern | File Path(s) | Notes |
|--------|--------------|--------|
| **Composite score (V3)** | `uw_composite_v2.py` | `compute_composite_score_v3()` (~line 514); `_compute_composite_score_core()`; WEIGHTS_V3, ENTRY_THRESHOLDS. |
| **Entry gate** | `uw_composite_v2.py` | `should_enter_v2()` — threshold, toxicity, freshness. |
| **Component calculators** | `uw_composite_v2.py` | e.g. `compute_flow_component`, `compute_dark_pool_component`, `compute_insider_component`, `compute_institutional_component`, `compute_market_tide_component`, `compute_calendar_component`, greeks_gamma, ftd_pressure, iv_rank, oi_change, squeeze_score, toxicity, regime_modifier, etc. |
| **Signal enrichment** | `uw_composite_v2.py` | `enrich_signal()` — pulls from cache/expanded intel. |
| **UW composite (signals)** | `signals/uw_composite.py` | Alternative/legacy composite. |
| **UW weight tuner** | `signals/uw_weight_tuner.py` | Ingests attribution log; adaptive weights. |
| **Score telemetry** | `telemetry/score_telemetry.py` | `record(symbol, score, components, metadata)`; persists to state. |
| **Pipeline audit doc** | `SIGNAL_SCORE_PIPELINE_AUDIT.md` | Flow: clusters → composite → should_enter_v2 → decide_and_execute. |

---

## 3. Entry Decision Function(s)

| Concern | File Path(s) | Notes |
|--------|--------------|--------|
| **Entry gate (score/threshold)** | `uw_composite_v2.py::should_enter_v2()` | Score vs threshold, toxicity < 0.90, freshness >= 0.25. |
| **Decision & execute** | `main.py::StrategyEngine.decide_and_execute()` (~7329) | Regime gate, concentration, theme risk, composite score + regime/macro multipliers, expectancy gate, momentum ignition, cooldown, position exists, trade_guard, submit_entry. |
| **Submit entry** | `main.py::AlpacaExecutor.submit_entry()` | Spread watchdog, size validation, limit/market order. |
| **Expectancy gate** | `v3_2_features.py::ExpectancyGate.should_enter()` | Minimum expected value gate. |

---

## 4. Exit Decision Function(s) + Exit Reason Codes

| Concern | File Path(s) | Notes |
|--------|--------------|--------|
| **Evaluate exits** | `main.py::AlpacaExecutor.evaluate_exits()` (~5886) | Central exit loop; builds exit_signals, close_reason. |
| **Composite close reason** | `main.py::build_composite_close_reason()` (~175) | time_exit, trail_stop, signal_decay, flow_reversal, profit_target, drawdown, momentum_reversal, regime_protection, displacement, stale_position, structural_exit, primary_reason. |
| **Exit score v2** | `src/exit/exit_score_v2.py::compute_exit_score_v2()` | Returns (exit_score, components, reason); components: flow_deterioration, darkpool_deterioration, sentiment_deterioration, score_deterioration, regime_shift, sector_shift, vol_expansion, thesis_invalidated, earnings_risk, overnight_flow_risk. |
| **Structural exit** | `structural_intelligence/structural_exit.py` | StructuralExit. |
| **Stops / profit targets** | `src/exit/stops_v2.py`, `src/exit/profit_targets_v2.py` | Stop and target logic. |
| **Exit reason taxonomy** | Implicit in `build_composite_close_reason` + exit_score_v2 reason strings | time_exit, trail_stop, signal_decay, flow_reversal, profit_target, stop_loss, regime_protection, displacement, stale_position, structural_exit, v2_exit(replacement|profit|stop|intel_deterioration|hold). |

---

## 5. Trade Lifecycle State Machine / Position Manager

| Concern | File Path(s) | Notes |
|--------|--------------|--------|
| **State persistence** | `state_manager.py` | StateManager; open_positions, realized_pnl, last_trade_per_symbol; atomic_write_json; reconciliation with Alpaca. |
| **Position metadata** | `config/registry.py::StateFiles.POSITION_METADATA` | `state/position_metadata.json` — per-symbol entry_score, ts, side, etc. |
| **Reconciliation** | `position_reconciliation_loop.py::PositionReconcilerV2` | Reconciles positions with broker. |
| **Executor (positions)** | `main.py::AlpacaExecutor` | Holds positions, evaluate_exits, submit_entry/close. |

---

## 6. Telemetry / Logging Layer + Persistence

| Concern | File Path(s) | Notes |
|--------|--------------|--------|
| **Attribution log (canonical)** | `config/registry.py::LogFiles.ATTRIBUTION` | `logs/attribution.jsonl` — used by main, dashboard, EOD. |
| **Entry attribution** | `main.py::log_attribution()` (~1706) | Writes to attribution + master_trade_log + signal snapshot. |
| **Exit attribution** | `main.py::log_exit_attribution()` (~1825) | Writes to attribution, master_trade_log, exit_attribution (v2), signal_context. |
| **Master trade log** | `utils/master_trade_log.py` | `logs/master_trade_log.jsonl` — append_master_trade. |
| **Exit attribution (v2)** | `src/exit/exit_attribution.py` | `logs/exit_attribution.jsonl` — build_exit_attribution_record, append_exit_attribution. |
| **Signal snapshots** | `telemetry/signal_snapshot_writer.py` | `logs/signal_snapshots.jsonl` — ENTRY_DECISION, ENTRY_FILL, EXIT_DECISION, EXIT_FILL. |
| **Signal context** | `telemetry/signal_context_logger.py` | `logs/signal_context.jsonl` — decision-level signal state. |
| **Score telemetry** | `telemetry/score_telemetry.py` | State file for scores/components; dashboard /api/scores/*. |
| **Telemetry logger** | `telemetry/logger.py` | Daily postmortem, live orders, ops errors, learning, portfolio, risk, gov events. |
| **Log path registry** | `config/registry.py` | LogFiles, CacheFiles, StateFiles — single source of truth for paths. |

---

## 7. Backtest Runner + Data Model

| Concern | File Path(s) | Notes |
|--------|--------------|--------|
| **Historical replay engine** | `historical_replay_engine.py` | HistoricalReplayEngine; load_signals from attribution; run_backtest; SimulatedTrade, BacktestMetrics. |
| **30d backtest on droplet** | `scripts/run_30d_backtest_droplet.py`, `board/eod/run_30d_backtest_on_droplet.sh` | Runs backtest on droplet. |
| **Backtest and push** | `scripts/run_backtest_on_droplet_and_push.py` | Run backtest and push results. |
| **Signal source for backtest** | `data/uw_attribution.jsonl`, `logs/attribution.jsonl`, `logs/composite_attribution.jsonl` | Per BACKTEST_ENGINE_README. |

---

## 8. Synthetic Lab Mode (Replay / Injection)

| Concern | File Path(s) | Notes |
|--------|--------------|--------|
| **Replay signal injection** | `scripts/replay_signal_injection.py` | Injects raw signals at (symbol, timestamp) for backtest; REPLAY_SIGNAL_KEYS, make_cached_load_bars. |
| **Inject signals into backtest dir** | `scripts/inject_signals_into_backtest_dir.py` | Injects signals into a backtest directory. |
| **Mock signal injection** | `mock_signal_injection.py` | Perfect whale signal for SRE sentinel. |
| **Fake signal test** | `inject_fake_signal_test.py` | SignalInjectionTest; create_fake_cluster, trace through flow. |
| **V2 synthetic trade test** | `scripts/run_v2_synthetic_trade_test.py` | Injected mode: --symbol, --entry_price, --exit_price, --fake_ts_start, etc. |
| **Replay week multi-scenario** | `scripts/replay_week_multi_scenario.py` | Multi-scenario replay. |
| **Replay exit timing** | `scripts/replay_exit_timing_counterfactuals.py` | Exit timing counterfactuals. |

---

## 9. Dashboard Endpoints + Schemas

| Concern | File Path(s) | Notes |
|--------|--------------|--------|
| **Dashboard app** | `dashboard.py` | Flask (or similar) app; all /api/* routes. |
| **Endpoint map** | `reports/DASHBOARD_ENDPOINT_MAP.md` | Panel → endpoint → data location. |
| **Panel inventory** | `data/dashboard_panel_inventory.json`, `reports/DASHBOARD_PANEL_INVENTORY.md` | Tabs, panels, endpoints, expected_schema. |
| **Closed trades / PnL** | `/api/stockbot/closed_trades`, `/api/pnl/reconcile` | attribution.jsonl, exit_attribution.jsonl, master_trade_log. |
| **Scores** | `/api/scores/distribution`, `/api/scores/components`, `/api/scores/telemetry` | telemetry.score_telemetry. |
| **Executive summary** | `/api/executive_summary` | executive_summary_generator → attribution, master_trade_log. |
| **XAI auditor** | `/api/xai/auditor`, `/api/xai/export` | explainable_logs.jsonl, attribution.jsonl. |
| **Positions** | `/api/positions`, `/api/health_status` | Alpaca, position_metadata, uw_flow_cache, bot_heartbeat. |

---

## 10. Panel → Endpoint → Backend Producer → Schema → Source of Truth

| Panel / Tab | Endpoint(s) | Backend Producer | Schema (key fields) | Source of Truth |
|-------------|-------------|------------------|----------------------|------------------|
| Positions | `/api/positions`, `/api/health_status` | AlpacaExecutor, state files | positions[], total_value, last_order, doctor | Alpaca API, state/position_metadata.json, state/bot_heartbeat.json |
| Closed trades | `/api/stockbot/closed_trades` | Read attribution + exit_attribution | closed_trades[] (symbol, pnl, exit_reason, …) | logs/attribution.jsonl, logs/exit_attribution.jsonl |
| PnL reconcile | `/api/pnl/reconcile` | Dashboard handler | date, reconciled PnL | Alpaca, logs/attribution.jsonl, state/daily_start_equity.json |
| Signal Review | `/api/signal_history` | signal_history_storage | signals[], last_signal_timestamp | signal_history_storage |
| SRE Monitoring | `/api/sre/health`, `/api/sre/self_heal_events` | SRE, health module | health, self_heal_events | state/health.json, data/self_heal_events.jsonl |
| Executive Summary | `/api/executive_summary` | executive_summary_generator | timeframe, summary stats | logs/attribution.jsonl, logs/master_trade_log.jsonl |
| XAI Auditor | `/api/xai/auditor`, `/api/xai/export` | explainable logger | explainable lines | data/explainable_logs.jsonl, logs/attribution.jsonl |
| Scores | `/api/scores/distribution`, `/api/scores/components`, `/api/scores/telemetry` | telemetry.score_telemetry | scores, components, lookback | telemetry state (score_telemetry) |
| Telemetry latest | `/api/telemetry/latest/index`, `/api/telemetry/latest/computed`, `/api/telemetry/latest/health` | Telemetry dir reader | computed/*.json | telemetry/YYYY-MM-DD/computed/ |
| Regime & posture | `/api/regime-and-posture` | State file reader | market_context, regime_posture | state/market_context_v2.json, state/regime_posture_state.json |

---

## Summary: Where to Touch for Attribution Mega-Block

- **Schema & contracts:** New schema under `schema/` or `config/`; extend `LogFiles` if new logs.
- **UW decomposition:** `src/uw/uw_client.py` (normalize), `uw_composite_v2.py` (flow/dark_pool/insider components), new `uw_micro_signals.py` for micro-features.
- **Scoring decomposition:** `uw_composite_v2.py` — emit full component tree + contributions; config for weights.
- **Entry/exit attribution:** `main.py::log_attribution`, `main.py::log_exit_attribution` — write new attribution schema; `src/exit/exit_attribution.py` for v2 exit row.
- **Persistence:** `logs/attribution.jsonl` (canonical), `logs/master_trade_log.jsonl`, `logs/exit_attribution.jsonl`; optional dedicated `logs/attribution_v2.jsonl` or versioned path.
- **Backtest/lab:** `historical_replay_engine.py`, `scripts/run_30d_backtest_droplet.py`, `scripts/replay_signal_injection.py` — emit same attribution records, support injectable components.
- **Dashboards:** `dashboard.py` — new/updated endpoints for component breakdown, exit quality; `reports/DASHBOARD_ENDPOINT_MAP.md` and panel inventory.
