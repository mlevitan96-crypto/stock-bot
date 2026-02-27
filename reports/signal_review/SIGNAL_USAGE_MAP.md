# Signal usage map (Phase 1B)

| signal_name | USED_IN_SCORE | USED_IN_GATE_SCORE | WEIGHT_SOURCE |
|-------------|---------------|---------------------|---------------|
| flow | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| dark_pool | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| insider | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| iv_skew | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| smile | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| whale | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| event | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| motif_bonus | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| toxicity_penalty | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| regime | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| congress | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| shorts_squeeze | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| institutional | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| market_tide | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| calendar | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| greeks_gamma | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| ftd_pressure | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| iv_rank | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| oi_change | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| etf_flow | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| squeeze_score | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |
| freshness_factor | True | True | uw_composite_v2.py WEIGHTS_V3 / get_weig... |

CONTRIBUTION_PATH: components[signal] * weight -> sum -> clamp(0,1) -> composite_pre_clamp; adjustments -> score -> gate

## DROPLET COMMANDS

```bash
cd /root/stock-bot
python3 scripts/signal_usage_map_on_droplet.py
```
