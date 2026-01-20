# WEIGHT_TUNING_SUMMARY_2026-01-20

## Data source
- `Droplet local logs/state`
- generated_utc: `2026-01-20T22:05:58.829474+00:00`

## Snapshot
- symbols_with_real_pnl: `49`
- symbols_with_shadow_pnl: `52`
- score_compare_events: `2381`

## Classification (shadow vs real)
- v2_better: `31`
- v1_better: `21`
- both_good: `8`
- both_bad: `18`

## Empirical risk profile (means)
- v2_better vol_20d_mean: `0.3080` | beta_mean: `1.070`
- v1_better vol_20d_mean: `0.5259` | beta_mean: `1.653`

## Current COMPOSITE_WEIGHTS_V2 (shadow-only)
- version: `2026-01-20_wt1`
- vol_bonus_max: `0.7`
- low_vol_penalty_max: `-0.15`
- beta_bonus_max: `0.45`
- uw_bonus_max: `0.25`
- premarket_align_bonus: `0.15`
- premarket_misalign_penalty: `-0.15`
- regime_align_bonus: `0.55`
- regime_misalign_penalty: `-0.35`
- misalign_dampen: `0.25`

## Weight deltas vs baseline (pre-tuning defaults)
- vol_bonus_max: `0.6` → `0.7` (Δ `+0.100`)
- low_vol_penalty_max: `-0.1` → `-0.15` (Δ `-0.050`)
- beta_bonus_max: `0.4` → `0.45` (Δ `+0.050`)
- uw_bonus_max: `0.2` → `0.25` (Δ `+0.050`)
- premarket_align_bonus: `0.1` → `0.15` (Δ `+0.050`)
- premarket_misalign_penalty: `-0.1` → `-0.15` (Δ `-0.050`)
- regime_align_bonus: `0.5` → `0.55` (Δ `+0.050`)
- regime_misalign_penalty: `-0.25` → `-0.35` (Δ `-0.100`)
- misalign_dampen: `0.25` → `0.25` (Δ `+0.000`)

## Why these weights (brutally honest)
- Today’s tuning is driven by observed differences in shadow vs real symbol outcomes and the regime/posture context.
- We strengthen penalties for **misaligned direction vs posture** and modestly reward **high-vol/high-beta** only when aligned.
- We add an explicit UW-strength bonus (conviction+trade_count) and a futures/premarket alignment term (SPY/QQQ overnight proxy).
