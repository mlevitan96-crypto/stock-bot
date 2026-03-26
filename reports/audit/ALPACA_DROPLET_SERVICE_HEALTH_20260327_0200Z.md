# Alpaca droplet service health (20260327_0200Z)

## stock-bot.service

### status

`
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Thu 2026-03-26 17:35:16 UTC; 3min 20s ago
   Main PID: 1578354 (systemd_start.s)
      Tasks: 33 (limit: 9483)
     Memory: 1.2G (peak: 1.6G)
        CPU: 2min 22.950s
     CGroup: /system.slice/stock-bot.service
             ├─1578354 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1578357 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1578406 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1578974 /root/stock-bot/venv/bin/python -u main.py
             └─1578994 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Reasons: {'too_young': 32, 'pnl_too_high': 0, 'score_advantage_insufficient': 0, 'in_cooldown': 0}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Sample positions:
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AAPL: age=0.0h, pnl=-0.58%, orig_score=4.09, advantage=-0.53, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AMD: age=0.0h, pnl=-0.19%, orig_score=4.30, advantage=-0.74, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     BA: age=0.0h, pnl=0.11%, orig_score=3.55, advantage=0.01, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     C: age=0.0h, pnl=-0.06%, orig_score=5.58, advantage=-2.02, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     CAT: age=0.0h, pnl=0.19%, orig_score=5.42, advantage=-1.86, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WMT: BLOCKED by max_positions_reached (Alpaca positions: 32, executor.opens: 32, max: 32), no displacement candidates
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BA: Processing cluster - direction=bearish, initial_score=4.10, source=composite_v3
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG LOW: Processing cluster - direction=bearish, initial_score=3.51, source=composite_v3
`

## uw-flow-daemon.service

### status

`
● uw-flow-daemon.service - Unusual Whales Flow Daemon (single instance)
     Loaded: loaded (/etc/systemd/system/uw-flow-daemon.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-03-26 17:07:44 UTC; 30min ago
   Main PID: 1572234 (python)
      Tasks: 1 (limit: 9483)
     Memory: 141.4M (peak: 153.6M)
        CPU: 5min 21.111s
     CGroup: /system.slice/uw-flow-daemon.service
             └─1572234 /root/stock-bot/venv/bin/python /root/stock-bot/uw_flow_daemon.py

Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "shorts_ftds:XLE", "base_endpoint": "shorts_ftds", "force_first": false, "last": 1774546531.2771711, "interval": 7200, "time_since_last": 185.96930813789368}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "shorts_ftds:XLE", "time_remaining": 7014.030691862106}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "max_pain:XLE", "base_endpoint": "max_pain", "force_first": false, "last": 1774545162.2702663, "interval": 1800, "time_since_last": 1554.97642827034}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "max_pain:XLE", "time_remaining": 245.02357172966003}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "insider:XLE", "base_endpoint": "insider", "force_first": false, "last": 1774469121.819349, "interval": 86400, "time_since_last": 77595.42749547958}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "insider:XLE", "time_remaining": 8804.572504520416}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "calendar:XLE", "base_endpoint": "calendar", "force_first": false, "last": 1774381132.353602, "interval": 604800, "time_since_last": 165584.946621418}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "calendar:XLE", "time_remaining": 439215.053378582}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "institutional_ownership:XLE", "base_endpoint": "institutional_ownership", "force_first": false, "last": 1774469122.007861, "interval": 86400, "time_since_last": 77595.29283690453}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "institutional_ownership:XLE", "time_remaining": 8804.707163095474}
`

## stock-bot-dashboard.service

### status

`
● stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000)
     Loaded: loaded (/etc/systemd/system/stock-bot-dashboard.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-03-26 17:37:40 UTC; 1min 0s ago
   Main PID: 1580958 (python3)
      Tasks: 5 (limit: 9483)
     Memory: 239.0M (peak: 283.6M)
        CPU: 8.249s
     CGroup: /system.slice/stock-bot-dashboard.service
             └─1580958 /usr/bin/python3 /root/stock-bot/dashboard.py

Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=signal_performance HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=signal_weight_recommendations HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=blocked_counterfactuals_summary HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=signal_profitability HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=exit_quality_summary HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=gate_profitability HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=intelligence_recommendations HTTP/1.1" 200 -
`

### journal (last 400) stock-bot.service

