# FULL TELEMETRY — 2026-01-01

## 1. Overview
- Generated at (UTC): **2026-01-24T02:44:23.807219+00:00**
- Data source: **local_no_ssh**
- Git head: **717f97c8e4ed**

### Status snapshot
- v1 status: **unknown / no live log found**
- v2 status: **v2-only engine (paper)**
- Daemon health: **healthy** (pid_ok=True lock_ok=True poll_fresh=True)
- Intel health checks: **{'ok': 19}** (n=19)

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
{"symbol": "AAPL", "timestamp": "2026-01-24T02:15:32.586253+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.10152, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:15:32.861590+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.1692, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:20:56.328203+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.10152, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:20:56.439767+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.1692, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:23:14.456649+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.10152, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:23:14.646879+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.1692, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:35:47.675594+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.10152, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:35:47.779485+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.1692, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:41:24.875496+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.10152, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:41:25.068660+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.1692, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:42:35.772941+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.10152, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
{"symbol": "AAPL", "timestamp": "2026-01-24T02:42:35.956549+00:00", "direction": "bullish", "uw_features": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sentiment": "BULLISH", "earnings_proximity": 3, "sector_alignment": 0.1, "regime_alignment": 0.25}, "uw_contribution": {"score_delta": 0.1692, "weight_profile": {"uw_version": "2026-01-20_uw_v1", "sector_profile": {"sector": "TECH", "version": "2026-01-20_sector_profiles_v1", "multipliers": {"flow_weight": 1.2, "darkpool_weight": 1.1, "earnings_weight": 1.0, "short_interest_weight": 0.8}}, "regime_profile": {"regime_label": "NEUTRAL", "version": "2026-01-20_regime_v1", "alignment": 0.25}}}, "composite_version": "v2", "uw_intel_version": "2026-01-20_uw_v1"}
```

- Exit attribution tail (`logs/exit_attribution.jsonl`):

```
{"symbol": "AAPL", "timestamp": "2026-01-22T23:49:33.509115+00:00", "entry_timestamp": "2026-01-22T23:49:33.501015+00:00", "exit_reason": "profit", "pnl": 4500.0, "pnl_pct": 9.0, "entry_price": 100.0, "exit_price": 1000.0, "qty": 5.0, "time_in_trade_minutes": 0.00013553333333333334, "entry_uw": {"uw_intel_version": "test", "v2_uw_adjustments": {"darkpool_bias": 0.01, "flow_strength": 0.05, "regime_alignment": 0.01, "sector_alignment": 0.01, "total": 0.08}, "v2_uw_inputs": {"darkpool_bias": 0.1, "flow_strength": 0.6, "regime_alignment": 0.2, "sector_alignment": 0.2}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}, "v2_uw_sector_profile": {"sector": "TECH"}}, "exit_uw": {"uw_intel_version": "test", "v2_uw_inputs": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sector_alignment": 0.2, "regime_alignment": 0.2}, "v2_uw_adjustments": {"flow_strength": 0.05, "darkpool_bias": 0.01, "sector_alignment": 0.01, "regime_alignment": 0.01, "total": 0.08}, "v2_uw_sector_profile": {"sector": "TECH"}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.10000000000000009, "relative_strength_deterioration": 0.0125, "v2_exit_score": 0.0031250000000000028, "v2_exit_components": {"flow_deterioration": 0.0, "darkpool_deterioration": 0.0, "sentiment_deterioration": 0.0, "score_deterioration": 0.0125, "regime_shift": 0.0, "sector_shift": 0.0, "vol_expansion": 0.0, "thesis_invalidated": 0.0, "earnings_risk": 0.0, "overnight_flow_risk": 0.0}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-22T23:49:34.543865+00:00", "entry_timestamp": "2026-01-01T00:00:00+00:00", "exit_reason": "profit", "pnl": null, "pnl_pct": null, "entry_price": null, "exit_price": null, "qty": null, "time_in_trade_minutes": null, "entry_uw": {}, "exit_uw": {}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.1, "relative_strength_deterioration": 0.0, "v2_exit_score": 0.5, "v2_exit_components": {"score_deterioration": 0.1}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T00:43:35.885364+00:00", "entry_timestamp": "2026-01-23T00:43:35.872770+00:00", "exit_reason": "profit", "pnl": 4500.0, "pnl_pct": 9.0, "entry_price": 100.0, "exit_price": 1000.0, "qty": 5.0, "time_in_trade_minutes": 0.00021035000000000002, "entry_uw": {"uw_intel_version": "test", "v2_uw_adjustments": {"darkpool_bias": 0.01, "flow_strength": 0.05, "regime_alignment": 0.01, "sector_alignment": 0.01, "total": 0.08}, "v2_uw_inputs": {"darkpool_bias": 0.1, "flow_strength": 0.6, "regime_alignment": 0.2, "sector_alignment": 0.2}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}, "v2_uw_sector_profile": {"sector": "TECH"}}, "exit_uw": {"uw_intel_version": "test", "v2_uw_inputs": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sector_alignment": 0.2, "regime_alignment": 0.2}, "v2_uw_adjustments": {"flow_strength": 0.05, "darkpool_bias": 0.01, "sector_alignment": 0.01, "regime_alignment": 0.01, "total": 0.08}, "v2_uw_sector_profile": {"sector": "TECH"}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.10000000000000009, "relative_strength_deterioration": 0.0125, "v2_exit_score": 0.0031250000000000028, "v2_exit_components": {"flow_deterioration": 0.0, "darkpool_deterioration": 0.0, "sentiment_deterioration": 0.0, "score_deterioration": 0.0125, "regime_shift": 0.0, "sector_shift": 0.0, "vol_expansion": 0.0, "thesis_invalidated": 0.0, "earnings_risk": 0.0, "overnight_flow_risk": 0.0}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T00:43:36.446658+00:00", "entry_timestamp": "2026-01-01T00:00:00+00:00", "exit_reason": "profit", "pnl": null, "pnl_pct": null, "entry_price": null, "exit_price": null, "qty": null, "time_in_trade_minutes": null, "entry_uw": {}, "exit_uw": {}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.1, "relative_strength_deterioration": 0.0, "v2_exit_score": 0.5, "v2_exit_components": {"score_deterioration": 0.1}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T00:57:25.107423+00:00", "entry_timestamp": "2026-01-23T00:57:25.091555+00:00", "exit_reason": "profit", "pnl": 4500.0, "pnl_pct": 9.0, "entry_price": 100.0, "exit_price": 1000.0, "qty": 5.0, "time_in_trade_minutes": 0.00026558333333333333, "entry_uw": {"uw_intel_version": "test", "v2_uw_adjustments": {"darkpool_bias": 0.01, "flow_strength": 0.05, "regime_alignment": 0.01, "sector_alignment": 0.01, "total": 0.08}, "v2_uw_inputs": {"darkpool_bias": 0.1, "flow_strength": 0.6, "regime_alignment": 0.2, "sector_alignment": 0.2}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}, "v2_uw_sector_profile": {"sector": "TECH"}}, "exit_uw": {"uw_intel_version": "test", "v2_uw_inputs": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sector_alignment": 0.2, "regime_alignment": 0.2}, "v2_uw_adjustments": {"flow_strength": 0.05, "darkpool_bias": 0.01, "sector_alignment": 0.01, "regime_alignment": 0.01, "total": 0.08}, "v2_uw_sector_profile": {"sector": "TECH"}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.10000000000000009, "relative_strength_deterioration": 0.0125, "v2_exit_score": 0.0031250000000000028, "v2_exit_components": {"flow_deterioration": 0.0, "darkpool_deterioration": 0.0, "sentiment_deterioration": 0.0, "score_deterioration": 0.0125, "regime_shift": 0.0, "sector_shift": 0.0, "vol_expansion": 0.0, "thesis_invalidated": 0.0, "earnings_risk": 0.0, "overnight_flow_risk": 0.0}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T00:57:26.224278+00:00", "entry_timestamp": "2026-01-01T00:00:00+00:00", "exit_reason": "profit", "pnl": null, "pnl_pct": null, "entry_price": null, "exit_price": null, "qty": null, "time_in_trade_minutes": null, "entry_uw": {}, "exit_uw": {}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.1, "relative_strength_deterioration": 0.0, "v2_exit_score": 0.5, "v2_exit_components": {"score_deterioration": 0.1}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T01:24:33.594354+00:00", "entry_timestamp": "2026-01-23T01:24:33.576124+00:00", "exit_reason": "profit", "pnl": 4500.0, "pnl_pct": 9.0, "entry_price": 100.0, "exit_price": 1000.0, "qty": 5.0, "time_in_trade_minutes": 0.00030481666666666666, "entry_uw": {"uw_intel_version": "test", "v2_uw_adjustments": {"darkpool_bias": 0.01, "flow_strength": 0.05, "regime_alignment": 0.01, "sector_alignment": 0.01, "total": 0.08}, "v2_uw_inputs": {"darkpool_bias": 0.1, "flow_strength": 0.6, "regime_alignment": 0.2, "sector_alignment": 0.2}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}, "v2_uw_sector_profile": {"sector": "TECH"}}, "exit_uw": {"uw_intel_version": "test", "v2_uw_inputs": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sector_alignment": 0.2, "regime_alignment": 0.2}, "v2_uw_adjustments": {"flow_strength": 0.05, "darkpool_bias": 0.01, "sector_alignment": 0.01, "regime_alignment": 0.01, "total": 0.08}, "v2_uw_sector_profile": {"sector": "TECH"}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.10000000000000009, "relative_strength_deterioration": 0.0125, "v2_exit_score": 0.0031250000000000028, "v2_exit_components": {"flow_deterioration": 0.0, "darkpool_deterioration": 0.0, "sentiment_deterioration": 0.0, "score_deterioration": 0.0125, "regime_shift": 0.0, "sector_shift": 0.0, "vol_expansion": 0.0, "thesis_invalidated": 0.0, "earnings_risk": 0.0, "overnight_flow_risk": 0.0}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T01:24:34.655059+00:00", "entry_timestamp": "2026-01-01T00:00:00+00:00", "exit_reason": "profit", "pnl": null, "pnl_pct": null, "entry_price": null, "exit_price": null, "qty": null, "time_in_trade_minutes": null, "entry_uw": {}, "exit_uw": {}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.1, "relative_strength_deterioration": 0.0, "v2_exit_score": 0.5, "v2_exit_components": {"score_deterioration": 0.1}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T01:25:24.616121+00:00", "entry_timestamp": "2026-01-23T01:25:24.608505+00:00", "exit_reason": "profit", "pnl": 4500.0, "pnl_pct": 9.0, "entry_price": 100.0, "exit_price": 1000.0, "qty": 5.0, "time_in_trade_minutes": 0.00012731666666666665, "entry_uw": {"uw_intel_version": "test", "v2_uw_adjustments": {"darkpool_bias": 0.01, "flow_strength": 0.05, "regime_alignment": 0.01, "sector_alignment": 0.01, "total": 0.08}, "v2_uw_inputs": {"darkpool_bias": 0.1, "flow_strength": 0.6, "regime_alignment": 0.2, "sector_alignment": 0.2}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}, "v2_uw_sector_profile": {"sector": "TECH"}}, "exit_uw": {"uw_intel_version": "test", "v2_uw_inputs": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sector_alignment": 0.2, "regime_alignment": 0.2}, "v2_uw_adjustments": {"flow_strength": 0.05, "darkpool_bias": 0.01, "sector_alignment": 0.01, "regime_alignment": 0.01, "total": 0.08}, "v2_uw_sector_profile": {"sector": "TECH"}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.10000000000000009, "relative_strength_deterioration": 0.0125, "v2_exit_score": 0.0031250000000000028, "v2_exit_components": {"flow_deterioration": 0.0, "darkpool_deterioration": 0.0, "sentiment_deterioration": 0.0, "score_deterioration": 0.0125, "regime_shift": 0.0, "sector_shift": 0.0, "vol_expansion": 0.0, "thesis_invalidated": 0.0, "earnings_risk": 0.0, "overnight_flow_risk": 0.0}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T01:25:25.171073+00:00", "entry_timestamp": "2026-01-01T00:00:00+00:00", "exit_reason": "profit", "pnl": null, "pnl_pct": null, "entry_price": null, "exit_price": null, "qty": null, "time_in_trade_minutes": null, "entry_uw": {}, "exit_uw": {}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.1, "relative_strength_deterioration": 0.0, "v2_exit_score": 0.5, "v2_exit_components": {"score_deterioration": 0.1}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T15:54:43.420597+00:00", "entry_timestamp": "2026-01-23T15:54:43.390868+00:00", "exit_reason": "profit", "pnl": 4500.0, "pnl_pct": 9.0, "entry_price": 100.0, "exit_price": 1000.0, "qty": 5.0, "time_in_trade_minutes": 0.0004959833333333333, "entry_uw": {"uw_intel_version": "test", "v2_uw_adjustments": {"darkpool_bias": 0.01, "flow_strength": 0.05, "regime_alignment": 0.01, "sector_alignment": 0.01, "total": 0.08}, "v2_uw_inputs": {"darkpool_bias": 0.1, "flow_strength": 0.6, "regime_alignment": 0.2, "sector_alignment": 0.2}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}, "v2_uw_sector_profile": {"sector": "TECH"}}, "exit_uw": {"uw_intel_version": "test", "v2_uw_inputs": {"flow_strength": 0.6, "darkpool_bias": 0.1, "sector_alignment": 0.2, "regime_alignment": 0.2}, "v2_uw_adjustments": {"flow_strength": 0.05, "darkpool_bias": 0.01, "sector_alignment": 0.01, "regime_alignment": 0.01, "total": 0.08}, "v2_uw_sector_profile": {"sector": "TECH"}, "v2_uw_regime_profile": {"regime_label": "NEUTRAL"}}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.10000000000000009, "relative_strength_deterioration": 0.0125, "v2_exit_score": 0.0031250000000000028, "v2_exit_components": {"flow_deterioration": 0.0, "darkpool_deterioration": 0.0, "sentiment_deterioration": 0.0, "score_deterioration": 0.0125, "regime_shift": 0.0, "sector_shift": 0.0, "vol_expansion": 0.0, "thesis_invalidated": 0.0, "earnings_risk": 0.0, "overnight_flow_risk": 0.0}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
{"symbol": "AAPL", "timestamp": "2026-01-23T15:54:44.216000+00:00", "entry_timestamp": "2026-01-01T00:00:00+00:00", "exit_reason": "profit", "pnl": null, "pnl_pct": null, "entry_price": null, "exit_price": null, "qty": null, "time_in_trade_minutes": null, "entry_uw": {}, "exit_uw": {}, "entry_regime": "NEUTRAL", "exit_regime": "NEUTRAL", "entry_sector_profile": {"sector": "TECH"}, "exit_sector_profile": {"sector": "TECH"}, "score_deterioration": 0.1, "relative_strength_deterioration": 0.0, "v2_exit_score": 0.5, "v2_exit_components": {"score_deterioration": 0.1}, "replacement_candidate": null, "replacement_reasoning": null, "composite_version": "v2"}
```

## 6b. Feature Equalizer Snapshot (v2-only, realized)
- No feature-level stats available (no realized exits with attribution).

## 7. Health & Reliability
- Daemon health summary: `{'timestamp': '2026-01-24T02:44:22.829219+00:00', 'status': 'healthy', 'pid_ok': True, 'lock_ok': True, 'poll_fresh': True, 'crash_loop': False, 'endpoint_errors': False}`
- Intel health summary: `{'ts': '2026-01-24T02:44:22.695647+00:00', 'status_counts': {'ok': 19}, 'check_count': 19}`
- System events tail (`logs/system_events.jsonl`):

```
{"timestamp": "2026-01-24T02:41:21.136122+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:42:25.583525+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-01-24T02:42:25.891723+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:42:26.275280+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:42:26.599264+00:00", "subsystem": "uw", "event_type": "uw_call", "severity": "INFO", "details": {"endpoint": "/api/market/top-net-impact", "endpoint_name": "", "status": 200, "cache_hit": false, "latency_ms": 2}}
{"timestamp": "2026-01-24T02:42:26.600519+00:00", "subsystem": "uw", "event_type": "uw_rate_limit_block", "severity": "WARN", "details": {"reason": "per_minute_cap", "endpoint": "/api/market/top-net-impact", "params": {"limit": 1}, "wait_s": 59.9947624206543}}
{"timestamp": "2026-01-24T02:42:26.920113+00:00", "subsystem": "uw", "event_type": "uw_invalid_endpoint_attempt", "severity": "ERROR", "details": {"endpoint": "/INVALID_ENDPOINT", "caller": "C:/Dev/stock-bot/scripts/run_regression_checks.py:198:main", "timestamp": 1769222546.9197624}}
{"timestamp": "2026-01-24T02:42:28.145609+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-01-24T02:42:28.532445+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:42:28.888394+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:42:31.935667+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-01-24T02:42:32.338631+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:42:32.774437+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:44:17.574775+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-01-24T02:44:17.805682+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:44:18.048681+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:44:18.288403+00:00", "subsystem": "uw", "event_type": "uw_call", "severity": "INFO", "details": {"endpoint": "/api/market/top-net-impact", "endpoint_name": "", "status": 200, "cache_hit": false, "latency_ms": 1}}
{"timestamp": "2026-01-24T02:44:18.289016+00:00", "subsystem": "uw", "event_type": "uw_rate_limit_block", "severity": "WARN", "details": {"reason": "per_minute_cap", "endpoint": "/api/market/top-net-impact", "params": {"limit": 1}, "wait_s": 59.99706292152405}}
{"timestamp": "2026-01-24T02:44:18.495766+00:00", "subsystem": "uw", "event_type": "uw_invalid_endpoint_attempt", "severity": "ERROR", "details": {"endpoint": "/INVALID_ENDPOINT", "caller": "C:/Dev/stock-bot/scripts/run_regression_checks.py:198:main", "timestamp": 1769222658.495445}}
{"timestamp": "2026-01-24T02:44:19.316024+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-01-24T02:44:19.574307+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:44:19.862702+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:44:21.803663+00:00", "subsystem": "uw", "event_type": "daily_universe_built", "severity": "INFO", "details": {"daily": 14, "core": 10, "mode": "mock", "version": "2026-01-20_universe_v1", "universe_scoring_v2_version": "2026-01-20_universe_v2", "wrote_daily_universe_v2": true}}
{"timestamp": "2026-01-24T02:44:22.062385+00:00", "subsystem": "uw", "event_type": "premarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
{"timestamp": "2026-01-24T02:44:22.320310+00:00", "subsystem": "uw", "event_type": "postmarket_intel_ready", "severity": "INFO", "details": {"symbols": 14, "mode": "mock", "uw_intel_version": "2026-01-20_uw_v1"}}
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
- As-of (UTC): **2026-01-24T02:44:23.942257+00:00**
- **24h** pnl_usd=4500.0 expectancy_usd=4500.0 win_rate=1.0 (insufficient_data=False)
- **48h** pnl_usd=22500.0 expectancy_usd=4500.0 win_rate=1.0 (insufficient_data=False)
- **5d** pnl_usd=22500.0 expectancy_usd=4500.0 win_rate=1.0 (insufficient_data=False)

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
- Copied files: **23**
- Truncated (tailed) logs: **1**
  - C:/Dev/stock-bot/telemetry/2026-01-01/logs/attribution.jsonl (tailed_last_lines=2000 original_bytes=1459321)

## Missing artifacts (best-effort)
- **state**:
  - state/market_context_v2.json
  - state/regime_posture_state.json
  - state/symbol_risk_features.json
- **logs**:
  - logs/live_trades.jsonl
  - logs/run.jsonl
  - logs/run_once.jsonl
  - logs/worker_error.jsonl
  - logs/scoring_flow.jsonl
  - logs/scoring_pipeline.jsonl
  - logs/scoring.jsonl
  - logs/gate.jsonl
  - logs/orders.jsonl
  - logs/exit.jsonl
- **reports**:
  - reports/V2_TUNING_SUGGESTIONS_2026-01-01.md

