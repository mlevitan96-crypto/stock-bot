# PAPER_CAPS_PHASE0_CONTEXT

## git rev-parse HEAD

```
efd27d13760df1f943a4867f0a4947f1d9f29c97
```

## systemctl status stock-bot

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Wed 2026-04-01 18:36:53 UTC; 7h ago
   Main PID: 1847213 (systemd_start.s)
      Tasks: 35 (limit: 9483)
     Memory: 808.7M (peak: 833.6M)
        CPU: 1h 4min 5.568s
     CGroup: /system.slice/stock-bot.service
             ├─1847213 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1847215 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1847221 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1847232 /root/stock-bot/venv/bin/python -u main.py
             └─1847256 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Apr 02 01:46:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:46:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 2/3): close_position_api_once returned None
Apr 02 01:46:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 3/3): close_position_api_once returned None
Apr 02 01:46:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close COP failed
Apr 02 01:46:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: COP could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:46:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing PFE (decision_px=28.47, entry=28.57, hold=380.8min)
Apr 02 01:46:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 1/3): close_position_api_once returned None
Apr 02 01:46:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:46:27,327 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:46:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:46:27,619 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:46:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:46:27,619 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols

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

## systemctl show Environment

```
Environment=EXPECTANCY_GATE_TRUTH_LOG=1 SIGNAL_SCORE_BREAKDOWN_LOG=1 MIN_EXEC_SCORE=2.7 TRUTH_ROUTER_ENABLED=1 TRUTH_ROUTER_MIRROR_LEGACY=1 STOCKBOT_TRUTH_ROOT=/var/lib/stock-bot/truth
EnvironmentFiles=/root/stock-bot/.env (ignore_errors=no)

```

## journalctl tail

