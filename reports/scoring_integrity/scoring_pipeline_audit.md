# Scoring Pipeline Audit

## Composite score construction

- **Entry:** uw_composite_v2.compute_composite_score_v2(symbol, enriched_data, regime) — used in main.py for cluster scoring and fallback.
- **Core:** _compute_composite_score_core (weights, components sum, freshness decay, whale_conviction_boost, clamp 0–8).
- **Weight application:** Each component = weight * raw_value; weights from WEIGHTS_V3 and optional adaptive.
- **Normalization:** conviction clipped 0–1; sentiment mapped to sign; components bounded per type.
- **Scaling:** Final clamp max(0, min(8, composite_score)).
- **Freshness decay:** composite_score = composite_raw * freshness (from enriched_data).
- **Defaults:** conviction None → 0.5; sentiment None → NEUTRAL; missing expanded_intel key → 0 for that component.

## Live vs diagnostic

- **Live:** main.py loads uw_flow_cache in process; clusters built with composite_score from compute_composite_score_v2; in decide_and_execute, score is then adjusted (signal_quality, UW, survivorship, regime/macro). **Expectancy gate previously used c.get("composite_score", score) → raw cluster score; min gate used adjusted score → mismatch.**
- **Diagnostic:** Scripts often call compute_composite_score_v2/v3 with same cache file; no signal_quality/uw/survivorship/structural_intelligence → raw composite only. So diagnostic score can match cluster’s composite_score but not the adjusted score used for the min gate.

## Finding

- **Gate score consistency (fixed):** Expectancy gate now uses the same `score` as the min-score gate (adjusted score), not the raw cluster composite. So score_floor_breach and min gate are aligned.
