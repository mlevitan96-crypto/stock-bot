# Signal Chain Audit

## Providers and data flow

| Layer | Component | Location | Output |
|-------|-----------|----------|--------|
| Cache | UW flow daemon | uw_flow_daemon.py | data/uw_flow_cache.json |
| Enrichment | enrich_signal | uw_enrichment_v2 | enriched dict (sentiment, conviction, expanded intel) |
| Composite | compute_composite_score_v2/v3 | uw_composite_v2 | score, components, whale_conviction_boost |
| Clusters | Cluster build | main.py (callers of composite) | clusters with composite_score, source |

## Composite score construction (uw_composite_v2)

- **Weights:** WEIGHTS_V3; adaptive via get_adaptive_weights(regime).
- **Components (21):** flow, dark_pool, insider, iv_term_skew, smile_slope, whale_persistence, event_alignment, motif, toxicity, regime_modifier, congress, shorts_squeeze, institutional, market_tide, calendar_catalyst, greeks_gamma, ftd_pressure, iv_rank, oi_change, etf_flow, squeeze_score.
- **Formula:** composite_raw = sum(components); composite_score = composite_raw * freshness; then whale_conviction_boost; clamp [0, 8].
- **Contract:** Missing conviction → 0.5 (neutral); missing sentiment → NEUTRAL.

## Execution and freshness

- **Executed:** main.py uses uw_flow_cache (loaded by process), enrich_signal per symbol, compute_composite_score_v2 for cluster path.
- **Non-zero:** Depends on cache and expanded_intel; zero conviction/sentiment yields low flow component.
- **Fresh:** freshness from enrichment; applied as multiplier in composite.
- **Contributing:** All components summed; zero weight or missing data → component 0.

## Verification

- Run diagnostic: load uw_flow_cache.json, for N symbols call enrich_signal then compute_composite_score_v2; check score and component keys non-null.
- Compare live cycle_summary (gate.jsonl) considered vs cache key count.
