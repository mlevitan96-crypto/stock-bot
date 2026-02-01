# Canonical Intelligence Inventory

**Generated:** 2026-01-28T17:19:42.695339+00:00 (UTC)
**Scope:** Expected intelligence outputs the system is designed to produce.

---

## 1. Data sources

| Source | Path / origin |
|--------|----------------|
| Market (Alpaca) | `APIConfig.ALPACA_*; paper trades` |
| UW API (Unusual Whales) | `APIConfig.UW_BASE_URL; flow, dark pool, sentiment` |
| UW flow cache | `data/uw_flow_cache.json` |
| UW flow cache log | `data/uw_flow_cache.log.jsonl` |
| Composite cache | `data/composite_cache.json` |
| State: regime | `state/regime_detector_state.json` |
| State: market context | `state/market_context_v2.json` |
| State: regime posture | `state/regime_posture_state.json` |
| State: signal weights | `state/signal_weights.json` |
| State: internal positions | `state/internal_positions.json` |

## 2. Signal layers (Decision Intelligence Trace)

From `telemetry/decision_intelligence_trace._comps_to_signal_layers`:

- **alpha_signals**
- **flow_signals**
- **regime_signals**
- **volatility_signals**
- **dark_pool_signals**

## 3. Feature / score component families

From `config.registry.SignalComponents.ALL_COMPONENTS`:

- `flow`
- `dark_pool`
- `insider`
- `iv_term_skew`
- `smile_slope`
- `whale_persistence`
- `event_alignment`
- `temporal_motif`
- `toxicity_penalty`
- `regime_modifier`
- `congress`
- `shorts_squeeze`
- `institutional`
- `market_tide`
- `calendar_catalyst`
- `greeks_gamma`
- `ftd_pressure`
- `iv_rank`
- `oi_change`
- `etf_flow`
- `squeeze_score`
- `freshness_factor`

## 4. Score components (aggregation)

Trace `aggregation.score_components` is built from the same component dict as signal layers (per-cluster scoring).

## 5. Gates

From `main.py` (append_gate_result):

- **score_gate**
- **capacity_gate**
- **risk_gate**
- **momentum_gate**
- **directional_gate**
- **displacement_gate**

## 6. Trade intents

- **trade_intent** — emitted to `logs/run.jsonl` (entry decisions: entered or blocked)
- **exit_intent** — emitted to `logs/run.jsonl` (exit decisions)
- **cycle / complete** — cycle summaries to `logs/run.jsonl`

## 7. Post-trade / computed artifacts

| Artifact | Path (under telemetry/<date>/computed/) |
|----------|------------------------------------------|
| entry_parity_details | `entry_parity_details.json` |
| live_vs_shadow_pnl | `live_vs_shadow_pnl.json` |
| shadow_vs_live_parity | `shadow_vs_live_parity.json` |
| feature_family_summary | `feature_family_summary.json` |
| exit_intel_completeness | `exit_intel_completeness.json` |
| score_distribution_curves | `score_distribution_curves.json` |
| signal_performance | `signal_performance.json` |
| signal_weight_recommendations | `signal_weight_recommendations.json` |
| feature_equalizer_builder | `feature_equalizer_builder.json` |
| feature_value_curves | `feature_value_curves.json` |
| long_short_analysis | `long_short_analysis.json` |
| regime_sector_feature_matrix | `regime_sector_feature_matrix.json` |
| regime_timeline | `regime_timeline.json` |
| replacement_telemetry_expanded | `replacement_telemetry_expanded.json` |
| pnl_windows | `pnl_windows.json` |

## 8. Shadow artifacts

Same as post-trade; shadow vs live parity is in `shadow_vs_live_parity`, `entry_parity_details`, `live_vs_shadow_pnl`.

## 9. Dashboard-visible intelligence

From `dashboard.py` computed API: live_vs_shadow_pnl, signal_performance, signal_weight_recommendations, score_distribution_curves, shadow_vs_live_parity, entry_parity_details, feature_family_summary, exit_intel_completeness.
