# ALPACA service health (20260326_1707Z)

## systemctl status (no-pager, truncated)

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Thu 2026-03-26 17:07:32 UTC; 13s ago
   Main PID: 1572209 (systemd_start.s)
      Tasks: 10 (limit: 9483)
     Memory: 759.3M (peak: 2.1G)
        CPU: 7.578s
     CGroup: /system.slice/stock-bot.service
             ├─1572209 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1572210 /root/stock-bot/venv/bin/python deploy_supervisor.py
             └─1572226 /root/stock-bot/venv/bin/python -u dashboard.py

Mar 26 17:07:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [dashboard]  * Running on all addresses (0.0.0.0)
Mar 26 17:07:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [dashboard]  * Running on http://127.0.0.1:5001
Mar 26 17:07:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [dashboard]  * Running on http://104.236.102.57:5001
Mar 26 17:07:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [dashboard] Press CTRL+C to quit
Mar 26 17:07:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [dashboard] [Dashboard] Alpaca API connected
Mar 26 17:07:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [dashboard] [Dashboard] Dependencies loaded
Mar 26 17:07:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [SUPERVISOR] [2026-03-26 17:07:41 UTC] Service dashboard started successfully (PID: 1572226)
Mar 26 17:07:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [SUPERVISOR] [2026-03-26 17:07:41 UTC] Waiting for port 5000 to be ready...
Mar 26 17:07:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [SUPERVISOR] [2026-03-26 17:07:41 UTC] Port 5000 is READY - deployment should succeed
Mar 26 17:07:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1572210]: [SUPERVISOR] [2026-03-26 17:07:41 UTC] Waiting 15s for health checks to stabilize...

● uw-flow-daemon.service - Unusual Whales Flow Daemon (single instance)
     Loaded: loaded (/etc/systemd/system/uw-flow-daemon.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-03-26 17:07:44 UTC; 1s ago
   Main PID: 1572234 (python)
      Tasks: 1 (limit: 9483)
     Memory: 66.9M (peak: 94.5M)
        CPU: 1.195s
     CGroup: /system.slice/uw-flow-daemon.service
             └─1572234 /root/stock-bot/venv/bin/python /root/stock-bot/uw_flow_daemon.py

Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "congress_recent_trades", "time_remaining": 10492.77729177475}
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "option_flow:AAPL", "base_endpoint": "option_flow", "force_first": false, "last": 1774544580.3120506, "interval": 150, "time_since_last": 285.169766664505}
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling allowed {"endpoint": "option_flow:AAPL"}
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_get: API call attempt {"url": "https://api.unusualwhales.com/api/option-trades/flow-alerts", "has_api_key": true}
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] ✅ RAW PAYLOAD RECEIVED: https://api.unusualwhales.com/api/option-trades/flow-alerts | Status: 200 | Data keys: ['data', 'newer_than', 'older_than']
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_get: API call success {"url": "https://api.unusualwhales.com/api/option-trades/flow-alerts", "status": 200, "has_data": true, "data_type": "list", "data_keys": ["data", "newer_than", "older_than"]}
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Retrieved 100 flow trades for AAPL
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Polling AAPL: got 100 raw trades
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_update_cache: Cache update start {"ticker": "AAPL", "data_keys": ["flow_trades", "sentiment", "conviction", "total_premium", "call_premium", "put_premium", "net_premium", "trade_count", "flow"], "has_data": true}
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_update_cache: Cache update complete {"ticker": "AAPL", "cache_size": 56, "ticker_data_keys": ["market_tide", "iv_term_skew", "smile_slope", "insider", "flow_trades", "sentiment", "conviction", "total_premium", "call_premium", "put_premium", "net_premium", "trade_count", "flow", "_last_update"]}

● stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000)
     Loaded: loaded (/etc/systemd/system/stock-bot-dashboard.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-03-26 17:07:44 UTC; 1s ago
   Main PID: 1572238 (python3)
      Tasks: 6 (limit: 9483)
     Memory: 80.4M (peak: 80.4M)
        CPU: 1.341s
     CGroup: /system.slice/stock-bot-dashboard.service
             └─1572238 /usr/bin/python3 /root/stock-bot/dashboard.py

Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: [Dashboard] Server starting on port 5000
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]:  * Serving Flask app 'dashboard'
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]:  * Debug mode: off
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]:  * Running on all addresses (0.0.0.0)
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]:  * Running on http://127.0.0.1:5000
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]:  * Running on http://104.236.102.57:5000
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: Press CTRL+C to quit
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: [Dashboard] Alpaca API connected
Mar 26 17:07:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1572238]: [Dashboard] Dependencies loaded
```

## journalctl last 200 lines (per unit)

Captured in full in `reports/ALPACA_FORWARD_DROPLET_RAW_20260326_1905Z.json` → `steps.journals_last_200`.

Units:

- `stock-bot.service`
- `uw-flow-daemon.service`
- `stock-bot-dashboard.service`
