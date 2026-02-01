# UW Signal Engine Map (Cache → Features)

**Generated:** 2026-01-28T16:44:56.247012+00:00

| UW endpoint | Feature extractor | Signal layer | Active/Inactive |
|-------------|-------------------|--------------|-----------------|
| dark_pool | uw_enrichment_v2 (dark_pool_notional, sentiment) | uw_composite_v2 (dp_component) | dark_pool_signals | active |
| etf_inflow_outflow | uw_enrichment_v2 (etf_flow) | uw_composite_v2 (etf_flow_component) | alpha_signals | active |
| greek_exposure | uw_enrichment_v2 (greeks) | uw_composite_v2 (greeks_gamma) | alpha_signals | active |
| greeks | uw_enrichment_v2 (greeks) | uw_composite_v2 (greeks_gamma_component, max_pain) | alpha_signals | active |
| iv_rank | uw_enrichment_v2 (iv_rank) | uw_composite_v2 (iv_rank_component) | alpha_signals | active |
| market_tide | uw_enrichment_v2 (market_tide) | uw_composite_v2 (tide_component) | regime_signals | active |
| max_pain | uw_composite_v2 (from greeks) | uw_composite_v2 (gamma_resistance_levels) | alpha_signals | active |
| net_impact | daemon (_top_net_impact) | uw_composite_v2 (indirect via symbol_intel) | flow_signals | active |
| oi_change | uw_enrichment_v2 (oi_change) | uw_composite_v2 (oi_change_component) | alpha_signals | active |
| option_flow | daemon (flow_trades) | uw_composite_v2 (flow_component, flow_trade_count) | flow_signals | active |
| shorts_ftds | uw_enrichment_v2 (shorts_ftds) | uw_composite_v2 (shorts_component, ftd_pressure) | alpha_signals | active |

**Note:** Inactive = data missing in cache; component uses neutral default (e.g. 0.2).