```
Apr 02 01:33:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 3/3): close_position_api_once returned None
Apr 02 01:33:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close F failed
Apr 02 01:33:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: F could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:33:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing XOM (decision_px=165.20, entry=161.58, hold=366.9min)
Apr 02 01:33:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 1/3): close_position_api_once returned None
Apr 02 01:33:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 2/3): close_position_api_once returned None
Apr 02 01:33:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:33:35,712 [CACHE-ENRICH] INFO: Starting self-healing cycle
Apr 02 01:33:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:33:35,907 [CACHE-ENRICH] INFO: No issues detected - system healthy
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 3/3): close_position_api_once returned None
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close XOM failed
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: XOM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7856: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts = info.get("ts", datetime.utcnow())
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7859: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   holding_period_min = (datetime.utcnow() - entry_ts).total_seconds() / 60.0
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing AAPL (decision_px=253.55, entry=255.38, hold=366.9min)
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7891: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts_dt = info.get("ts", datetime.utcnow())
Apr 02 01:33:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 1/3): close_position_api_once returned None
Apr 02 01:33:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 2/3): close_position_api_once returned None
Apr 02 01:33:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:33:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:33:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 3/3): close_position_api_once returned None
Apr 02 01:33:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close AAPL failed
Apr 02 01:33:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: AAPL could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:33:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing CVX (decision_px=202.00, entry=197.94, hold=366.8min)
Apr 02 01:33:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 1/3): close_position_api_once returned None
Apr 02 01:33:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 2/3): close_position_api_once returned None
Apr 02 01:33:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 3/3): close_position_api_once returned None
Apr 02 01:33:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close CVX failed
Apr 02 01:33:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: CVX could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:33:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing GM (decision_px=73.97, entry=74.90, hold=366.9min)
Apr 02 01:33:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 1/3): close_position_api_once returned None
Apr 02 01:34:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 2/3): close_position_api_once returned None
Apr 02 01:34:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 3/3): close_position_api_once returned None
Apr 02 01:34:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GM failed
Apr 02 01:34:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:34:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NIO (decision_px=6.15, entry=6.17, hold=367.0min)
Apr 02 01:34:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 1/3): close_position_api_once returned None
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 363 (iter_count=391)
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 392
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12816: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   audit_seg("run_once", "ERROR", {"error": str(e), "type": type(e).__name__})
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12953: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   """Persist fail counter to disk."""
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12957: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   log_event("worker_state", "fail_count_save_error", error=str(e))
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:34:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 2/3): close_position_api_once returned None
Apr 02 01:34:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 3/3): close_position_api_once returned None
Apr 02 01:34:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close NIO failed
Apr 02 01:34:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: NIO could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:34:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing LOW (decision_px=234.52, entry=236.54, hold=366.9min)
Apr 02 01:34:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 1/3): close_position_api_once returned None
Apr 02 01:34:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:34:23,430 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:34:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:34:23,727 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:34:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:34:23,727 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:34:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 2/3): close_position_api_once returned None
Apr 02 01:34:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:34:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:34:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 3/3): close_position_api_once returned None
Apr 02 01:34:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close LOW failed
Apr 02 01:34:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: LOW could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:34:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing HD (decision_px=329.97, entry=329.84, hold=366.9min)
Apr 02 01:34:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 1/3): close_position_api_once returned None
Apr 02 01:34:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 2/3): close_position_api_once returned None
Apr 02 01:34:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 3/3): close_position_api_once returned None
Apr 02 01:34:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close HD failed
Apr 02 01:34:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: HD could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:34:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NVDA (decision_px=172.95, entry=176.22, hold=367.0min)
Apr 02 01:34:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 1/3): close_position_api_once returned None
Apr 02 01:35:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 2/3): close_position_api_once returned None
Apr 02 01:35:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 3/3): close_position_api_once returned None
Apr 02 01:35:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close NVDA failed
Apr 02 01:35:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: NVDA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:35:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing GOOGL (decision_px=292.03, entry=297.79, hold=367.1min)
Apr 02 01:35:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 1/3): close_position_api_once returned None
Apr 02 01:35:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 2/3): close_position_api_once returned None
Apr 02 01:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 364 (iter_count=392)
Apr 02 01:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 393
Apr 02 01:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:35:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 3/3): close_position_api_once returned None
Apr 02 01:35:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GOOGL failed
Apr 02 01:35:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GOOGL could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:35:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JNJ (decision_px=244.35, entry=244.12, hold=366.9min)
Apr 02 01:35:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 1/3): close_position_api_once returned None
Apr 02 01:35:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 2/3): close_position_api_once returned None
Apr 02 01:35:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:35:23,736 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:35:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:35:24,059 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:35:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:35:24,059 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:35:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 3/3): close_position_api_once returned None
Apr 02 01:35:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JNJ failed
Apr 02 01:35:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JNJ could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:35:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing SLB (decision_px=50.73, entry=50.10, hold=366.9min)
Apr 02 01:35:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 1/3): close_position_api_once returned None
Apr 02 01:35:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 2/3): close_position_api_once returned None
Apr 02 01:35:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 3/3): close_position_api_once returned None
Apr 02 01:35:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close SLB failed
Apr 02 01:35:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: SLB could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:35:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing TGT (decision_px=120.00, entry=121.23, hold=367.1min)
Apr 02 01:35:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 1/3): close_position_api_once returned None
Apr 02 01:35:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:35:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:35:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 2/3): close_position_api_once returned None
Apr 02 01:35:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 3/3): close_position_api_once returned None
Apr 02 01:35:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close TGT failed
Apr 02 01:35:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: TGT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:35:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing C (decision_px=115.31, entry=115.29, hold=366.8min)
Apr 02 01:35:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 1/3): close_position_api_once returned None
Apr 02 01:35:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 2/3): close_position_api_once returned None
Apr 02 01:35:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 3/3): close_position_api_once returned None
Apr 02 01:35:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close C failed
Apr 02 01:35:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: C could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:35:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MS (decision_px=165.55, entry=166.35, hold=366.4min)
Apr 02 01:36:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 1/3): close_position_api_once returned None
Apr 02 01:36:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 2/3): close_position_api_once returned None
Apr 02 01:36:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 3/3): close_position_api_once returned None
Apr 02 01:36:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MS failed
Apr 02 01:36:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MS could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:36:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing XLK (decision_px=133.32, entry=135.12, hold=366.2min)
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 1/3): close_position_api_once returned None
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 365 (iter_count=393)
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 394
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:36:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:36:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:36:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 2/3): close_position_api_once returned None
Apr 02 01:36:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 3/3): close_position_api_once returned None
Apr 02 01:36:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close XLK failed
Apr 02 01:36:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: XLK could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:36:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JPM (decision_px=292.46, entry=295.31, hold=366.2min)
Apr 02 01:36:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 1/3): close_position_api_once returned None
Apr 02 01:36:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:36:24,069 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:36:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:36:24,437 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:36:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:36:24,437 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:36:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 2/3): close_position_api_once returned None
Apr 02 01:36:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 3/3): close_position_api_once returned None
Apr 02 01:36:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JPM failed
Apr 02 01:36:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JPM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:36:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing WFC (decision_px=80.00, entry=81.02, hold=366.2min)
Apr 02 01:36:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 1/3): close_position_api_once returned None
Apr 02 01:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 2/3): close_position_api_once returned None
Apr 02 01:36:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 3/3): close_position_api_once returned None
Apr 02 01:36:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close WFC failed
Apr 02 01:36:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: WFC could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:36:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing CAT (decision_px=719.15, entry=735.10, hold=365.6min)
Apr 02 01:36:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:36:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:36:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 1/3): close_position_api_once returned None
Apr 02 01:36:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 2/3): close_position_api_once returned None
Apr 02 01:36:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 3/3): close_position_api_once returned None
Apr 02 01:36:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close CAT failed
Apr 02 01:36:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: CAT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:36:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Apr 02 01:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 366 (iter_count=394)
Apr 02 01:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 395
Apr 02 01:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:37:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:37:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] [MOCK-SIGNAL] Injecting perfect whale signal at 2026-04-02T01:37:14.769690+00:00
Apr 02 01:37:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] [MOCK-SIGNAL] ✅ Mock signal passed: score=4.53 (>= 4.0)
Apr 02 01:37:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:24,445 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:37:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:24,769 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:37:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:24,770 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:38 UTC] Rotating logs/score_snapshot.jsonl (11.6MB)
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:38 UTC] Rotating logs/signals.jsonl (12.6MB)
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:38 UTC] Rotating logs/signal_score_breakdown.jsonl (6.9MB)
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 01:37:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:38 UTC] Rotating logs/signal_snapshots.jsonl (7.6MB)
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC] Rotating state/portfolio_state.jsonl (7.8MB)
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC] ----------------------------------------
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC] SERVICE STATUS:
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC]   dashboard: RUNNING (health: OK)
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC]   trading-bot: RUNNING (health: OK)
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC]   v4-research: EXITED(0) (health: OK)
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC]   heartbeat-keeper: RUNNING (health: OK)
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC] OVERALL SYSTEM HEALTH: OK
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC] Uptime: 420 minutes
Apr 02 01:37:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:37:39 UTC] ----------------------------------------
Apr 02 01:37:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $162,500.88, Equity: $47,210.39
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,174 [CACHE-ENRICH] INFO: signal_open_position: evaluated AAPL -> 3.2900
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6772: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,192 [CACHE-ENRICH] INFO: signal_open_position: evaluated C -> 3.7640
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,210 [CACHE-ENRICH] INFO: signal_open_position: evaluated CAT -> 3.7030
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,232 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.8960
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,251 [CACHE-ENRICH] INFO: signal_open_position: evaluated COP -> 3.4330
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,270 [CACHE-ENRICH] INFO: signal_open_position: evaluated CVX -> 3.2680
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,290 [CACHE-ENRICH] INFO: signal_open_position: evaluated F -> 3.2720
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,308 [CACHE-ENRICH] INFO: signal_open_position: evaluated GM -> 3.7470
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,326 [CACHE-ENRICH] INFO: signal_open_position: evaluated GOOGL -> 3.1560
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,344 [CACHE-ENRICH] INFO: signal_open_position: evaluated HD -> 2.9580
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,362 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 3.9370
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,380 [CACHE-ENRICH] INFO: signal_open_position: evaluated JNJ -> 3.1180
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,398 [CACHE-ENRICH] INFO: signal_open_position: evaluated JPM -> 3.4070
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,417 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 3.9260
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,436 [CACHE-ENRICH] INFO: signal_open_position: evaluated LOW -> 2.9690
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,456 [CACHE-ENRICH] INFO: signal_open_position: evaluated MA -> 3.2290
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,475 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.6150
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,494 [CACHE-ENRICH] INFO: signal_open_position: evaluated MS -> 3.5730
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,513 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.6510
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,531 [CACHE-ENRICH] INFO: signal_open_position: evaluated NIO -> 3.7210
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,549 [CACHE-ENRICH] INFO: signal_open_position: evaluated NVDA -> 3.8090
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,570 [CACHE-ENRICH] INFO: signal_open_position: evaluated PFE -> 3.3770
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,589 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.8570
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,609 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 3.8850
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,627 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.4260
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,645 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.9260
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,664 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.3100
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,683 [CACHE-ENRICH] INFO: signal_open_position: evaluated UNH -> 3.5310
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,706 [CACHE-ENRICH] INFO: signal_open_position: evaluated WFC -> 3.3360
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,728 [CACHE-ENRICH] INFO: signal_open_position: evaluated WMT -> 3.0270
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,747 [CACHE-ENRICH] INFO: signal_open_position: evaluated XLK -> 3.4750
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:37:52,767 [CACHE-ENRICH] INFO: signal_open_position: evaluated XOM -> 3.2580
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6876: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now = datetime.utcnow()
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: -0.0186% (entry=$15.61, current=$15.32)
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: COIN using Alpaca P&L: -0.0245% (entry=$173.75, current=$169.50)
Apr 02 01:37:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: PLTR using Alpaca P&L: -0.0167% (entry=$146.50, current=$144.05)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: LCID using Alpaca P&L: -0.0125% (entry=$9.61, current=$9.49)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: HOOD using Alpaca P&L: -0.0249% (entry=$70.15, current=$68.40)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: RIVN using Alpaca P&L: -0.0173% (entry=$15.01, current=$14.75)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MRNA using Alpaca P&L: 0.0124% (entry=$50.10, current=$49.48)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MSFT using Alpaca P&L: 0.0100% (entry=$369.55, current=$365.84)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: UNH using Alpaca P&L: 0.0119% (entry=$273.95, current=$270.70)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: COP using Alpaca P&L: -0.0238% (entry=$128.33, current=$131.38)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: PFE using Alpaca P&L: 0.0042% (entry=$28.57, current=$28.45)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MA using Alpaca P&L: -0.0131% (entry=$492.23, current=$485.80)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: WMT using Alpaca P&L: 0.0021% (entry=$124.91, current=$124.65)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: F using Alpaca P&L: -0.0094% (entry=$11.66, current=$11.55)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: XOM using Alpaca P&L: -0.0212% (entry=$161.58, current=$165.00)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: AAPL using Alpaca P&L: 0.0074% (entry=$255.38, current=$253.50)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: CVX using Alpaca P&L: -0.0183% (entry=$197.94, current=$201.57)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: GM using Alpaca P&L: 0.0124% (entry=$74.90, current=$73.97)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: NIO using Alpaca P&L: -0.0097% (entry=$6.17, current=$6.23)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: LOW using Alpaca P&L: 0.0085% (entry=$236.54, current=$234.52)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: HD using Alpaca P&L: -0.0004% (entry=$329.84, current=$329.97)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: NVDA using Alpaca P&L: 0.0190% (entry=$176.22, current=$172.88)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: GOOGL using Alpaca P&L: 0.0171% (entry=$297.79, current=$292.70)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: JNJ using Alpaca P&L: -0.0009% (entry=$244.12, current=$244.35)
Apr 02 01:37:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SLB using Alpaca P&L: 0.0126% (entry=$50.10, current=$50.73)
Apr 02 01:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: TGT using Alpaca P&L: 0.0101% (entry=$121.23, current=$120.00)
Apr 02 01:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: C using Alpaca P&L: 0.0116% (entry=$115.29, current=$113.95)
Apr 02 01:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MS using Alpaca P&L: 0.0048% (entry=$166.35, current=$165.55)
Apr 02 01:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: XLK using Alpaca P&L: 0.0140% (entry=$135.12, current=$133.23)
Apr 02 01:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: JPM using Alpaca P&L: 0.0126% (entry=$295.31, current=$291.59)
Apr 02 01:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: WFC using Alpaca P&L: 0.0126% (entry=$81.02, current=$80.00)
Apr 02 01:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: CAT using Alpaca P&L: -0.0242% (entry=$735.10, current=$717.35)
Apr 02 01:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Found 32 positions to close: ['SOFI', 'COIN', 'PLTR', 'LCID', 'HOOD', 'RIVN', 'MRNA', 'MSFT', 'UNH', 'COP', 'PFE', 'MA', 'WMT', 'F', 'XOM', 'AAPL', 'CVX', 'GM', 'NIO', 'LOW', 'HD', 'NVDA', 'GOOGL', 'JNJ', 'SLB', 'TGT', 'C', 'MS', 'XLK', 'JPM', 'WFC', 'CAT']
Apr 02 01:37:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing SOFI (decision_px=15.32, entry=15.61, hold=374.5min)
Apr 02 01:37:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SOFI (attempt 1/3): close_position_api_once returned None
Apr 02 01:37:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SOFI (attempt 2/3): close_position_api_once returned None
Apr 02 01:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SOFI (attempt 3/3): close_position_api_once returned None
Apr 02 01:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close SOFI failed
Apr 02 01:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: SOFI could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:38:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing COIN (decision_px=169.50, entry=173.75, hold=374.5min)
Apr 02 01:38:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COIN (attempt 1/3): close_position_api_once returned None
Apr 02 01:38:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COIN (attempt 2/3): close_position_api_once returned None
Apr 02 01:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 367 (iter_count=395)
Apr 02 01:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 396
Apr 02 01:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:38:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:38:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:38:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COIN (attempt 3/3): close_position_api_once returned None
Apr 02 01:38:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close COIN failed
Apr 02 01:38:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: COIN could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:38:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing PLTR (decision_px=144.05, entry=146.50, hold=374.5min)
Apr 02 01:38:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 1/3): close_position_api_once returned None
Apr 02 01:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 2/3): close_position_api_once returned None
Apr 02 01:38:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:38:24,778 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:38:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:38:25,081 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:38:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:38:25,081 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:38:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 3/3): close_position_api_once returned None
Apr 02 01:38:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close PLTR failed
Apr 02 01:38:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: PLTR could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:38:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing LCID (decision_px=9.49, entry=9.61, hold=374.6min)
Apr 02 01:38:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 1/3): close_position_api_once returned None
Apr 02 01:38:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 2/3): close_position_api_once returned None
Apr 02 01:38:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:38:35,909 [CACHE-ENRICH] INFO: Starting self-healing cycle
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:38:36,133 [CACHE-ENRICH] INFO: No issues detected - system healthy
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 3/3): close_position_api_once returned None
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close LCID failed
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: LCID could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7856: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts = info.get("ts", datetime.utcnow())
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7859: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   holding_period_min = (datetime.utcnow() - entry_ts).total_seconds() / 60.0
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing HOOD (decision_px=68.40, entry=70.15, hold=374.6min)
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7891: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts_dt = info.get("ts", datetime.utcnow())
Apr 02 01:38:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 1/3): close_position_api_once returned None
Apr 02 01:38:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 2/3): close_position_api_once returned None
Apr 02 01:38:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:38:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:38:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 3/3): close_position_api_once returned None
Apr 02 01:38:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close HOOD failed
Apr 02 01:38:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: HOOD could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:38:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing RIVN (decision_px=14.75, entry=15.01, hold=374.5min)
Apr 02 01:38:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close RIVN (attempt 1/3): close_position_api_once returned None
Apr 02 01:38:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close RIVN (attempt 2/3): close_position_api_once returned None
Apr 02 01:38:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close RIVN (attempt 3/3): close_position_api_once returned None
Apr 02 01:38:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close RIVN failed
Apr 02 01:38:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: RIVN could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:38:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MRNA (decision_px=49.48, entry=50.10, hold=374.3min)
Apr 02 01:38:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MRNA (attempt 1/3): close_position_api_once returned None
Apr 02 01:39:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MRNA (attempt 2/3): close_position_api_once returned None
Apr 02 01:39:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MRNA (attempt 3/3): close_position_api_once returned None
Apr 02 01:39:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MRNA failed
Apr 02 01:39:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MRNA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:39:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MSFT (decision_px=365.84, entry=369.55, hold=374.4min)
Apr 02 01:39:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MSFT (attempt 1/3): close_position_api_once returned None
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 368 (iter_count=396)
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 397
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12816: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   audit_seg("run_once", "ERROR", {"error": str(e), "type": type(e).__name__})
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12953: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   """Persist fail counter to disk."""
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12957: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   log_event("worker_state", "fail_count_save_error", error=str(e))
Apr 02 01:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:39:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:39:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:39:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MSFT (attempt 2/3): close_position_api_once returned None
Apr 02 01:39:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MSFT (attempt 3/3): close_position_api_once returned None
Apr 02 01:39:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MSFT failed
Apr 02 01:39:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MSFT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:39:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing UNH (decision_px=270.70, entry=273.95, hold=374.0min)
Apr 02 01:39:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close UNH (attempt 1/3): close_position_api_once returned None
Apr 02 01:39:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close UNH (attempt 2/3): close_position_api_once returned None
Apr 02 01:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:39:25,093 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:39:25,368 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:39:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:39:25,368 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:39:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close UNH (attempt 3/3): close_position_api_once returned None
Apr 02 01:39:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close UNH failed
Apr 02 01:39:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: UNH could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:39:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing COP (decision_px=131.38, entry=128.33, hold=374.0min)
Apr 02 01:39:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 1/3): close_position_api_once returned None
Apr 02 01:39:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 2/3): close_position_api_once returned None
Apr 02 01:39:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 3/3): close_position_api_once returned None
Apr 02 01:39:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close COP failed
Apr 02 01:39:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: COP could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:39:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing PFE (decision_px=28.45, entry=28.57, hold=374.0min)
Apr 02 01:39:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 1/3): close_position_api_once returned None
Apr 02 01:39:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:39:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:39:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 2/3): close_position_api_once returned None
Apr 02 01:39:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 3/3): close_position_api_once returned None
Apr 02 01:39:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close PFE failed
Apr 02 01:39:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: PFE could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:39:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MA (decision_px=485.80, entry=492.23, hold=373.8min)
Apr 02 01:39:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MA (attempt 1/3): close_position_api_once returned None
Apr 02 01:39:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MA (attempt 2/3): close_position_api_once returned None
Apr 02 01:40:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MA (attempt 3/3): close_position_api_once returned None
Apr 02 01:40:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MA failed
Apr 02 01:40:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:40:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing WMT (decision_px=124.65, entry=124.91, hold=373.8min)
Apr 02 01:40:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 1/3): close_position_api_once returned None
Apr 02 01:40:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 2/3): close_position_api_once returned None
Apr 02 01:40:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:40:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 369 (iter_count=397)
Apr 02 01:40:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 398
Apr 02 01:40:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:40:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:40:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:40:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:40:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:40:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:40:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 3/3): close_position_api_once returned None
Apr 02 01:40:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close WMT failed
Apr 02 01:40:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: WMT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:40:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing F (decision_px=11.55, entry=11.66, hold=373.8min)
Apr 02 01:40:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:40:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:40:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 1/3): close_position_api_once returned None
Apr 02 01:40:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 2/3): close_position_api_once returned None
Apr 02 01:40:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 3/3): close_position_api_once returned None
Apr 02 01:40:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close F failed
Apr 02 01:40:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: F could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:40:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing XOM (decision_px=165.00, entry=161.58, hold=373.9min)
Apr 02 01:40:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 1/3): close_position_api_once returned None
Apr 02 01:40:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:40:25,375 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:40:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:40:25,735 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:40:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:40:25,736 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:40:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 2/3): close_position_api_once returned None
Apr 02 01:40:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 3/3): close_position_api_once returned None
Apr 02 01:40:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close XOM failed
Apr 02 01:40:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: XOM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:40:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing AAPL (decision_px=253.50, entry=255.38, hold=373.9min)
Apr 02 01:40:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 1/3): close_position_api_once returned None
Apr 02 01:40:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 2/3): close_position_api_once returned None
Apr 02 01:40:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:40:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:40:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 3/3): close_position_api_once returned None
Apr 02 01:40:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close AAPL failed
Apr 02 01:40:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: AAPL could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:40:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing CVX (decision_px=201.57, entry=197.94, hold=373.8min)
Apr 02 01:40:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 1/3): close_position_api_once returned None
Apr 02 01:40:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 2/3): close_position_api_once returned None
Apr 02 01:40:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 3/3): close_position_api_once returned None
Apr 02 01:40:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close CVX failed
Apr 02 01:40:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: CVX could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:40:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing GM (decision_px=73.97, entry=74.90, hold=373.8min)
Apr 02 01:40:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 1/3): close_position_api_once returned None
Apr 02 01:41:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 2/3): close_position_api_once returned None
Apr 02 01:41:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 3/3): close_position_api_once returned None
Apr 02 01:41:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GM failed
Apr 02 01:41:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:41:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NIO (decision_px=6.23, entry=6.17, hold=374.0min)
Apr 02 01:41:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 1/3): close_position_api_once returned None
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 2/3): close_position_api_once returned None
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 370 (iter_count=398)
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 399
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:41:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:41:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:41:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:41:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 3/3): close_position_api_once returned None
Apr 02 01:41:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close NIO failed
Apr 02 01:41:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: NIO could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:41:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing LOW (decision_px=234.52, entry=236.54, hold=373.8min)
Apr 02 01:41:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 1/3): close_position_api_once returned None
Apr 02 01:41:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 2/3): close_position_api_once returned None
Apr 02 01:41:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:41:25,744 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:41:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:41:26,060 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:41:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:41:26,060 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:41:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 3/3): close_position_api_once returned None
Apr 02 01:41:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close LOW failed
Apr 02 01:41:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: LOW could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:41:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing HD (decision_px=329.97, entry=329.84, hold=373.7min)
Apr 02 01:41:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 1/3): close_position_api_once returned None
Apr 02 01:41:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 2/3): close_position_api_once returned None
Apr 02 01:41:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 3/3): close_position_api_once returned None
Apr 02 01:41:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close HD failed
Apr 02 01:41:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: HD could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:41:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NVDA (decision_px=172.88, entry=176.22, hold=373.8min)
Apr 02 01:41:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 1/3): close_position_api_once returned None
Apr 02 01:41:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 2/3): close_position_api_once returned None
Apr 02 01:41:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:41:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:41:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 3/3): close_position_api_once returned None
Apr 02 01:41:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close NVDA failed
Apr 02 01:41:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: NVDA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:41:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing GOOGL (decision_px=292.70, entry=297.79, hold=373.8min)
Apr 02 01:41:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 1/3): close_position_api_once returned None
Apr 02 01:41:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 2/3): close_position_api_once returned None
Apr 02 01:41:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 3/3): close_position_api_once returned None
Apr 02 01:41:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GOOGL failed
Apr 02 01:41:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GOOGL could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:41:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JNJ (decision_px=244.35, entry=244.12, hold=373.7min)
Apr 02 01:42:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 1/3): close_position_api_once returned None
Apr 02 01:42:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 2/3): close_position_api_once returned None
Apr 02 01:42:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 3/3): close_position_api_once returned None
Apr 02 01:42:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JNJ failed
Apr 02 01:42:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JNJ could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:42:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing SLB (decision_px=50.73, entry=50.10, hold=373.6min)
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 1/3): close_position_api_once returned None
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 371 (iter_count=399)
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 400
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Heartbeat file OK: state/bot_heartbeat.json (iter 400)
Apr 02 01:42:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:42:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:42:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:42:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 2/3): close_position_api_once returned None
Apr 02 01:42:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 3/3): close_position_api_once returned None
Apr 02 01:42:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close SLB failed
Apr 02 01:42:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: SLB could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:42:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing TGT (decision_px=120.00, entry=121.23, hold=373.8min)
Apr 02 01:42:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 1/3): close_position_api_once returned None
Apr 02 01:42:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 2/3): close_position_api_once returned None
Apr 02 01:42:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:42:26,069 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:42:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:42:26,370 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:42:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:42:26,370 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:42:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 3/3): close_position_api_once returned None
Apr 02 01:42:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close TGT failed
Apr 02 01:42:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: TGT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:42:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing C (decision_px=113.95, entry=115.29, hold=373.6min)
Apr 02 01:42:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 1/3): close_position_api_once returned None
Apr 02 01:42:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 2/3): close_position_api_once returned None
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:42:39 UTC] ----------------------------------------
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:42:39 UTC] SERVICE STATUS:
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:42:39 UTC]   dashboard: RUNNING (health: OK)
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:42:39 UTC]   trading-bot: RUNNING (health: OK)
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:42:39 UTC]   v4-research: EXITED(0) (health: OK)
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:42:39 UTC]   heartbeat-keeper: RUNNING (health: OK)
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:42:39 UTC] OVERALL SYSTEM HEALTH: OK
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:42:39 UTC] Uptime: 425 minutes
Apr 02 01:42:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 01:42:39 UTC] ----------------------------------------
Apr 02 01:42:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 3/3): close_position_api_once returned None
Apr 02 01:42:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close C failed
Apr 02 01:42:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: C could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:42:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MS (decision_px=165.55, entry=166.35, hold=373.1min)
Apr 02 01:42:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 1/3): close_position_api_once returned None
Apr 02 01:42:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:42:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:42:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 2/3): close_position_api_once returned None
Apr 02 01:42:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 3/3): close_position_api_once returned None
Apr 02 01:42:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MS failed
Apr 02 01:42:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MS could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:42:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing XLK (decision_px=133.23, entry=135.12, hold=372.9min)
Apr 02 01:42:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 1/3): close_position_api_once returned None
Apr 02 01:42:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 2/3): close_position_api_once returned None
Apr 02 01:43:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 3/3): close_position_api_once returned None
Apr 02 01:43:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close XLK failed
Apr 02 01:43:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: XLK could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:43:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JPM (decision_px=291.59, entry=295.31, hold=372.9min)
Apr 02 01:43:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 1/3): close_position_api_once returned None
Apr 02 01:43:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 2/3): close_position_api_once returned None
Apr 02 01:43:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:43:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 372 (iter_count=400)
Apr 02 01:43:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 401
Apr 02 01:43:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:43:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:43:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:43:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:43:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:43:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:43:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 3/3): close_position_api_once returned None
Apr 02 01:43:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JPM failed
Apr 02 01:43:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JPM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:43:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing WFC (decision_px=80.00, entry=81.02, hold=373.0min)
Apr 02 01:43:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:43:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:43:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 1/3): close_position_api_once returned None
Apr 02 01:43:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 2/3): close_position_api_once returned None
Apr 02 01:43:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 3/3): close_position_api_once returned None
Apr 02 01:43:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close WFC failed
Apr 02 01:43:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: WFC could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:43:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing CAT (decision_px=717.35, entry=735.10, hold=372.3min)
Apr 02 01:43:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 1/3): close_position_api_once returned None
Apr 02 01:43:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:43:26,378 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:43:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:43:26,687 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:43:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:43:26,688 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:43:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 2/3): close_position_api_once returned None
Apr 02 01:43:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 3/3): close_position_api_once returned None
Apr 02 01:43:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close CAT failed
Apr 02 01:43:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: CAT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 01:43:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Apr 02 01:43:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:43:36,135 [CACHE-ENRICH] INFO: Starting self-healing cycle
Apr 02 01:43:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:43:36,326 [CACHE-ENRICH] INFO: No issues detected - system healthy
Apr 02 01:43:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:43:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 373 (iter_count=401)
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 402
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12816: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   audit_seg("run_once", "ERROR", {"error": str(e), "type": type(e).__name__})
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12953: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   """Persist fail counter to disk."""
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12957: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   log_event("worker_state", "fail_count_save_error", error=str(e))
Apr 02 01:44:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 01:44:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:44:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 01:44:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:26,695 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 01:44:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:26,993 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 01:44:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:26,993 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 01:44:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $162,500.88, Equity: $47,210.77
Apr 02 01:44:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,070 [CACHE-ENRICH] INFO: signal_open_position: evaluated AAPL -> 3.2120
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6772: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,089 [CACHE-ENRICH] INFO: signal_open_position: evaluated C -> 3.6860
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,110 [CACHE-ENRICH] INFO: signal_open_position: evaluated CAT -> 3.6280
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,127 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.8180
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,144 [CACHE-ENRICH] INFO: signal_open_position: evaluated COP -> 3.3540
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,164 [CACHE-ENRICH] INFO: signal_open_position: evaluated CVX -> 3.1890
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,182 [CACHE-ENRICH] INFO: signal_open_position: evaluated F -> 3.1940
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,201 [CACHE-ENRICH] INFO: signal_open_position: evaluated GM -> 3.6690
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,219 [CACHE-ENRICH] INFO: signal_open_position: evaluated GOOGL -> 3.0790
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,237 [CACHE-ENRICH] INFO: signal_open_position: evaluated HD -> 2.8870
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,254 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 3.8580
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,273 [CACHE-ENRICH] INFO: signal_open_position: evaluated JNJ -> 3.0420
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,292 [CACHE-ENRICH] INFO: signal_open_position: evaluated JPM -> 3.3290
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,311 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 3.8470
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,330 [CACHE-ENRICH] INFO: signal_open_position: evaluated LOW -> 2.9000
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,350 [CACHE-ENRICH] INFO: signal_open_position: evaluated MA -> 3.1530
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,370 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.5370
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,388 [CACHE-ENRICH] INFO: signal_open_position: evaluated MS -> 3.4950
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,408 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.5740
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,428 [CACHE-ENRICH] INFO: signal_open_position: evaluated NIO -> 3.6420
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,446 [CACHE-ENRICH] INFO: signal_open_position: evaluated NVDA -> 3.7320
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,465 [CACHE-ENRICH] INFO: signal_open_position: evaluated PFE -> 3.2980
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,487 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.7770
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,507 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 3.8070
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,527 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.3480
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,545 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.8470
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,562 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.2360
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,581 [CACHE-ENRICH] INFO: signal_open_position: evaluated UNH -> 3.4550
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,601 [CACHE-ENRICH] INFO: signal_open_position: evaluated WFC -> 3.2580
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,622 [CACHE-ENRICH] INFO: signal_open_position: evaluated WMT -> 2.9550
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,640 [CACHE-ENRICH] INFO: signal_open_position: evaluated XLK -> 3.3980
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 01:44:35,659 [CACHE-ENRICH] INFO: signal_open_position: evaluated XOM -> 3.1800
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6876: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now = datetime.utcnow()
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: -0.0192% (entry=$15.61, current=$15.31)
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: COIN using Alpaca P&L: -0.0273% (entry=$173.75, current=$169.00)
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: PLTR using Alpaca P&L: -0.0171% (entry=$146.50, current=$144.00)
Apr 02 01:44:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: LCID using Alpaca P&L: -0.0125% (entry=$9.61, current=$9.49)
Apr 02 01:44:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: HOOD using Alpaca P&L: -0.0271% (entry=$70.15, current=$68.25)
Apr 02 01:44:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: RIVN using Alpaca P&L: -0.0173% (entry=$15.01, current=$14.75)
Apr 02 01:44:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MRNA using Alpaca P&L: 0.0124% (entry=$50.10, current=$49.48)
Apr 02 01:44:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MSFT using Alpaca P&L: 0.0096% (entry=$369.55, current=$366.00)
Apr 02 01:44:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: UNH using Alpaca P&L: 0.0097% (entry=$273.95, current=$271.30)
Apr 02 01:44:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: COP using Alpaca P&L: -0.0238% (entry=$128.33, current=$131.38)
Apr 02 01:44:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: PFE using Alpaca P&L: 0.0035% (entry=$28.57, current=$28.47)
Apr 02 01:44:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-b
```

## Paper-only proof

- **paper endpoint / mode detected in combined unit+main sample:** **True**
- **`main.py` `submit_order` string hits:** 24 (live executor; unchanged by this mission).
- **`paper_cap_enforcement.py` `submit_order` hits:** 0 (must stay 0).
- **Pointers:** main.py Config TRADING_MODE / ALPACA_BASE_URL (~351–352); main.py _is_paper_url / paper-only enforcement (~916–951); main.py AlpacaExecutor._submit_order_guarded → api.submit_order (~4316–4452)