`
/2026 17:38:04] "GET /api/cockpit HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG C: Processing cluster - direction=bearish, initial_score=4.94, source=composite_v3
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] 2026-03-26 17:38:04,701 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 11 with computed signals
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] 2026-03-26 17:38:04,701 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG HOOD: Processing cluster - direction=bearish, initial_score=4.32, source=composite_v3
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG MRNA: Processing cluster - direction=bearish, initial_score=4.13, source=composite_v3
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG MS: Processing cluster - direction=bearish, initial_score=4.81, source=composite_v3
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] 2026-03-26 17:38:04,912 [CACHE-ENRICH] INFO: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /health HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GOOGL: Processing cluster - direction=bearish, initial_score=4.75, source=composite_v3
Mar 26 17:38:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG NIO: Processing cluster - direction=bearish, initial_score=4.12, source=composite_v3
Mar 26 17:38:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLK: Processing cluster - direction=bearish, initial_score=4.69, source=composite_v3
Mar 26 17:38:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG COP: Processing cluster - direction=bearish, initial_score=4.53, source=composite_v3
Mar 26 17:38:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG UNH: Processing cluster - direction=bearish, initial_score=4.03, source=composite_v3
Mar 26 17:38:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLE: Processing cluster - direction=bearish, initial_score=4.67, source=composite_v3
Mar 26 17:38:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GM: Processing cluster - direction=bearish, initial_score=4.69, source=composite_v3
Mar 26 17:38:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GM: expectancy=0.2565, should_trade=True, reason=expectancy_passed
Mar 26 17:38:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GM: PASSED expectancy gate, checking other gates...
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GM: Attempting displacement of AAPL (score advantage: n/a)
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GM: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG COIN: Processing cluster - direction=bearish, initial_score=4.15, source=composite_v3
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG AMZN: Processing cluster - direction=bearish, initial_score=4.65, source=composite_v3
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG AMZN: expectancy=0.2220, should_trade=True, reason=expectancy_passed
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG AMZN: PASSED expectancy gate, checking other gates...
Mar 26 17:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG AMZN: Attempting displacement of SOFI (score advantage: n/a)
Mar 26 17:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG AMZN: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG SLB: Processing cluster - direction=bearish, initial_score=4.14, source=composite_v3
Mar 26 17:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG F: Processing cluster - direction=bearish, initial_score=4.01, source=composite_v3
Mar 26 17:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG RIVN: Processing cluster - direction=bearish, initial_score=4.13, source=composite_v3
Mar 26 17:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLV: Processing cluster - direction=bearish, initial_score=4.53, source=composite_v3
Mar 26 17:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLV: expectancy=0.2036, should_trade=True, reason=expectancy_passed
Mar 26 17:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLV: PASSED expectancy gate, checking other gates...
Mar 26 17:38:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLV: Attempting displacement of SOFI (score advantage: n/a)
Mar 26 17:38:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLV: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BAC: Processing cluster - direction=bearish, initial_score=4.50, source=composite_v3
Mar 26 17:38:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BAC: expectancy=0.2515, should_trade=True, reason=expectancy_passed
Mar 26 17:38:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BAC: PASSED expectancy gate, checking other gates...
Mar 26 17:38:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BAC: Attempting displacement of SOFI (score advantage: n/a)
Mar 26 17:38:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BAC: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XOM: Processing cluster - direction=bearish, initial_score=3.81, source=composite_v3
Mar 26 17:38:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG DIA: Processing cluster - direction=bearish, initial_score=4.41, source=composite_v3
Mar 26 17:38:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WFC: Processing cluster - direction=bearish, initial_score=4.44, source=composite_v3
Mar 26 17:38:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WFC: expectancy=0.2237, should_trade=True, reason=expectancy_passed
Mar 26 17:38:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WFC: PASSED expectancy gate, checking other gates...
Mar 26 17:38:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 26 17:38:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Mar 26 17:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WFC: Attempting displacement of SOFI (score advantage: n/a)
Mar 26 17:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WFC: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLP: Processing cluster - direction=bearish, initial_score=4.42, source=composite_v3
Mar 26 17:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLP: expectancy=0.2393, should_trade=True, reason=expectancy_passed
Mar 26 17:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLP: PASSED expectancy gate, checking other gates...
Mar 26 17:38:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLP: Attempting displacement of SOFI (score advantage: n/a)
Mar 26 17:38:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG XLP: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG IWM: Processing cluster - direction=bearish, initial_score=4.39, source=composite_v3
Mar 26 17:38:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG SPY: Processing cluster - direction=bearish, initial_score=4.39, source=composite_v3
Mar 26 17:38:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG SPY: expectancy=0.1790, should_trade=True, reason=expectancy_passed
Mar 26 17:38:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG SPY: PASSED expectancy gate, checking other gates...
Mar 26 17:38:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG SPY: Attempting displacement of SOFI (score advantage: n/a)
Mar 26 17:38:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG SPY: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG PFE: Processing cluster - direction=bearish, initial_score=4.38, source=composite_v3
Mar 26 17:38:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG PFE: expectancy=0.1788, should_trade=True, reason=expectancy_passed
Mar 26 17:38:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG PFE: PASSED expectancy gate, checking other gates...
Mar 26 17:38:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG PFE: Attempting displacement of SOFI (score advantage: n/a)
Mar 26 17:38:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG PFE: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG CVX: Processing cluster - direction=bearish, initial_score=3.68, source=composite_v3
Mar 26 17:38:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG CVX: expectancy=0.1817, should_trade=True, reason=expectancy_passed
Mar 26 17:38:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG CVX: PASSED expectancy gate, checking other gates...
Mar 26 17:38:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG CVX: Attempting displacement of SOFI (score advantage: n/a)
Mar 26 17:38:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG CVX: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG JNJ: Processing cluster - direction=bearish, initial_score=4.32, source=composite_v3
Mar 26 17:38:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG JNJ: expectancy=0.1682, should_trade=True, reason=expectancy_passed
Mar 26 17:38:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG JNJ: PASSED expectancy gate, checking other gates...
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG JNJ: Attempting displacement of XLF (score advantage: n/a)
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG JNJ: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GS: Processing cluster - direction=bearish, initial_score=4.30, source=composite_v3
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GS: expectancy=0.1881, should_trade=True, reason=expectancy_passed
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GS: PASSED expectancy gate, checking other gates...
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GS: Attempting displacement of AAPL (score advantage: n/a)
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG GS: BLOCKED - displacement policy (displacement_no_thesis_dominance)
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WMT: Processing cluster - direction=bearish, initial_score=4.07, source=composite_v3
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WMT: expectancy=0.1695, should_trade=True, reason=expectancy_passed
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WMT: PASSED expectancy gate, checking other gates...
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] /root/stock-bot/main.py:5700: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   now = datetime.utcnow()
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG DISPLACEMENT: No candidates found for score 3.56
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Total positions: 32
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Reasons: {'too_young': 32, 'pnl_too_high': 0, 'score_advantage_insufficient': 0, 'in_cooldown': 0}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Sample positions:
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AAPL: age=0.0h, pnl=-0.58%, orig_score=4.09, advantage=-0.53, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AMD: age=0.0h, pnl=-0.19%, orig_score=4.30, advantage=-0.74, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     BA: age=0.0h, pnl=0.11%, orig_score=3.55, advantage=0.01, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     C: age=0.0h, pnl=-0.06%, orig_score=5.58, advantage=-2.02, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     CAT: age=0.0h, pnl=0.19%, orig_score=5.42, advantage=-1.86, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG WMT: BLOCKED by max_positions_reached (Alpaca positions: 32, executor.opens: 32, max: 32), no displacement candidates
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BA: Processing cluster - direction=bearish, initial_score=4.10, source=composite_v3
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG LOW: Processing cluster - direction=bearish, initial_score=3.51, source=composite_v3
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG TGT: Processing cluster - direction=bearish, initial_score=3.31, source=composite_v3
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG JPM: Processing cluster - direction=bearish, initial_score=3.96, source=composite_v3
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG JPM: expectancy=0.1593, should_trade=True, reason=expectancy_passed
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG JPM: PASSED expectancy gate, checking other gates...
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG DISPLACEMENT: No candidates found for score 3.31
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Total positions: 32
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Reasons: {'too_young': 32, 'pnl_too_high': 0, 'score_advantage_insufficient': 0, 'in_cooldown': 0}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Sample positions:
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AAPL: age=0.0h, pnl=-0.60%, orig_score=4.09, advantage=-0.78, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AMD: age=0.0h, pnl=-0.17%, orig_score=4.30, advantage=-0.98, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     BA: age=0.0h, pnl=0.11%, orig_score=3.55, advantage=-0.24, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     C: age=0.0h, pnl=-0.05%, orig_score=5.58, advantage=-2.27, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     CAT: age=0.0h, pnl=0.19%, orig_score=5.42, advantage=-2.11, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG JPM: BLOCKED by max_positions_reached (Alpaca positions: 32, executor.opens: 32, max: 32), no displacement candidates
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG V: Processing cluster - direction=bearish, initial_score=3.83, source=composite_v3
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG V: expectancy=0.1455, should_trade=True, reason=expectancy_passed
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG V: PASSED expectancy gate, checking other gates...
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG DISPLACEMENT: No candidates found for score 3.31
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Total positions: 32
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Reasons: {'too_young': 32, 'pnl_too_high': 0, 'score_advantage_insufficient': 0, 'in_cooldown': 0}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Sample positions:
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AAPL: age=0.0h, pnl=-0.60%, orig_score=4.09, advantage=-0.78, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AMD: age=0.0h, pnl=-0.17%, orig_score=4.30, advantage=-0.99, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     BA: age=0.0h, pnl=0.11%, orig_score=3.55, advantage=-0.24, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     C: age=0.0h, pnl=-0.05%, orig_score=5.58, advantage=-2.28, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     CAT: age=0.0h, pnl=0.19%, orig_score=5.42, advantage=-2.11, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG V: BLOCKED by max_positions_reached (Alpaca positions: 32, executor.opens: 32, max: 32), no displacement candidates
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG HD: Processing cluster - direction=bearish, initial_score=3.81, source=composite_v3
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG HD: expectancy=0.1281, should_trade=True, reason=expectancy_passed
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG HD: PASSED expectancy gate, checking other gates...
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG DISPLACEMENT: No candidates found for score 3.22
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Total positions: 32
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Reasons: {'too_young': 32, 'pnl_too_high': 0, 'score_advantage_insufficient': 0, 'in_cooldown': 0}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Sample positions:
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AAPL: age=0.0h, pnl=-0.60%, orig_score=4.09, advantage=-0.88, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AMD: age=0.0h, pnl=-0.17%, orig_score=4.30, advantage=-1.08, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     BA: age=0.0h, pnl=0.11%, orig_score=3.55, advantage=-0.33, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     C: age=0.0h, pnl=-0.05%, orig_score=5.58, advantage=-2.37, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     CAT: age=0.0h, pnl=0.19%, orig_score=5.42, advantage=-2.20, fail=too_young
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG HD: BLOCKED by max_positions_reached (Alpaca positions: 32, executor.opens: 32, max: 32), no displacement candidates
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BLK: Processing cluster - direction=bearish, initial_score=3.87, source=composite_v3
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BLK: expectancy=0.1243, should_trade=True, reason=expectancy_passed
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BLK: PASSED expectancy gate, checking other gates...
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG DISPLACEMENT: No candidates found for score 3.20
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Total positions: 32
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Reasons: {'too_young': 32, 'pnl_too_high': 0, 'score_advantage_insufficient': 0, 'in_cooldown': 0}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]   Sample positions:
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AAPL: age=0.0h, pnl=-0.60%, orig_score=4.09, advantage=-0.89, fail=too_young
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     AMD: age=0.0h, pnl=-0.17%, orig_score=4.30, advantage=-1.09, fail=too_young
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     BA: age=0.0h, pnl=0.11%, orig_score=3.55, advantage=-0.35, fail=too_young
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     C: age=0.0h, pnl=-0.06%, orig_score=5.58, advantage=-2.38, fail=too_young
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot]     CAT: age=0.0h, pnl=0.19%, orig_score=5.42, advantage=-2.22, fail=too_young
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG BLK: BLOCKED by max_positions_reached (Alpaca positions: 32, executor.opens: 32, max: 32), no displacement candidates
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1578357]: [trading-bot] DEBUG COST: Processing cluster - direction=bearish, initial_score=3.76, source=composite_v3
`

