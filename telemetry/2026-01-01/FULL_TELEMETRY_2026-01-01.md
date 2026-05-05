# FULL TELEMETRY — 2026-01-01

## 1. Overview
- Generated at (UTC): **2026-05-01T22:29:58.023136+00:00**
- Data source: **local_no_ssh**
- Git head: **453b8952d9c4**

### Status snapshot
- v1 status: **unknown / no live log found**
- v2 status: **v2-only engine (paper)**
- Daemon health: **healthy** (pid_ok=True lock_ok=True poll_fresh=True)
- Intel health checks: **{'ok': 18, 'stale': 1}** (n=19)

## 1b. Computed Artifacts Index
- `exit_intel_completeness.json` — Exit attribution completeness + missing-key counts.
- `feature_equalizer_builder.json` — Equalizer-ready per-feature realized outcome summaries.
- `feature_value_curves.json` — Per-feature value curves (binned) vs realized PnL.
- `long_short_analysis.json` — Long vs short expectancy stats from realized exits.
- `pnl_windows.json` — Rolling (24h/48h/5d) PnL/expectancy/win-rate + per-symbol table.
- `regime_sector_feature_matrix.json` — Regime/Sector → per-feature realized PnL matrix.
- `regime_timeline.json` — Hourly (UTC) regime/posture timeline (best-effort) + day summary.
- `replacement_telemetry_expanded.json` — Replacement rates by feature/family + cause histogram + anomaly flag.
- `score_distribution_curves.json` — Score histograms + delta histograms by feature family (long/short split).
- `signal_performance.json` — Per-signal (feature-family) win rate/expectancy/trade count + regime/side breakdowns.
- `signal_weight_recommendations.json` — Advisory (read-only) signal weight delta suggestions derived from performance.

## 2. v2 Trading Summary (paper)
- Live entries (opened): **0**
- Live exits: **0**
- Closed trades (realized): **0**
- Total PnL (USD): **0.0**
- Replacement events: **0**
- Exit reasons distribution: **{}**

### Best trades (by realized PnL, USD)
- None (no realized exits today).

### Worst trades (by realized PnL, USD)
- None (no realized exits today).

### Replacement logic events
- None.

### Long vs short asymmetry (realized exits)
- **overall**: n=0 win_rate=0.0 avg_pnl_usd=0.0 expectancy_usd=0.0
- **long**: n=0 win_rate=0.0 avg_pnl_usd=0.0 expectancy_usd=0.0
- **short**: n=0 win_rate=0.0 avg_pnl_usd=0.0 expectancy_usd=0.0

## 3. Entry Intelligence
- UW feature usage (non-zero adjustments counts): **{}**
- Entry sector distribution (closed trades): **{}**
- Entry regime distribution (closed trades): **{}**

## 4. Exit Intelligence
- Exit score stats (v2_exit_score): **{}**
- Score deterioration stats (entry_v2_score - exit_v2_score): **{}**
- Exit reasons distribution: **{}**
- Exit intel completeness: complete_rate=0.0 (complete=0 / total=0)

## 4b. Feature Value Curve Highlights
- **flow_strength** best[0.0,0.0] avg_pnl_usd=0.0 | worst[0.0,0.0] avg_pnl_usd=0.0 | monotonicity=0.0
- **darkpool_bias** best[0.0,0.0] avg_pnl_usd=0.0 | worst[0.0,0.0] avg_pnl_usd=0.0 | monotonicity=0.0
- **sentiment** best[0.0,0.0] avg_pnl_usd=0.0 | worst[0.0,0.0] avg_pnl_usd=0.0 | monotonicity=0.0
- **earnings_proximity** best[0.0,0.0] avg_pnl_usd=0.0 | worst[0.0,0.0] avg_pnl_usd=0.0 | monotonicity=0.0
- **sector_alignment** best[0.0,0.0] avg_pnl_usd=0.0 | worst[0.0,0.0] avg_pnl_usd=0.0 | monotonicity=0.0
- **regime_alignment** best[0.0,0.0] avg_pnl_usd=0.0 | worst[0.0,0.0] avg_pnl_usd=0.0 | monotonicity=0.0

