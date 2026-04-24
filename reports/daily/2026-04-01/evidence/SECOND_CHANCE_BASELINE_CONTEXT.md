# SECOND_CHANCE_BASELINE_CONTEXT

## git rev-parse HEAD

```
e03f25ef06483e6e0157228d6821613aeac4085f
```

## systemctl status stock-bot

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Wed 2026-04-01 18:36:53 UTC; 5h 31min ago
   Main PID: 1847213 (systemd_start.s)
      Tasks: 35 (limit: 9483)
     Memory: 802.2M (peak: 831.0M)
        CPU: 1h 1min 31.917s
     CGroup: /system.slice/stock-bot.service
             ├─1847213 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1847215 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1847221 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1847232 /root/stock-bot/venv/bin/python -u main.py
             └─1847256 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Apr 02 00:08:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 00:08:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 00:08:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 00:08:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 3/3): close_position_api_once returned None
Apr 02 00:08:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close TGT failed
Apr 02 00:08:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: TGT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:08:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing C (decision_px=114.20, entry=115.29, hold=279.2min)
Apr 02 00:08:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:08:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:08:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 1/3): close_position_api_once returned None

```

## systemctl cat stock-bot

```
# /etc/systemd/system/stock-bot.service
[Unit]
Description=Algorithmic Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/stock-bot
EnvironmentFile=/root/stock-bot/.env
ExecStart=/root/stock-bot/systemd_start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# /etc/systemd/system/stock-bot.service.d/override.conf
[Service]
Environment="EXPECTANCY_GATE_TRUTH_LOG=1"
Environment="SIGNAL_SCORE_BREAKDOWN_LOG=1"

# /etc/systemd/system/stock-bot.service.d/paper-overlay.conf
[Service]
Environment=MIN_EXEC_SCORE=2.7

# /etc/systemd/system/stock-bot.service.d/truth.conf
[Service]
# Canonical Truth Root (CTR) — mirror mode only
Environment=TRUTH_ROUTER_ENABLED=1
Environment=TRUTH_ROUTER_MIRROR_LEGACY=1
Environment=STOCKBOT_TRUTH_ROOT=/var/lib/stock-bot/truth

