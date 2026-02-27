# Adversarial Review (Phase 5)

## MODEL B — Challenges
- Challenge signal rankings: small n or single-bucket dominance can make delta_mean misleading.
- Contradictions: a group (e.g. regime_macro) may be EDGE_POSITIVE while a sub-component is EDGE_NEGATIVE; resolve by preferring group-level when sample is small.
- Misleading correlations: pnl variance may be driven by one symbol or one day; check stability across buckets.
- Noise: signals with |corr_pnl| < 0.05 or |delta_mean| < 0.01 may be noise.

## MODEL C — Data integrity
- Attribution: confirm replay_results contain group_sums and (when available) components.
- Stale caches: if most records have zero or identical components, pipeline may be using pre-attribution data.
- Composite consistency: group_sums (uw + regime_macro + other_components) should align with sum of components.

## Raw edge analysis (reference)

# Multi-Model Edge Analysis (Phase 4)

## WINNER vs LOSER profiles

| signal | mean_winner | mean_loser | delta_mean | corr_pnl | n |
|--------|-------------|------------|------------|----------|---|

## EDGE_POSITIVE (increase weight)


## EDGE_NEGATIVE (decrease or zero weight)


## Bucket summary (from pipeline)

# Blocked-trade score bucket analysis

| bucket | n | mean_pnl_pct | win_rate | median_pnl_pct | mean_expectancy_contribution |
|--------|---|--------------|----------|----------------|------------------------------|

# Signal-group expectancy (strong vs weak)

| group | n_strong | n_weak | mean_pnl_strong | mean_pnl_weak | delta_expectancy |
|-------|----------|--------|-----------------|---------------|------------------|
| uw | 0 | 0 | - | - | - |
| regime_macro | 0 | 0 | - | - | - |
| other_components | 0 | 0 | - | - | - |