## 5. PnL Analysis
### PnL by symbol (USD)

### PnL by sector (USD)

### PnL by regime (USD)

### PnL by exit reason (USD)

## 6. Attribution
- Entry attribution tail (`logs/uw_attribution.jsonl`):

```
{"symbol": "SPY", "timestamp": "2026-04-29T22:49:03.560490+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "sentiment_score": 1.0, "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.0864, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "UNKNOWN", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.0, "darkpool_weight": 1.0, "earnings_weight": 1.0, "short_interest_weight": 1.0}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "SPY", "timestamp": "2026-04-29T22:49:24.082295+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "sentiment_score": 1.0, "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.0864, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "UNKNOWN", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.0, "darkpool_weight": 1.0, "earnings_weight": 1.0, "short_interest_weight": 1.0}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-05-01T22:18:37.315355+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "sentiment_score": 1.0, "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.10152, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-05-01T22:18:37.486512+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "sentiment_score": 1.0, "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.1692, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
```

- Exit attribution tail (`logs/exit_attribution.jsonl`):

```
(missing)
```

## 6b. Feature Equalizer Snapshot (v2-only, realized)
- No feature-level stats available (no realized exits with attribution).

## 7. Health & Reliability
- Daemon health summary: `{'timestamp': '2026-05-01T22:29:57.246796+00:00', 'status': 'healthy', 'pid_ok': True, 'lock_ok': True, 'poll_fresh': True, 'crash_loop': False, 'endpoint_errors': False}`
- Intel health summary: `{'ts': '2026-05-01T22:29:57.132769+00:00', 'status_counts': {'ok': 18, 'stale': 1}, 'check_count': 19}`
- System events tail (`logs/system_events.jsonl`):

```
{"timestamp": "2026-05-01T22:18:31.476553+00:00", "subsystem": "uw", "event_type": "uw_rate_limit_block", "severity": "WARN", "details": {"reason": "per_minute_cap", "endpoint": "/api/market/top-net-impact", "params": {"limit": 1}, "wait_s": 20.950035572052002}}
{"timestamp": "2026-05-01T22:18:31.728902+00:00", "subsystem": "uw", "event_type": "uw_invalid_endpoint_attempt", "severity": "ERROR", "details": {"endpoint": "/INVALID_ENDPOINT", "caller": "C:/Dev/stock-bot/scripts/run_regression_checks.py:198:main", "timestamp": 1777673911.7286046}}
{"timestamp": "2026-05-01T22:18:32.502529+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "sniper": 14, "radar": 0, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-05-01T22:18:32.836703+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-05-01T22:18:33.149515+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-05-01T22:18:34.855990+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "sniper": 14, "radar": 0, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-05-01T22:18:35.182118+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-05-01T22:18:35.489645+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-05-01T22:18:37.406675+00:00", "subsystem": "data_armor", "event_type": "uw_composite_input_coerced", "severity": "INFO", "details": {"note": "poisoned_or_blank_uw_fields_normalized"}, "symbol": "AAPL"}
{"timestamp": "2026-05-01T22:18:45.167375+00:00", "subsystem": "environment", "event_type": "missing_alpaca_trade_api", "severity": "WARN", "details": {"note": "alpaca_trade_api not installed in this environment"}}
{"timestamp": "2026-05-01T22:18:45.167849+00:00", "subsystem": "environment", "event_type": "missing_flask_library", "severity": "WARN", "details": {"note": "flask not installed in this environment"}}
{"timestamp": "2026-05-01T22:29:41.339049+00:00", "subsystem": "environment", "event_type": "missing_alpaca_trade_api", "severity": "WARN", "details": {"note": "alpaca_trade_api not installed in this environment"}}
{"timestamp": "2026-05-01T22:29:41.339836+00:00", "subsystem": "environment", "event_type": "missing_flask_library", "severity": "WARN", "details": {"note": "flask not installed in this environment"}}
{"timestamp": "2026-05-01T22:29:51.875605+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "sniper": 14, "radar": 0, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-05-01T22:29:52.205268+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-05-01T22:29:52.492064+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-05-01T22:29:52.808922+00:00", "subsystem": "uw", "event_type": "uw_call", "severity": "INFO", "details": {"endpoint": "/api/market/top-net-impact", "endpoint_name": "default", "params": {"limit": 1}, "status": 200, "cache_hit": false, "latency_ms": 1, "caller": "<string>:1:<module>"}}
{"timestamp": "2026-05-01T22:29:52.809577+00:00", "subsystem": "uw", "event_type": "uw_rate_limit_block", "severity": "WARN", "details": {"reason": "per_minute_cap", "endpoint": "/api/market/top-net-impact", "params": {"limit": 1}, "wait_s": 59.97116017341614}}
{"timestamp": "2026-05-01T22:29:53.067660+00:00", "subsystem": "uw", "event_type": "uw_invalid_endpoint_attempt", "severity": "ERROR", "details": {"endpoint": "/INVALID_ENDPOINT", "caller": "C:/Dev/stock-bot/scripts/run_regression_checks.py:198:main", "timestamp": 1777674593.0673766}}
{"timestamp": "2026-05-01T22:29:53.738263+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "sniper": 14, "radar": 0, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-05-01T22:29:54.060695+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-05-01T22:29:54.414595+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-05-01T22:29:56.162150+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "sniper": 14, "radar": 0, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-05-01T22:29:56.457193+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-05-01T22:29:56.760621+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
```