### journal (last 400) uw-flow-daemon.service

`
uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "max_pain:DIA", "time_remaining": 243.6719114780426}
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "insider:DIA", "base_endpoint": "insider", "force_first": false, "last": 1774469003.957776, "interval": 86400, "time_since_last": 77709.20303726196}
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "insider:DIA", "time_remaining": 8690.796962738037}
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "calendar:DIA", "base_endpoint": "calendar", "force_first": false, "last": 1774381128.007817, "interval": 604800, "time_since_last": 165585.2026362419}
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "calendar:DIA", "time_remaining": 439214.7973637581}
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "institutional_ownership:DIA", "base_endpoint": "institutional_ownership", "force_first": false, "last": 1774469004.1428769, "interval": 86400, "time_since_last": 77709.06800842285}
Mar 26 17:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "institutional_ownership:DIA", "time_remaining": 8690.931991577148}
Mar 26 17:38:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "option_flow:XLF", "base_endpoint": "option_flow", "force_first": false, "last": 1774546379.2275407, "interval": 150, "time_since_last": 335.49793696403503}
Mar 26 17:38:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling allowed {"endpoint": "option_flow:XLF"}
Mar 26 17:38:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_get: API call attempt {"url": "https://api.unusualwhales.com/api/option-trades/flow-alerts", "has_api_key": true}
Mar 26 17:38:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] ✅ RAW PAYLOAD RECEIVED: https://api.unusualwhales.com/api/option-trades/flow-alerts | Status: 200 | Data keys: ['data', 'newer_than', 'older_than']
Mar 26 17:38:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_get: API call success {"url": "https://api.unusualwhales.com/api/option-trades/flow-alerts", "status": 200, "has_data": true, "data_type": "list", "data_keys": ["data", "newer_than", "older_than"]}
Mar 26 17:38:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Retrieved 100 flow trades for XLF
Mar 26 17:38:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Polling XLF: got 100 raw trades
Mar 26 17:38:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_update_cache: Cache update start {"ticker": "XLF", "data_keys": ["flow_trades", "sentiment", "conviction", "total_premium", "call_premium", "put_premium", "net_premium", "trade_count", "flow"], "has_data": true}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_update_cache: Cache update complete {"ticker": "XLF", "cache_size": 56, "ticker_data_keys": ["market_tide", "iv_term_skew", "smile_slope", "insider", "flow_trades", "sentiment", "conviction", "total_premium", "call_premium", "put_premium", "net_premium", "trade_count", "flow", "_last_update"]}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Cache for XLF: 100 trades stored
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "dark_pool_levels:XLF", "base_endpoint": "dark_pool_levels", "force_first": false, "last": 1774546379.489995, "interval": 900, "time_since_last": 335.7053234577179}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "dark_pool_levels:XLF", "time_remaining": 564.2946765422821}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "greek_exposure:XLF", "base_endpoint": "greek_exposure", "force_first": false, "last": 1774546524.9448795, "interval": 3600, "time_since_last": 190.25132083892822}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "greek_exposure:XLF", "time_remaining": 3409.748679161072}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "greeks:XLF", "base_endpoint": "greeks", "force_first": false, "last": 1774546525.4098203, "interval": 3600, "time_since_last": 189.78656148910522}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "greeks:XLF", "time_remaining": 3410.213438510895}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "oi_change:XLF", "base_endpoint": "oi_change", "force_first": false, "last": 1774546379.7096596, "interval": 900, "time_since_last": 335.4869067668915}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "oi_change:XLF", "time_remaining": 564.5130932331085}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "etf_flow:XLF", "base_endpoint": "etf_flow", "force_first": false, "last": 1774546525.632576, "interval": 3600, "time_since_last": 189.5641541481018}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "etf_flow:XLF", "time_remaining": 3410.435845851898}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "iv_rank:XLF", "base_endpoint": "iv_rank", "force_first": false, "last": 1774546526.950136, "interval": 3600, "time_since_last": 188.24682688713074}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "iv_rank:XLF", "time_remaining": 3411.7531731128693}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "shorts_ftds:XLF", "base_endpoint": "shorts_ftds", "force_first": false, "last": 1774546527.2880356, "interval": 7200, "time_since_last": 187.90918517112732}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "shorts_ftds:XLF", "time_remaining": 7012.090814828873}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "max_pain:XLF", "base_endpoint": "max_pain", "force_first": false, "last": 1774545159.6053874, "interval": 1800, "time_since_last": 1555.5919921398163}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "max_pain:XLF", "time_remaining": 244.40800786018372}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "insider:XLF", "base_endpoint": "insider", "force_first": false, "last": 1774469006.1929626, "interval": 86400, "time_since_last": 77709.00461411476}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "insider:XLF", "time_remaining": 8690.995385885239}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "calendar:XLF", "base_endpoint": "calendar", "force_first": false, "last": 1774381130.1765425, "interval": 604800, "time_since_last": 165585.0742647648}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "calendar:XLF", "time_remaining": 439214.9257352352}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "institutional_ownership:XLF", "base_endpoint": "institutional_ownership", "force_first": false, "last": 1774469006.3546126, "interval": 86400, "time_since_last": 77708.89665150642}
Mar 26 17:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "institutional_ownership:XLF", "time_remaining": 8691.103348493576}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "option_flow:XLE", "base_endpoint": "option_flow", "force_first": false, "last": 1774546381.3949401, "interval": 150, "time_since_last": 335.3699514865875}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling allowed {"endpoint": "option_flow:XLE"}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_get: API call attempt {"url": "https://api.unusualwhales.com/api/option-trades/flow-alerts", "has_api_key": true}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] ✅ RAW PAYLOAD RECEIVED: https://api.unusualwhales.com/api/option-trades/flow-alerts | Status: 200 | Data keys: ['data', 'newer_than', 'older_than']
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_get: API call success {"url": "https://api.unusualwhales.com/api/option-trades/flow-alerts", "status": 200, "has_data": true, "data_type": "list", "data_keys": ["data", "newer_than", "older_than"]}
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Retrieved 100 flow trades for XLE
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Polling XLE: got 100 raw trades
Mar 26 17:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_update_cache: Cache update start {"ticker": "XLE", "data_keys": ["flow_trades", "sentiment", "conviction", "total_premium", "call_premium", "put_premium", "net_premium", "trade_count", "flow"], "has_data": true}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_update_cache: Cache update complete {"ticker": "XLE", "cache_size": 56, "ticker_data_keys": ["market_tide", "iv_term_skew", "smile_slope", "insider", "flow_trades", "sentiment", "conviction", "total_premium", "call_premium", "put_premium", "net_premium", "trade_count", "flow", "_last_update"]}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Cache for XLE: 100 trades stored
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "dark_pool_levels:XLE", "base_endpoint": "dark_pool_levels", "force_first": false, "last": 1774546381.6858287, "interval": 900, "time_since_last": 335.5589282512665}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "dark_pool_levels:XLE", "time_remaining": 564.4410717487335}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "greek_exposure:XLE", "base_endpoint": "greek_exposure", "force_first": false, "last": 1774546529.174043, "interval": 3600, "time_since_last": 188.0711808204651}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "greek_exposure:XLE", "time_remaining": 3411.928819179535}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "greeks:XLE", "base_endpoint": "greeks", "force_first": false, "last": 1774546529.5763874, "interval": 3600, "time_since_last": 187.66899871826172}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "greeks:XLE", "time_remaining": 3412.3310012817383}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "oi_change:XLE", "base_endpoint": "oi_change", "force_first": false, "last": 1774546381.9285889, "interval": 900, "time_since_last": 335.3169791698456}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "oi_change:XLE", "time_remaining": 564.6830208301544}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "etf_flow:XLE", "base_endpoint": "etf_flow", "force_first": false, "last": 1774546529.7073596, "interval": 3600, "time_since_last": 187.53846192359924}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "etf_flow:XLE", "time_remaining": 3412.4615380764008}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "iv_rank:XLE", "base_endpoint": "iv_rank", "force_first": false, "last": 1774546531.0136306, "interval": 3600, "time_since_last": 186.23261332511902}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "iv_rank:XLE", "time_remaining": 3413.767386674881}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "shorts_ftds:XLE", "base_endpoint": "shorts_ftds", "force_first": false, "last": 1774546531.2771711, "interval": 7200, "time_since_last": 185.96930813789368}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "shorts_ftds:XLE", "time_remaining": 7014.030691862106}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "max_pain:XLE", "base_endpoint": "max_pain", "force_first": false, "last": 1774545162.2702663, "interval": 1800, "time_since_last": 1554.97642827034}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "max_pain:XLE", "time_remaining": 245.02357172966003}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "insider:XLE", "base_endpoint": "insider", "force_first": false, "last": 1774469121.819349, "interval": 86400, "time_since_last": 77595.42749547958}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "insider:XLE", "time_remaining": 8804.572504520416}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "calendar:XLE", "base_endpoint": "calendar", "force_first": false, "last": 1774381132.353602, "interval": 604800, "time_since_last": 165584.946621418}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "calendar:XLE", "time_remaining": 439215.053378582}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "institutional_ownership:XLE", "base_endpoint": "institutional_ownership", "force_first": false, "last": 1774469122.007861, "interval": 86400, "time_since_last": 77595.29283690453}
Mar 26 17:38:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "institutional_ownership:XLE", "time_remaining": 8804.707163095474}
Mar 26 17:38:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "option_flow:XLK", "base_endpoint": "option_flow", "force_first": false, "last": 1774546383.648549, "interval": 150, "time_since_last": 335.1667766571045}
Mar 26 17:38:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling allowed {"endpoint": "option_flow:XLK"}
Mar 26 17:38:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_get: API call attempt {"url": "https://api.unusualwhales.com/api/option-trades/flow-alerts", "has_api_key": true}
Mar 26 17:38:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] ✅ RAW PAYLOAD RECEIVED: https://api.unusualwhales.com/api/option-trades/flow-alerts | Status: 200 | Data keys: ['data', 'newer_than', 'older_than']
Mar 26 17:38:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_get: API call success {"url": "https://api.unusualwhales.com/api/option-trades/flow-alerts", "status": 200, "has_data": true, "data_type": "list", "data_keys": ["data", "newer_than", "older_than"]}
Mar 26 17:38:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Retrieved 100 flow trades for XLK
Mar 26 17:38:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Polling XLK: got 100 raw trades
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_update_cache: Cache update start {"ticker": "XLK", "data_keys": ["flow_trades", "sentiment", "conviction", "total_premium", "call_premium", "put_premium", "net_premium", "trade_count", "flow"], "has_data": true}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:_update_cache: Cache update complete {"ticker": "XLK", "cache_size": 56, "ticker_data_keys": ["market_tide", "iv_term_skew", "smile_slope", "insider", "flow_trades", "sentiment", "conviction", "total_premium", "call_premium", "put_premium", "net_premium", "trade_count", "flow", "_last_update"]}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [UW-DAEMON] Cache for XLK: 100 trades stored
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "dark_pool_levels:XLK", "base_endpoint": "dark_pool_levels", "force_first": false, "last": 1774546383.9257312, "interval": 900, "time_since_last": 335.34175729751587}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "dark_pool_levels:XLK", "time_remaining": 564.6582427024841}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "greek_exposure:XLK", "base_endpoint": "greek_exposure", "force_first": false, "last": 1774546533.1577346, "interval": 3600, "time_since_last": 186.11022806167603}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "greek_exposure:XLK", "time_remaining": 3413.889771938324}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "greeks:XLK", "base_endpoint": "greeks", "force_first": false, "last": 1774546533.5866094, "interval": 3600, "time_since_last": 185.68150544166565}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "greeks:XLK", "time_remaining": 3414.3184945583344}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "oi_change:XLK", "base_endpoint": "oi_change", "force_first": false, "last": 1774546384.1050708, "interval": 900, "time_since_last": 335.1631968021393}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "oi_change:XLK", "time_remaining": 564.8368031978607}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "etf_flow:XLK", "base_endpoint": "etf_flow", "force_first": false, "last": 1774546533.7155037, "interval": 3600, "time_since_last": 185.55294251441956}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "etf_flow:XLK", "time_remaining": 3414.4470574855804}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "iv_rank:XLK", "base_endpoint": "iv_rank", "force_first": false, "last": 1774546534.3668127, "interval": 3600, "time_since_last": 184.90181493759155}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "iv_rank:XLK", "time_remaining": 3415.0981850624084}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "shorts_ftds:XLK", "base_endpoint": "shorts_ftds", "force_first": false, "last": 1774546534.6784115, "interval": 7200, "time_since_last": 184.5904130935669}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "shorts_ftds:XLK", "time_remaining": 7015.409586906433}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "max_pain:XLK", "base_endpoint": "max_pain", "force_first": false, "last": 1774545164.9363706, "interval": 1800, "time_since_last": 1554.3326437473297}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "max_pain:XLK", "time_remaining": 245.6673562526703}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "insider:XLK", "base_endpoint": "insider", "force_first": false, "last": 1774469237.4798465, "interval": 86400, "time_since_last": 77481.78933143616}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "insider:XLK", "time_remaining": 8918.210668563843}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "calendar:XLK", "base_endpoint": "calendar", "force_first": false, "last": 1774381134.4817715, "interval": 604800, "time_since_last": 165584.83747386932}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "calendar:XLK", "time_remaining": 439215.1625261307}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "institutional_ownership:XLK", "base_endpoint": "institutional_ownership", "force_first": false, "last": 1774469237.6442962, "interval": 86400, "time_since_last": 77481.67545318604}
Mar 26 17:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1572234]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "institutional_ownership:XLK", "time_remaining": 8918.324546813965}
`

