# Signal coverage and waste (Phase 4)

## Summary

- **Collected (inventory):** 56
- **Used in score:** 22
- **Waste (collected but never used):** 34 — atr_distance, beta_bonus, beta_vs_spy, calendar_catalyst, composite_pre_clamp, distance_pct, event_alignment, freshness, iv_term_skew, low_vol_penalty, options_flow, other_components, posture_confidence, premarket_bonus, qqq_overnight_ret, realized_vol_20d, regime_align_bonus, regime_macro, regime_misalign_penalty, regime_modifier, score, shaping_adj, sizing_overlay, smile_slope, spy_overnight_ret, temporal_motif, total, toxicity, uw, uw_bonus, uw_conviction, vol_bonus, whale_conviction_boost, whale_persistence
- **Broken (used but frequently missing/zero):** 0
- **Healthy (used and present):** 22
- **Crushed (contribution ~0):** 0

## Broken signals (exact missing input / where produced / where it becomes null)

- None.

## Waste (collected, not used)

- atr_distance
- beta_bonus
- beta_vs_spy
- calendar_catalyst
- composite_pre_clamp
- distance_pct
- event_alignment
- freshness
- iv_term_skew
- low_vol_penalty
- options_flow
- other_components
- posture_confidence
- premarket_bonus
- qqq_overnight_ret
- realized_vol_20d
- regime_align_bonus
- regime_macro
- regime_misalign_penalty
- regime_modifier
- score
- shaping_adj
- sizing_overlay
- smile_slope
- spy_overnight_ret
- temporal_motif
- total
- toxicity
- uw
- uw_bonus
- uw_conviction
- vol_bonus
- whale_conviction_boost
- whale_persistence

## Crushed (contribution ~0)

- None.

## DROPLET COMMANDS

```bash
cd /root/stock-bot
python3 scripts/signal_inventory_on_droplet.py
python3 scripts/signal_usage_map_on_droplet.py
python3 scripts/signal_pipeline_deep_dive_on_droplet.py
python3 scripts/signal_coverage_and_waste_report_on_droplet.py
```