## 8. Promotion Readiness Notes
- Reasons v2 looks ready:
  - Daemon + intel health look OK (best-effort)
- Reasons v2 is not ready:
  - No realized exits today (cannot validate exit quality/PnL)
- Questions to investigate:
  - Are there consistent divergences between v1_score vs v2_score on high-quality symbols today?
  - Do replacement exits improve realized outcomes vs holding?

## Universe & Intel snapshots (best-effort)
- Universe v1: n=14 (file present=True)
- Universe v2: n=14 (file present=True)
- Regime state: NEUTRAL, conf=0.25

## Regime/Sector Matrix Highlights

## PnL Windows (rolling)
- As-of (UTC): **2026-05-01T22:29:58.112088+00:00**
- **24h** pnl_usd=0.0 expectancy_usd=0.0 win_rate=0.0 (insufficient_data=True)
- **48h** pnl_usd=0.0 expectancy_usd=0.0 win_rate=0.0 (insufficient_data=True)
- **5d** pnl_usd=0.0 expectancy_usd=0.0 win_rate=0.0 (insufficient_data=True)

## Signal Performance (realized)
- None (no realized trades or no signal-family snapshots available).

## Score Distribution Summary
- **flow** delta_hist.n=0 bins=32
- **darkpool** delta_hist.n=0 bins=32
- **alignment** delta_hist.n=0 bins=32

## Replacement Telemetry Summary
- Replacement rate: **0.0** (repl=0 / total=0)
- Replacement anomaly detected: **False**

## Bundle contents (high-level)
- Copied files: **25**
- Truncated (tailed) logs: **0**

## Missing artifacts (best-effort)
- **state**:
  - state/market_context_v2.json
  - state/regime_posture_state.json
  - state/symbol_risk_features.json
- **logs**:
  - logs/live_trades.jsonl
  - logs/run_once.jsonl
  - logs/worker_error.jsonl
  - logs/scoring_flow.jsonl
  - logs/scoring_pipeline.jsonl
  - logs/scoring.jsonl
  - logs/gate.jsonl
  - logs/exit.jsonl
- **reports**:
  - reports/V2_TUNING_SUGGESTIONS_2026-01-01.md

