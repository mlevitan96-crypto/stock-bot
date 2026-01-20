# WEIGHT_TUNING_SUMMARY_2026-01-20

## Data source
- `Droplet local logs/state`
- generated_utc: `2026-01-20T21:46:51.659617+00:00`

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
- v2_better vol_20d_mean: `0.0000` | beta_mean: `0.000`
- v1_better vol_20d_mean: `0.0000` | beta_mean: `0.000`

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

## Why these weights (brutally honest)
- Today’s tuning is driven by observed differences in shadow vs real symbol outcomes and the regime/posture context.
- We strengthen penalties for **misaligned direction vs posture** and modestly reward **high-vol/high-beta** only when aligned.
- We add an explicit UW-strength bonus (conviction+trade_count) and a futures/premarket alignment term (SPY/QQQ overnight proxy).