### journal (last 400) stock-bot-dashboard.service

`
.57:5000
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: Press CTRL+C to quit
Mar 26 17:28:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:28:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:28:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:28:02] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:28:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:28:02] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:28:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: [Dashboard] Alpaca API connected
Mar 26 17:28:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: [Dashboard] Dependencies loaded
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/versions HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/ping HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/direction_banner HTTP/1.1" 200 -
Mar 26 17:28:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:08] "GET /api/situation HTTP/1.1" 200 -
Mar 26 17:28:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:09] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:28:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:10] "GET /api/stockbot/closed_trades HTTP/1.1" 200 -
Mar 26 17:28:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:10] "GET /api/stockbot/fast_lane_ledger HTTP/1.1" 200 -
Mar 26 17:28:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:11] "GET /api/sre/health HTTP/1.1" 200 -
Mar 26 17:28:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:11] "GET /api/sre/self_heal_events?limit=5 HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/executive_summary HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/failure_points HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/learning_readiness HTTP/1.1" 200 -
Mar 26 17:28:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:12] "GET /api/profitability_learning HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/dashboard/data_integrity HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/xai/auditor HTTP/1.1" 200 -
Mar 26 17:28:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:13] "GET /api/xai/health HTTP/1.1" 200 -
Mar 26 17:28:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:21] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 200 -
Mar 26 17:28:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:21] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 401 -
Mar 26 17:28:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:28] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 200 -
Mar 26 17:28:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 127.0.0.1 - - [26/Mar/2026 17:28:28] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 200 -
Mar 26 17:29:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:29:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:29:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:29:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:29:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:29:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:30:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:30:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:30:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:30:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:30:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:30:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:31:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:31:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:31:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:31:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:31:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:31:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:32:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:32:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:32:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:32:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:32:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:32:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:33:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:33:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:33:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:33:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:33:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:33:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:34:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:34:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:34:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:34:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:34:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:34:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:35:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:35:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:35:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:35:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:35:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1575423]: 75.167.147.249 - - [26/Mar/2026 17:35:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopping stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000)...
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Deactivated successfully.
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopped stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Consumed 7.995s CPU time, 199.4M memory peak, 0B memory swap peak.
Mar 26 17:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Started stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Starting Flask app...
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Starting on port 5000...
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Instance: UNKNOWN
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Loading dependencies...
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Server starting on port 5000
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Serving Flask app 'dashboard'
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Debug mode: off
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Running on all addresses (0.0.0.0)
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Running on http://127.0.0.1:5000
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]:  * Running on http://104.236.102.57:5000
Mar 26 17:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: Press CTRL+C to quit
Mar 26 17:35:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Alpaca API connected
Mar 26 17:35:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: [Dashboard] Dependencies loaded
Mar 26 17:36:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:36:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:36:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:36:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:36:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:36:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET / HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/positions HTTP/1.1" 401 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/version HTTP/1.1" 401 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/health_status HTTP/1.1" 401 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /favicon.ico HTTP/1.1" 401 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /favicon.ico HTTP/1.1" 404 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:36:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:31] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=signal_weight_recommendations HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=signal_performance HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=gate_profitability HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=blocked_counterfactuals_summary HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=exit_quality_summary HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=signal_profitability HTTP/1.1" 200 -
Mar 26 17:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:36:35] "GET /api/telemetry/latest/computed?name=intelligence_recommendations HTTP/1.1" 200 -
Mar 26 17:37:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:37:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:37:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:37:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:37:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 75.167.147.249 - - [26/Mar/2026 17:37:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:37:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:37:09] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 401 -
Mar 26 17:37:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:37:09] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 200 -
Mar 26 17:37:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:37:19] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 404 -
Mar 26 17:37:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1578346]: 127.0.0.1 - - [26/Mar/2026 17:37:23] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 404 -
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopping stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000)...
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Deactivated successfully.
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopped stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot-dashboard.service: Consumed 2.699s CPU time, 87.8M memory peak, 0B memory swap peak.
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Started stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000).
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Starting Flask app...
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Starting on port 5000...
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Instance: UNKNOWN
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Loading dependencies...[Dashboard] Server starting on port 5000
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Serving Flask app 'dashboard'
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Debug mode: off
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Running on all addresses (0.0.0.0)
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Running on http://127.0.0.1:5000
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]:  * Running on http://104.236.102.57:5000
Mar 26 17:37:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: Press CTRL+C to quit
Mar 26 17:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Alpaca API connected
Mar 26 17:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: [Dashboard] Dependencies loaded
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/versions HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/ping HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/direction_banner HTTP/1.1" 200 -
Mar 26 17:37:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:49] "GET /api/situation HTTP/1.1" 200 -
Mar 26 17:37:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:50] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:37:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:51] "GET /api/stockbot/closed_trades HTTP/1.1" 200 -
Mar 26 17:37:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:51] "GET /api/stockbot/fast_lane_ledger HTTP/1.1" 200 -
Mar 26 17:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:52] "GET /api/sre/health HTTP/1.1" 200 -
Mar 26 17:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:52] "GET /api/sre/self_heal_events?limit=5 HTTP/1.1" 200 -
Mar 26 17:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:52] "GET /api/executive_summary HTTP/1.1" 200 -
Mar 26 17:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:53] "GET /api/failure_points HTTP/1.1" 200 -
Mar 26 17:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:53] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:53] "GET /api/learning_readiness HTTP/1.1" 200 -
Mar 26 17:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:53] "GET /api/profitability_learning HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/dashboard/data_integrity HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/xai/auditor HTTP/1.1" 200 -
Mar 26 17:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:37:54] "GET /api/xai/health HTTP/1.1" 200 -
Mar 26 17:38:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 75.167.147.249 - - [26/Mar/2026 17:38:01] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:38:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 75.167.147.249 - - [26/Mar/2026 17:38:01] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:38:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 75.167.147.249 - - [26/Mar/2026 17:38:01] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:38:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:03] "GET / HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/version HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/positions HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/health_status HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/signal_history HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/version HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /favicon.ico HTTP/1.1" 401 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/signal_history HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /favicon.ico HTTP/1.1" 404 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/health_status HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/positions HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/alpaca_operational_activity?hours=72 HTTP/1.1" 200 -
Mar 26 17:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:04] "GET /api/telemetry/latest/computed?name=data_integrity HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/index HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=signal_performance HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=signal_weight_recommendations HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=live_vs_shadow_pnl HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=blocked_counterfactuals_summary HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=signal_profitability HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/paper-mode-intel-state HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=exit_quality_summary HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=gate_profitability HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/health HTTP/1.1" 200 -
Mar 26 17:38:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python3[1580958]: 127.0.0.1 - - [26/Mar/2026 17:38:08] "GET /api/telemetry/latest/computed?name=intelligence_recommendations HTTP/1.1" 200 -
`

