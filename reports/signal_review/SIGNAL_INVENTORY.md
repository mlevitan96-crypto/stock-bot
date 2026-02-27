# Signal inventory (Phase 1A)

Discovered **56** signals. Source: uw_composite_v2.py components + main.py breakdown.

| signal_name | source_file | compute_entrypoint | status |
|-------------|-------------|--------------------|--------|
| atr_distance | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| beta_bonus | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| beta_vs_spy | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| calendar | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| calendar_catalyst | uw_composite_v2.py | get_weight(component, regime) | USED_IN_SCORE |
| composite_pre_clamp | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| congress | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| dark_pool | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| distance_pct | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| etf_flow | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| event | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| event_alignment | uw_composite_v2.py | get_weight(component, regime) | USED_IN_SCORE |
| flow | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| freshness | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| freshness_factor | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| ftd_pressure | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| greeks_gamma | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| insider | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| institutional | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| iv_rank | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| iv_skew | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| iv_term_skew | uw_composite_v2.py | get_weight(component, regime) | USED_IN_SCORE |
| low_vol_penalty | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| market_tide | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| motif_bonus | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| oi_change | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| options_flow | uw_composite_v2.py | get_weight(component, regime) | USED_IN_SCORE |
| other_components | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| posture_confidence | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| premarket_bonus | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| qqq_overnight_ret | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| realized_vol_20d | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| regime | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| regime_align_bonus | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| regime_macro | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| regime_misalign_penalty | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| regime_modifier | uw_composite_v2.py | get_weight(component, regime) | USED_IN_SCORE |
| score | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| shaping_adj | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| shorts_squeeze | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| sizing_overlay | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| smile | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| smile_slope | uw_composite_v2.py | get_weight(component, regime) | USED_IN_SCORE |
| spy_overnight_ret | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| squeeze_score | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| temporal_motif | uw_composite_v2.py | get_weight(component, regime) | USED_IN_SCORE |
| total | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| toxicity | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| toxicity_penalty | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| uw | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| uw_bonus | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| uw_conviction | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| vol_bonus | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| whale | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| whale_conviction_boost | uw_composite_v2.py | _compute_composite_score_core | USED_IN_SCORE |
| whale_persistence | uw_composite_v2.py | get_weight(component, regime) | USED_IN_SCORE |

## DROPLET COMMANDS

```bash
cd /root/stock-bot
python3 scripts/signal_inventory_on_droplet.py
```