```

## journalctl -u stock-bot (tail 600)

```
Apr 01 23:58:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7859: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 23:58:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   holding_period_min = (datetime.utcnow() - entry_ts).total_seconds() / 60.0
Apr 01 23:58:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing PFE (decision_px=28.55, entry=28.57, hold=273.0min)
Apr 01 23:58:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7891: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 23:58:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts_dt = info.get("ts", datetime.utcnow())
Apr 01 23:58:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 23:58:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 23:58:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 1/3): close_position_api_once returned None
Apr 01 23:58:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 2/3): close_position_api_once returned None
Apr 01 23:58:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 3/3): close_position_api_once returned None
Apr 01 23:58:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close PFE failed
Apr 01 23:58:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: PFE could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 01 23:58:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MA (decision_px=492.50, entry=492.23, hold=272.8min)
Apr 01 23:58:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MA (attempt 1/3): close_position_api_once returned None
Apr 01 23:58:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 23:58:52,418 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 01 23:58:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 23:58:52,723 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 01 23:58:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 23:58:52,724 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 01 23:58:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MA (attempt 2/3): close_position_api_once returned None
Apr 01 23:59:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MA (attempt 3/3): close_position_api_once returned None
Apr 01 23:59:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MA failed
Apr 01 23:59:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 01 23:59:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing WMT (decision_px=124.56, entry=124.91, hold=272.8min)
Apr 01 23:59:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 1/3): close_position_api_once returned None
Apr 01 23:59:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 2/3): close_position_api_once returned None
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 267 (iter_count=296)
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 297
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12816: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   day = datetime.utcnow().strftime("%Y-%m-%d")
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12953: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   "last_heartbeat_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12957: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   "last_attempt_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
Apr 01 23:59:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 01 23:59:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 23:59:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 23:59:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 3/3): close_position_api_once returned None
Apr 01 23:59:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close WMT failed
Apr 01 23:59:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: WMT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 01 23:59:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing F (decision_px=11.68, entry=11.66, hold=272.7min)
Apr 01 23:59:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 1/3): close_position_api_once returned None
Apr 01 23:59:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 2/3): close_position_api_once returned None
Apr 01 23:59:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 3/3): close_position_api_once returned None
Apr 01 23:59:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close F failed
Apr 01 23:59:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: F could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 01 23:59:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing XOM (decision_px=159.40, entry=161.58, hold=272.8min)
Apr 01 23:59:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 1/3): close_position_api_once returned None
Apr 01 23:59:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 2/3): close_position_api_once returned None
Apr 01 23:59:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 3/3): close_position_api_once returned None
Apr 01 23:59:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close XOM failed
Apr 01 23:59:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: XOM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 01 23:59:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing AAPL (decision_px=254.95, entry=255.38, hold=272.8min)
Apr 01 23:59:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 1/3): close_position_api_once returned None
Apr 01 23:59:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 2/3): close_position_api_once returned None
Apr 01 23:59:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 23:59:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 01 23:59:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 3/3): close_position_api_once returned None
Apr 01 23:59:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close AAPL failed
Apr 01 23:59:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: AAPL could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 01 23:59:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing CVX (decision_px=196.22, entry=197.94, hold=272.8min)
Apr 01 23:59:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 1/3): close_position_api_once returned None
Apr 01 23:59:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 2/3): close_position_api_once returned None
Apr 01 23:59:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 23:59:52,734 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 01 23:59:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 23:59:53,023 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 01 23:59:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-01 23:59:53,023 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 01 23:59:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 3/3): close_position_api_once returned None
Apr 01 23:59:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close CVX failed
Apr 01 23:59:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: CVX could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 01 23:59:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing GM (decision_px=75.05, entry=74.90, hold=272.8min)
Apr 01 23:59:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 1/3): close_position_api_once returned None
Apr 01 23:59:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 2/3): close_position_api_once returned None
Apr 02 00:00:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 3/3): close_position_api_once returned None
Apr 02 00:00:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GM failed
Apr 02 00:00:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:00:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NIO (decision_px=6.18, entry=6.17, hold=272.9min)
Apr 02 00:00:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 1/3): close_position_api_once returned None
Apr 02 00:00:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 00:00:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 268 (iter_count=297)
Apr 02 00:00:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 298
Apr 02 00:00:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 00:00:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 00:00:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 00:00:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 00:00:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 00:00:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 4.2s (target=5.0s, elapsed=0.8s)
Apr 02 00:00:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 2/3): close_position_api_once returned None
Apr 02 00:00:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:00:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:00:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 00:00:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 269 (iter_count=297)
Apr 02 00:00:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 298
Apr 02 00:00:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 00:00:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 00:00:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 00:00:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 00:00:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 00:00:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 00:00:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 3/3): close_position_api_once returned None
Apr 02 00:00:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close NIO failed
Apr 02 00:00:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: NIO could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:00:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing LOW (decision_px=235.98, entry=236.54, hold=272.8min)
Apr 02 00:00:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 1/3): close_position_api_once returned None
Apr 02 00:00:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 2/3): close_position_api_once returned None
Apr 02 00:00:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 3/3): close_position_api_once returned None
Apr 02 00:00:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close LOW failed
Apr 02 00:00:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: LOW could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:00:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing HD (decision_px=329.56, entry=329.84, hold=272.6min)
Apr 02 00:00:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 1/3): close_position_api_once returned None
Apr 02 00:00:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 2/3): close_position_api_once returned None
Apr 02 00:00:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 3/3): close_position_api_once returned None
Apr 02 00:00:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close HD failed
Apr 02 00:00:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: HD could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:00:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NVDA (decision_px=176.05, entry=176.22, hold=272.7min)
Apr 02 00:00:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 1/3): close_position_api_once returned None
Apr 02 00:00:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:00:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:00:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 2/3): close_position_api_once returned None
Apr 02 00:00:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 3/3): close_position_api_once returned None
Apr 02 00:00:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close NVDA failed
Apr 02 00:00:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: NVDA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:00:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing GOOGL (decision_px=297.43, entry=297.79, hold=272.8min)
Apr 02 00:00:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 1/3): close_position_api_once returned None
Apr 02 00:00:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 2/3): close_position_api_once returned None
Apr 02 00:00:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:00:53,032 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 00:00:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:00:53,388 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 00:00:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:00:53,389 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 00:00:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 3/3): close_position_api_once returned None
Apr 02 00:00:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GOOGL failed
Apr 02 00:00:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GOOGL could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:00:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JNJ (decision_px=244.10, entry=244.12, hold=272.6min)
Apr 02 00:00:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 1/3): close_position_api_once returned None
Apr 02 00:01:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 2/3): close_position_api_once returned None
Apr 02 00:01:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 3/3): close_position_api_once returned None
Apr 02 00:01:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JNJ failed
Apr 02 00:01:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JNJ could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:01:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing SLB (decision_px=49.94, entry=50.10, hold=272.6min)
Apr 02 00:01:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 1/3): close_position_api_once returned None
Apr 02 00:01:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:01:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:01:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 00:01:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 270 (iter_count=298)
Apr 02 00:01:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 299
Apr 02 00:01:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 00:01:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 00:01:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 00:01:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 00:01:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 00:01:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 00:01:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 2/3): close_position_api_once returned None
Apr 02 00:01:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 3/3): close_position_api_once returned None
Apr 02 00:01:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close SLB failed
Apr 02 00:01:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: SLB could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:01:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing TGT (decision_px=120.45, entry=121.23, hold=272.8min)
Apr 02 00:01:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 1/3): close_position_api_once returned None
Apr 02 00:01:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 2/3): close_position_api_once returned None
Apr 02 00:01:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 3/3): close_position_api_once returned None
Apr 02 00:01:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close TGT failed
Apr 02 00:01:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: TGT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:01:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing C (decision_px=115.50, entry=115.29, hold=272.5min)
Apr 02 00:01:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 1/3): close_position_api_once returned None
Apr 02 00:01:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 2/3): close_position_api_once returned None
Apr 02 00:01:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 3/3): close_position_api_once returned None
Apr 02 00:01:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close C failed
Apr 02 00:01:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: C could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:01:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MS (decision_px=166.84, entry=166.35, hold=272.1min)
Apr 02 00:01:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:01:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:01:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 1/3): close_position_api_once returned None
Apr 02 00:01:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 2/3): close_position_api_once returned None
Apr 02 00:01:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 3/3): close_position_api_once returned None
Apr 02 00:01:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MS failed
Apr 02 00:01:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MS could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:01:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing XLK (decision_px=135.00, entry=135.12, hold=271.9min)
Apr 02 00:01:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 1/3): close_position_api_once returned None
Apr 02 00:01:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:01:53,397 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 00:01:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:01:53,730 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 00:01:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:01:53,731 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 00:01:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 2/3): close_position_api_once returned None
Apr 02 00:02:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 3/3): close_position_api_once returned None
Apr 02 00:02:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close XLK failed
Apr 02 00:02:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: XLK could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:02:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JPM (decision_px=295.66, entry=295.31, hold=271.9min)
Apr 02 00:02:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 1/3): close_position_api_once returned None
Apr 02 00:02:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 2/3): close_position_api_once returned None
Apr 02 00:02:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:02:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 271 (iter_count=299)
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 300
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Heartbeat file OK: state/bot_heartbeat.json (iter 300)
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 3/3): close_position_api_once returned None
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JPM failed
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JPM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:02:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing WFC (decision_px=80.51, entry=81.02, hold=271.9min)
Apr 02 00:02:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 1/3): close_position_api_once returned None
Apr 02 00:02:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 2/3): close_position_api_once returned None
Apr 02 00:02:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 3/3): close_position_api_once returned None
Apr 02 00:02:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close WFC failed
Apr 02 00:02:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: WFC could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:02:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing CAT (decision_px=730.46, entry=735.10, hold=271.3min)
Apr 02 00:02:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 1/3): close_position_api_once returned None
Apr 02 00:02:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 2/3): close_position_api_once returned None
Apr 02 00:02:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 3/3): close_position_api_once returned None
Apr 02 00:02:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close CAT failed
Apr 02 00:02:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: CAT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 00:02:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 00:02:34 UTC] ----------------------------------------
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 00:02:34 UTC] SERVICE STATUS:
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 00:02:34 UTC]   dashboard: RUNNING (health: OK)
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 00:02:34 UTC]   trading-bot: RUNNING (health: OK)
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 00:02:34 UTC]   v4-research: EXITED(0) (health: OK)
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 00:02:34 UTC]   heartbeat-keeper: RUNNING (health: OK)
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 00:02:34 UTC] OVERALL SYSTEM HEALTH: OK
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 00:02:34 UTC] Uptime: 325 minutes
Apr 02 00:02:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 00:02:34 UTC] ----------------------------------------
Apr 02 00:02:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:02:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:02:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:02:53,740 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 00:02:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:02:54,139 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 00:02:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:02:54,139 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 272 (iter_count=300)
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 301
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 00:03:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 00:03:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:31,540 [CACHE-ENRICH] INFO: Starting self-healing cycle
Apr 02 00:03:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:31,750 [CACHE-ENRICH] INFO: No issues detected - system healthy
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $162,500.88, Equity: $47,251.70
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,377 [CACHE-ENRICH] INFO: signal_open_position: evaluated AAPL -> 3.0020
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6772: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,399 [CACHE-ENRICH] INFO: signal_open_position: evaluated C -> 3.4770
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,417 [CACHE-ENRICH] INFO: signal_open_position: evaluated CAT -> 3.4250
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,437 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.6080
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,458 [CACHE-ENRICH] INFO: signal_open_position: evaluated COP -> 3.1420
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,479 [CACHE-ENRICH] INFO: signal_open_position: evaluated CVX -> 2.9740
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,500 [CACHE-ENRICH] INFO: signal_open_position: evaluated F -> 2.9850
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,519 [CACHE-ENRICH] INFO: signal_open_position: evaluated GM -> 3.4600
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,538 [CACHE-ENRICH] INFO: signal_open_position: evaluated GOOGL -> 2.8740
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,560 [CACHE-ENRICH] INFO: signal_open_position: evaluated HD -> 2.6980
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,582 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 3.6450
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,602 [CACHE-ENRICH] INFO: signal_open_position: evaluated JNJ -> 2.8380
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,622 [CACHE-ENRICH] INFO: signal_open_position: evaluated JPM -> 3.1200
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,643 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 3.6350
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,667 [CACHE-ENRICH] INFO: signal_open_position: evaluated LOW -> 2.7140
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,689 [CACHE-ENRICH] INFO: signal_open_position: evaluated MA -> 2.9500
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,712 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.3280
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,737 [CACHE-ENRICH] INFO: signal_open_position: evaluated MS -> 3.2860
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,762 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.3670
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,785 [CACHE-ENRICH] INFO: signal_open_position: evaluated NIO -> 3.4300
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,805 [CACHE-ENRICH] INFO: signal_open_position: evaluated NVDA -> 3.5250
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,826 [CACHE-ENRICH] INFO: signal_open_position: evaluated PFE -> 3.0860
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,847 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.5600
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,867 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 3.5980
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,889 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.1390
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,915 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.6350
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,941 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.0370
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,962 [CACHE-ENRICH] INFO: signal_open_position: evaluated UNH -> 3.2520
Apr 02 00:03:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:33,981 [CACHE-ENRICH] INFO: signal_open_position: evaluated WFC -> 3.0480
Apr 02 00:03:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:34,001 [CACHE-ENRICH] INFO: signal_open_position: evaluated WMT -> 2.7630
Apr 02 00:03:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:34,020 [CACHE-ENRICH] INFO: signal_open_position: evaluated XLK -> 3.1930
Apr 02 00:03:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 00:03:34,039 [CACHE-ENRICH] INFO: signal_open_position: evaluated XOM -> 2.9710
Apr 02 00:03:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6876: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 00:03:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now = datetime.utcnow()
Apr 02 00:03:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: 0.0026% (entry=$15.61, current=$15.65)
Apr 02 00:03:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[18472
```

## Displacement behavior (pre-change)

No runtime displacement parameters were modified. First-pass displacement remains authoritative; paper second-chance is env-gated (`PAPER_SECOND_CHANCE_DISPLACEMENT=1`) and adds logging + offline queue only.
