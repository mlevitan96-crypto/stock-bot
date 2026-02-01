# UW Ingestion Audit (Daemon → Cache)

**Generated:** 2026-01-28T16:44:56.247012+00:00

**Cache path:** /root/stock-bot/data/uw_flow_cache.json
**Cache exists:** True

## Per-endpoint

### dark_pool
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['dark_pool_levels', 'dark_pool']
- **Data in cache:** yes

### etf_inflow_outflow
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['etf_flow']
- **Data in cache:** yes

### greek_exposure
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['greek_exposure', 'greeks']
- **Data in cache:** yes

### greeks
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['greeks']
- **Data in cache:** yes

### iv_rank
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['iv_rank']
- **Data in cache:** yes

### market_tide
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['market_tide', '_market_tide']
- **Data in cache:** yes

### max_pain
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['max_pain']
- **Data in cache:** yes

### net_impact
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['top_net_impact', '_top_net_impact']
- **Data in cache:** yes

### oi_change
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['oi_change']
- **Data in cache:** yes

### option_flow
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['option_flow', 'flow_trades']
- **Data in cache:** yes

### shorts_ftds
- **Daemon attempts fetch:** yes (uw_flow_daemon.py SmartPoller)
- **Cache keys:** ['shorts_ftds', 'ftd_pressure', 'ftd', 'shorts']
- **Data in cache:** yes
