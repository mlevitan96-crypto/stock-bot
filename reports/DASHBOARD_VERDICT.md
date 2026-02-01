# Dashboard Verdict

**Generated:** 2026-01-28T16:08:19.715054+00:00

## Per-section

1. Pre-flight (service, daemon, no audit, heartbeat): **PASS**
2. Endpoint cache status (exists, readable, <30m, parseable): **PASS**
3. Schema integrity: **PASS**
4. Panel wiring: **PASS**
5. System events: **PASS**

## Endpoint summary

- **Healthy (data present):** ['dark_pool', 'market_tide', 'net_impact', 'oi_change', 'option_flow']
- **Missing (no data in cache):** ['etf_inflow_outflow', 'greek_exposure', 'greeks', 'iv_rank', 'max_pain', 'shorts_ftds']
- **Stale (cache >30m old):** []
- **Miswired:** []

## Statement

**Dashboard endpoint connectivity and data integrity are PASS.**