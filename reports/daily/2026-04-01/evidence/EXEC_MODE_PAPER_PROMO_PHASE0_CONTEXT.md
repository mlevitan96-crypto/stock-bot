# EXEC_MODE_PAPER_PROMO_PHASE0_CONTEXT

## git rev-parse HEAD

```
cd8d48992863c3641037e7aee139ce2ffdf6744c
```

## systemctl status

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Wed 2026-04-01 18:36:53 UTC; 8h ago
   Main PID: 1847213 (systemd_start.s)
      Tasks: 35 (limit: 9483)
     Memory: 853.4M (peak: 878.8M)
        CPU: 1h 5min 30.488s
     CGroup: /system.slice/stock-bot.service
             ├─1847213 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1847215 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1847221 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1847232 /root/stock-bot/venv/bin/python -u main.py
             └─1847256 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Apr 02 02:41:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 1/3): close_position_api_once returned None
Apr 02 02:41:27 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 2/3): close_position_api_once returned None
Apr 02 02:41:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 3/3): close_position_api_once returned None
Apr 02 02:41:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GM failed
Apr 02 02:41:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:41:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NIO (decision_px=6.08, entry=6.17, hold=434.4min)
Apr 02 02:41:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 1/3): close_position_api_once returned None
Apr 02 02:41:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:41:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:41:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 2/3): close_position_api_once returned None

```

## systemctl cat

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

## journalctl

```
Apr 02 02:28:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7859: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:28:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   holding_period_min = (datetime.utcnow() - entry_ts).total_seconds() / 60.0
Apr 02 02:28:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NVDA (decision_px=172.00, entry=176.22, hold=420.8min)
Apr 02 02:28:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7891: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:28:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts_dt = info.get("ts", datetime.utcnow())
Apr 02 02:28:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 1/3): close_position_api_once returned None
Apr 02 02:28:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:28:41,242 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:28:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:28:41,564 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:28:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:28:41,565 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:28:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 2/3): close_position_api_once returned None
Apr 02 02:28:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 3/3): close_position_api_once returned None
Apr 02 02:28:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close NVDA failed
Apr 02 02:28:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: NVDA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:28:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing GOOGL (decision_px=291.20, entry=297.79, hold=420.8min)
Apr 02 02:28:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 1/3): close_position_api_once returned None
Apr 02 02:28:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 2/3): close_position_api_once returned None
Apr 02 02:28:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:28:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:29:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 3/3): close_position_api_once returned None
Apr 02 02:29:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GOOGL failed
Apr 02 02:29:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GOOGL could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:29:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JNJ (decision_px=244.35, entry=244.12, hold=420.7min)
Apr 02 02:29:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 1/3): close_position_api_once returned None
Apr 02 02:29:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 2/3): close_position_api_once returned None
Apr 02 02:29:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 3/3): close_position_api_once returned None
Apr 02 02:29:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JNJ failed
Apr 02 02:29:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JNJ could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:29:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing SLB (decision_px=51.31, entry=50.10, hold=420.6min)
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 418 (iter_count=446)
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 447
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12816: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   audit_seg("run_once", "ERROR", {"error": str(e), "type": type(e).__name__})
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12953: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   """Persist fail counter to disk."""
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12957: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   log_event("worker_state", "fail_count_save_error", error=str(e))
Apr 02 02:29:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:29:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 1/3): close_position_api_once returned None
Apr 02 02:29:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 2/3): close_position_api_once returned None
Apr 02 02:29:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 3/3): close_position_api_once returned None
Apr 02 02:29:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close SLB failed
Apr 02 02:29:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: SLB could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:29:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing TGT (decision_px=119.50, entry=121.23, hold=420.8min)
Apr 02 02:29:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 1/3): close_position_api_once returned None
Apr 02 02:29:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 2/3): close_position_api_once returned None
Apr 02 02:29:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:29:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:29:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 3/3): close_position_api_once returned None
Apr 02 02:29:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close TGT failed
Apr 02 02:29:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: TGT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:29:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing C (decision_px=113.00, entry=115.29, hold=420.6min)
Apr 02 02:29:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 1/3): close_position_api_once returned None
Apr 02 02:29:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 2/3): close_position_api_once returned None
Apr 02 02:29:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:29:41,575 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:29:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:29:41,897 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:29:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:29:41,898 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:29:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 3/3): close_position_api_once returned None
Apr 02 02:29:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close C failed
Apr 02 02:29:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: C could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:29:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MS (decision_px=163.30, entry=166.35, hold=420.1min)
Apr 02 02:29:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 1/3): close_position_api_once returned None
Apr 02 02:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 2/3): close_position_api_once returned None
Apr 02 02:29:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 3/3): close_position_api_once returned None
Apr 02 02:29:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MS failed
Apr 02 02:29:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MS could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:29:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing XLK (decision_px=132.50, entry=135.12, hold=420.0min)
Apr 02 02:29:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 1/3): close_position_api_once returned None
Apr 02 02:29:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 2/3): close_position_api_once returned None
Apr 02 02:30:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:30:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:30:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 3/3): close_position_api_once returned None
Apr 02 02:30:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close XLK failed
Apr 02 02:30:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: XLK could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:30:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JPM (decision_px=290.65, entry=295.31, hold=419.9min)
Apr 02 02:30:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 1/3): close_position_api_once returned None
Apr 02 02:30:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 2/3): close_position_api_once returned None
Apr 02 02:30:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:30:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 419 (iter_count=447)
Apr 02 02:30:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 448
Apr 02 02:30:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:30:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:30:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:30:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:30:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:30:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:30:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 3/3): close_position_api_once returned None
Apr 02 02:30:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JPM failed
Apr 02 02:30:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JPM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:30:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing WFC (decision_px=79.95, entry=81.02, hold=420.0min)
Apr 02 02:30:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 1/3): close_position_api_once returned None
Apr 02 02:30:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 2/3): close_position_api_once returned None
Apr 02 02:30:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 3/3): close_position_api_once returned None
Apr 02 02:30:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close WFC failed
Apr 02 02:30:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: WFC could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:30:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing CAT (decision_px=716.60, entry=735.10, hold=419.3min)
Apr 02 02:30:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 1/3): close_position_api_once returned None
Apr 02 02:30:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 2/3): close_position_api_once returned None
Apr 02 02:30:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:30:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:30:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 3/3): close_position_api_once returned None
Apr 02 02:30:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close CAT failed
Apr 02 02:30:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: CAT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:30:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Apr 02 02:30:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:30:41,907 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:30:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:30:42,198 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:30:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:30:42,198 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:31:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:31:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:31:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:31:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 420 (iter_count=448)
Apr 02 02:31:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 449
Apr 02 02:31:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:31:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:31:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:31:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:31:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:31:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:31:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:31:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:31:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $162,500.88, Equity: $47,220.02
Apr 02 02:31:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,091 [CACHE-ENRICH] INFO: signal_open_position: evaluated AAPL -> 3.4260
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6772: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,112 [CACHE-ENRICH] INFO: signal_open_position: evaluated C -> 3.8990
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,130 [CACHE-ENRICH] INFO: signal_open_position: evaluated CAT -> 3.8350
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,148 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 4.0320
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,166 [CACHE-ENRICH] INFO: signal_open_position: evaluated COP -> 3.5710
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,185 [CACHE-ENRICH] INFO: signal_open_position: evaluated CVX -> 3.4070
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,204 [CACHE-ENRICH] INFO: signal_open_position: evaluated F -> 3.4070
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,223 [CACHE-ENRICH] INFO: signal_open_position: evaluated GM -> 3.8820
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,242 [CACHE-ENRICH] INFO: signal_open_position: evaluated GOOGL -> 3.2880
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,261 [CACHE-ENRICH] INFO: signal_open_position: evaluated HD -> 3.0800
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,280 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 4.0750
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,299 [CACHE-ENRICH] INFO: signal_open_position: evaluated JNJ -> 3.2500
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,318 [CACHE-ENRICH] INFO: signal_open_position: evaluated JPM -> 3.5420
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,337 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 4.0640
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,356 [CACHE-ENRICH] INFO: signal_open_position: evaluated LOW -> 3.0890
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,375 [CACHE-ENRICH] INFO: signal_open_position: evaluated MA -> 3.3610
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,394 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.7500
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,414 [CACHE-ENRICH] INFO: signal_open_position: evaluated MS -> 3.7080
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,433 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.7860
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,453 [CACHE-ENRICH] INFO: signal_open_position: evaluated NIO -> 3.8590
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,473 [CACHE-ENRICH] INFO: signal_open_position: evaluated NVDA -> 3.9440
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,493 [CACHE-ENRICH] INFO: signal_open_position: evaluated PFE -> 3.5150
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,511 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.9980
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,530 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 4.0200
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,548 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.5610
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,565 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 4.0640
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,582 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.4390
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,600 [CACHE-ENRICH] INFO: signal_open_position: evaluated UNH -> 3.6630
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,617 [CACHE-ENRICH] INFO: signal_open_position: evaluated WFC -> 3.4720
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,634 [CACHE-ENRICH] INFO: signal_open_position: evaluated WMT -> 3.1510
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,653 [CACHE-ENRICH] INFO: signal_open_position: evaluated XLK -> 3.6080
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:36,673 [CACHE-ENRICH] INFO: signal_open_position: evaluated XOM -> 3.3930
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6876: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now = datetime.utcnow()
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: -0.0218% (entry=$15.61, current=$15.27)
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: COIN using Alpaca P&L: -0.0310% (entry=$173.75, current=$168.37)
Apr 02 02:31:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: PLTR using Alpaca P&L: -0.0208% (entry=$146.50, current=$143.45)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: LCID using Alpaca P&L: -0.0187% (entry=$9.61, current=$9.43)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: HOOD using Alpaca P&L: -0.0339% (entry=$70.15, current=$67.77)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: RIVN using Alpaca P&L: -0.0213% (entry=$15.01, current=$14.69)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MRNA using Alpaca P&L: 0.0220% (entry=$50.10, current=$49.00)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MSFT using Alpaca P&L: 0.0136% (entry=$369.55, current=$364.51)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: UNH using Alpaca P&L: 0.0147% (entry=$273.95, current=$269.93)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: COP using Alpaca P&L: -0.0361% (entry=$128.33, current=$132.96)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: PFE using Alpaca P&L: 0.0095% (entry=$28.57, current=$28.30)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MA using Alpaca P&L: -0.0108% (entry=$492.23, current=$486.91)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: WMT using Alpaca P&L: 0.0017% (entry=$124.91, current=$124.70)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: F using Alpaca P&L: -0.0137% (entry=$11.66, current=$11.50)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: XOM using Alpaca P&L: -0.0255% (entry=$161.58, current=$165.70)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: AAPL using Alpaca P&L: 0.0076% (entry=$255.38, current=$253.44)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: CVX using Alpaca P&L: -0.0230% (entry=$197.94, current=$202.50)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: GM using Alpaca P&L: 0.0124% (entry=$74.90, current=$73.97)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: NIO using Alpaca P&L: 0.0178% (entry=$6.17, current=$6.06)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: LOW using Alpaca P&L: 0.0085% (entry=$236.54, current=$234.52)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: HD using Alpaca P&L: -0.0004% (entry=$329.84, current=$329.97)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: NVDA using Alpaca P&L: 0.0243% (entry=$176.22, current=$171.94)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: GOOGL using Alpaca P&L: 0.0221% (entry=$297.79, current=$291.20)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: JNJ using Alpaca P&L: 0.0046% (entry=$244.12, current=$242.99)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SLB using Alpaca P&L: 0.0242% (entry=$50.10, current=$51.31)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: TGT using Alpaca P&L: 0.0143% (entry=$121.23, current=$119.50)
Apr 02 02:31:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: C using Alpaca P&L: 0.0177% (entry=$115.29, current=$113.25)
Apr 02 02:31:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MS using Alpaca P&L: 0.0183% (entry=$166.35, current=$163.30)
Apr 02 02:31:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: XLK using Alpaca P&L: 0.0194% (entry=$135.12, current=$132.50)
Apr 02 02:31:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: JPM using Alpaca P&L: 0.0178% (entry=$295.31, current=$290.05)
Apr 02 02:31:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: WFC using Alpaca P&L: 0.0190% (entry=$81.02, current=$79.48)
Apr 02 02:31:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: CAT using Alpaca P&L: -0.0252% (entry=$735.10, current=$716.60)
Apr 02 02:31:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Found 32 positions to close: ['SOFI', 'COIN', 'PLTR', 'LCID', 'HOOD', 'RIVN', 'MRNA', 'MSFT', 'UNH', 'COP', 'PFE', 'MA', 'WMT', 'F', 'XOM', 'AAPL', 'CVX', 'GM', 'NIO', 'LOW', 'HD', 'NVDA', 'GOOGL', 'JNJ', 'SLB', 'TGT', 'C', 'MS', 'XLK', 'JPM', 'WFC', 'CAT']
Apr 02 02:31:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing SOFI (decision_px=15.27, entry=15.61, hold=428.2min)
Apr 02 02:31:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SOFI (attempt 1/3): close_position_api_once returned None
Apr 02 02:31:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:42,207 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:31:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:42,511 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:31:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:31:42,511 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:31:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SOFI (attempt 2/3): close_position_api_once returned None
Apr 02 02:31:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SOFI (attempt 3/3): close_position_api_once returned None
Apr 02 02:31:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close SOFI failed
Apr 02 02:31:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: SOFI could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:31:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing COIN (decision_px=168.37, entry=173.75, hold=428.2min)
Apr 02 02:31:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COIN (attempt 1/3): close_position_api_once returned None
Apr 02 02:31:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COIN (attempt 2/3): close_position_api_once returned None
Apr 02 02:31:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COIN (attempt 3/3): close_position_api_once returned None
Apr 02 02:31:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close COIN failed
Apr 02 02:31:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: COIN could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:31:59 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing PLTR (decision_px=143.45, entry=146.50, hold=428.3min)
Apr 02 02:32:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:32:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:32:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 1/3): close_position_api_once returned None
Apr 02 02:32:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 2/3): close_position_api_once returned None
Apr 02 02:32:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 3/3): close_position_api_once returned None
Apr 02 02:32:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close PLTR failed
Apr 02 02:32:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: PLTR could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:32:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing LCID (decision_px=9.43, entry=9.61, hold=428.4min)
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 421 (iter_count=449)
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 450
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Heartbeat file OK: state/bot_heartbeat.json (iter 450)
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:32:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 1/3): close_position_api_once returned None
Apr 02 02:32:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 2/3): close_position_api_once returned None
Apr 02 02:32:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 3/3): close_position_api_once returned None
Apr 02 02:32:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close LCID failed
Apr 02 02:32:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: LCID could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:32:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing HOOD (decision_px=67.77, entry=70.15, hold=428.3min)
Apr 02 02:32:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 1/3): close_position_api_once returned None
Apr 02 02:32:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 2/3): close_position_api_once returned None
Apr 02 02:32:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:32:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:32:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 3/3): close_position_api_once returned None
Apr 02 02:32:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close HOOD failed
Apr 02 02:32:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: HOOD could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:32:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing RIVN (decision_px=14.69, entry=15.01, hold=428.3min)
Apr 02 02:32:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close RIVN (attempt 1/3): close_position_api_once returned None
Apr 02 02:32:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close RIVN (attempt 2/3): close_position_api_once returned None
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:32:41 UTC] ----------------------------------------
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:32:41 UTC] SERVICE STATUS:
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:32:41 UTC]   dashboard: RUNNING (health: OK)
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:32:41 UTC]   trading-bot: RUNNING (health: OK)
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:32:41 UTC]   v4-research: EXITED(0) (health: OK)
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:32:41 UTC]   heartbeat-keeper: RUNNING (health: OK)
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:32:41 UTC] OVERALL SYSTEM HEALTH: OK
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:32:41 UTC] Uptime: 475 minutes
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:32:41 UTC] ----------------------------------------
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close RIVN (attempt 3/3): close_position_api_once returned None
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close RIVN failed
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: RIVN could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:32:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MRNA (decision_px=49.00, entry=50.10, hold=428.0min)
Apr 02 02:32:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:32:42,522 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:32:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:32:42,814 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:32:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:32:42,814 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:32:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MRNA (attempt 1/3): close_position_api_once returned None
Apr 02 02:32:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MRNA (attempt 2/3): close_position_api_once returned None
Apr 02 02:32:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MRNA (attempt 3/3): close_position_api_once returned None
Apr 02 02:32:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MRNA failed
Apr 02 02:32:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MRNA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:32:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MSFT (decision_px=364.51, entry=369.55, hold=428.2min)
Apr 02 02:32:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MSFT (attempt 1/3): close_position_api_once returned None
Apr 02 02:32:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MSFT (attempt 2/3): close_position_api_once returned None
Apr 02 02:33:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:33:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:33:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MSFT (attempt 3/3): close_position_api_once returned None
Apr 02 02:33:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MSFT failed
Apr 02 02:33:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MSFT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:33:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing UNH (decision_px=269.93, entry=273.95, hold=427.7min)
Apr 02 02:33:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close UNH (attempt 1/3): close_position_api_once returned None
Apr 02 02:33:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close UNH (attempt 2/3): close_position_api_once returned None
Apr 02 02:33:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:33:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 422 (iter_count=450)
Apr 02 02:33:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 451
Apr 02 02:33:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:33:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:33:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:33:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:33:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:33:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:33:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close UNH (attempt 3/3): close_position_api_once returned None
Apr 02 02:33:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close UNH failed
Apr 02 02:33:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: UNH could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:33:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing COP (decision_px=132.96, entry=128.33, hold=427.7min)
Apr 02 02:33:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 1/3): close_position_api_once returned None
Apr 02 02:33:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 2/3): close_position_api_once returned None
Apr 02 02:33:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COP (attempt 3/3): close_position_api_once returned None
Apr 02 02:33:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close COP failed
Apr 02 02:33:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: COP could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:33:24 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing PFE (decision_px=28.30, entry=28.57, hold=427.8min)
Apr 02 02:33:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 1/3): close_position_api_once returned None
Apr 02 02:33:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 2/3): close_position_api_once returned None
Apr 02 02:33:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:33:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:33:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PFE (attempt 3/3): close_position_api_once returned None
Apr 02 02:33:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close PFE failed
Apr 02 02:33:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: PFE could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:33:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MA (decision_px=486.91, entry=492.23, hold=427.5min)
Apr 02 02:33:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MA (attempt 1/3): close_position_api_once returned None
Apr 02 02:33:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:33:38,811 [CACHE-ENRICH] INFO: Starting self-healing cycle
Apr 02 02:33:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:33:39,019 [CACHE-ENRICH] INFO: No issues detected - system healthy
Apr 02 02:33:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MA (attempt 2/3): close_position_api_once returned None
Apr 02 02:33:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:33:42,823 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:33:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:33:43,131 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:33:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:33:43,131 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MA (attempt 3/3): close_position_api_once returned None
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MA failed
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7856: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts = info.get("ts", datetime.utcnow())
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7859: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   holding_period_min = (datetime.utcnow() - entry_ts).total_seconds() / 60.0
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing WMT (decision_px=124.70, entry=124.91, hold=427.6min)
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7891: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:33:45 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts_dt = info.get("ts", datetime.utcnow())
Apr 02 02:33:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 1/3): close_position_api_once returned None
Apr 02 02:33:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 2/3): close_position_api_once returned None
Apr 02 02:33:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WMT (attempt 3/3): close_position_api_once returned None
Apr 02 02:33:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close WMT failed
Apr 02 02:33:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: WMT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:33:56 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing F (decision_px=11.50, entry=11.66, hold=427.5min)
Apr 02 02:33:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 1/3): close_position_api_once returned None
Apr 02 02:34:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:34:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:34:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 2/3): close_position_api_once returned None
Apr 02 02:34:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close F (attempt 3/3): close_position_api_once returned None
Apr 02 02:34:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close F failed
Apr 02 02:34:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: F could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:34:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing XOM (decision_px=165.70, entry=161.58, hold=427.6min)
Apr 02 02:34:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 1/3): close_position_api_once returned None
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 423 (iter_count=451)
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 452
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12816: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   audit_seg("run_once", "ERROR", {"error": str(e), "type": type(e).__name__})
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12953: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   """Persist fail counter to disk."""
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12957: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   log_event("worker_state", "fail_count_save_error", error=str(e))
Apr 02 02:34:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:34:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 2/3): close_position_api_once returned None
Apr 02 02:34:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 3/3): close_position_api_once returned None
Apr 02 02:34:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close XOM failed
Apr 02 02:34:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: XOM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:34:17 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing AAPL (decision_px=253.44, entry=255.38, hold=427.6min)
Apr 02 02:34:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 1/3): close_position_api_once returned None
Apr 02 02:34:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 2/3): close_position_api_once returned None
Apr 02 02:34:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close AAPL (attempt 3/3): close_position_api_once returned None
Apr 02 02:34:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close AAPL failed
Apr 02 02:34:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: AAPL could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:34:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing CVX (decision_px=202.50, entry=197.94, hold=427.5min)
Apr 02 02:34:29 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 1/3): close_position_api_once returned None
Apr 02 02:34:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:34:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:34:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 2/3): close_position_api_once returned None
Apr 02 02:34:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CVX (attempt 3/3): close_position_api_once returned None
Apr 02 02:34:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close CVX failed
Apr 02 02:34:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: CVX could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:34:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing GM (decision_px=73.97, entry=74.90, hold=427.6min)
Apr 02 02:34:40 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 1/3): close_position_api_once returned None
Apr 02 02:34:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:34:43,140 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:34:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:34:43,476 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:34:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:34:43,476 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:34:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 2/3): close_position_api_once returned None
Apr 02 02:34:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GM (attempt 3/3): close_position_api_once returned None
Apr 02 02:34:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GM failed
Apr 02 02:34:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:34:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NIO (decision_px=6.06, entry=6.17, hold=427.7min)
Apr 02 02:34:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 1/3): close_position_api_once returned None
Apr 02 02:34:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 2/3): close_position_api_once returned None
Apr 02 02:34:55 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:34:55,282 [CACHE-ENRICH] INFO: 79.124.40.174 - - [02/Apr/2026 02:34:55] "GET /jars HTTP/1.1" 404 -
Apr 02 02:35:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NIO (attempt 3/3): close_position_api_once returned None
Apr 02 02:35:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close NIO failed
Apr 02 02:35:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: NIO could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:35:00 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing LOW (decision_px=234.52, entry=236.54, hold=427.6min)
Apr 02 02:35:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 1/3): close_position_api_once returned None
Apr 02 02:35:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:35:01 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:35:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 2/3): close_position_api_once returned None
Apr 02 02:35:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LOW (attempt 3/3): close_position_api_once returned None
Apr 02 02:35:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close LOW failed
Apr 02 02:35:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: LOW could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:35:10 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing HD (decision_px=329.97, entry=329.84, hold=427.4min)
Apr 02 02:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 424 (iter_count=452)
Apr 02 02:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 453
Apr 02 02:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:35:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:35:12 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 1/3): close_position_api_once returned None
Apr 02 02:35:15 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 2/3): close_position_api_once returned None
Apr 02 02:35:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HD (attempt 3/3): close_position_api_once returned None
Apr 02 02:35:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close HD failed
Apr 02 02:35:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: HD could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:35:21 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing NVDA (decision_px=171.94, entry=176.22, hold=427.5min)
Apr 02 02:35:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 1/3): close_position_api_once returned None
Apr 02 02:35:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 2/3): close_position_api_once returned None
Apr 02 02:35:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:35:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:35:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 3/3): close_position_api_once returned None
Apr 02 02:35:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close NVDA failed
Apr 02 02:35:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: NVDA could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:35:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing GOOGL (decision_px=291.20, entry=297.79, hold=427.5min)
Apr 02 02:35:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 1/3): close_position_api_once returned None
Apr 02 02:35:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 2/3): close_position_api_once returned None
Apr 02 02:35:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close GOOGL (attempt 3/3): close_position_api_once returned None
Apr 02 02:35:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close GOOGL failed
Apr 02 02:35:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: GOOGL could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:35:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JNJ (decision_px=242.99, entry=244.12, hold=427.4min)
Apr 02 02:35:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:35:43,485 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:35:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:35:43,876 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:35:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:35:43,876 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:35:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 1/3): close_position_api_once returned None
Apr 02 02:35:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 2/3): close_position_api_once returned None
Apr 02 02:35:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JNJ (attempt 3/3): close_position_api_once returned None
Apr 02 02:35:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JNJ failed
Apr 02 02:35:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JNJ could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:35:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing SLB (decision_px=51.31, entry=50.10, hold=427.4min)
Apr 02 02:35:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 1/3): close_position_api_once returned None
Apr 02 02:35:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 2/3): close_position_api_once returned None
Apr 02 02:36:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:36:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:36:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SLB (attempt 3/3): close_position_api_once returned None
Apr 02 02:36:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close SLB failed
Apr 02 02:36:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: SLB could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:36:04 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing TGT (decision_px=119.50, entry=121.23, hold=427.5min)
Apr 02 02:36:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 1/3): close_position_api_once returned None
Apr 02 02:36:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 2/3): close_position_api_once returned None
Apr 02 02:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 425 (iter_count=453)
Apr 02 02:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 454
Apr 02 02:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:36:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:36:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close TGT (attempt 3/3): close_position_api_once returned None
Apr 02 02:36:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close TGT failed
Apr 02 02:36:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: TGT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:36:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing C (decision_px=113.25, entry=115.29, hold=427.3min)
Apr 02 02:36:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 1/3): close_position_api_once returned None
Apr 02 02:36:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 2/3): close_position_api_once returned None
Apr 02 02:36:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close C (attempt 3/3): close_position_api_once returned None
Apr 02 02:36:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close C failed
Apr 02 02:36:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: C could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:36:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing MS (decision_px=163.30, entry=166.35, hold=426.9min)
Apr 02 02:36:26 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 1/3): close_position_api_once returned None
Apr 02 02:36:30 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 2/3): close_position_api_once returned None
Apr 02 02:36:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:36:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close MS (attempt 3/3): close_position_api_once returned None
Apr 02 02:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close MS failed
Apr 02 02:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: MS could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:36:35 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing XLK (decision_px=132.50, entry=135.12, hold=426.7min)
Apr 02 02:36:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 1/3): close_position_api_once returned None
Apr 02 02:36:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 2/3): close_position_api_once returned None
Apr 02 02:36:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:36:43,886 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:36:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:36:44,172 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:36:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:36:44,172 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:36:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close XLK (attempt 3/3): close_position_api_once returned None
Apr 02 02:36:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close XLK failed
Apr 02 02:36:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: XLK could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:36:46 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing JPM (decision_px=290.05, entry=295.31, hold=426.7min)
Apr 02 02:36:48 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 1/3): close_position_api_once returned None
Apr 02 02:36:51 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 2/3): close_position_api_once returned None
Apr 02 02:36:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 3/3): close_position_api_once returned None
Apr 02 02:36:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close JPM failed
Apr 02 02:36:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: JPM could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:36:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing WFC (decision_px=79.48, entry=81.02, hold=426.7min)
Apr 02 02:36:58 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 1/3): close_position_api_once returned None
Apr 02 02:37:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 2/3): close_position_api_once returned None
Apr 02 02:37:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:37:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:37:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close WFC (attempt 3/3): close_position_api_once returned None
Apr 02 02:37:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close WFC failed
Apr 02 02:37:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: WFC could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:37:07 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing CAT (decision_px=716.60, entry=735.10, hold=426.0min)
Apr 02 02:37:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 1/3): close_position_api_once returned None
Apr 02 02:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 426 (iter_count=454)
Apr 02 02:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 455
Apr 02 02:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:37:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:37:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 2/3): close_position_api_once returned None
Apr 02 02:37:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] [MOCK-SIGNAL] Injecting perfect whale signal at 2026-04-02T02:37:14.850372+00:00
Apr 02 02:37:14 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] [MOCK-SIGNAL] ✅ Mock signal passed: score=4.53 (>= 4.0)
Apr 02 02:37:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close CAT (attempt 3/3): close_position_api_once returned None
Apr 02 02:37:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close CAT failed
Apr 02 02:37:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: CAT could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:37:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker evaluate_exits() completed
Apr 02 02:37:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:37:32 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] Rotating logs/score_snapshot.jsonl (11.6MB)
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] Rotating logs/signals.jsonl (12.6MB)
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] Rotating logs/signal_score_breakdown.jsonl (6.9MB)
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] Rotating logs/signal_snapshots.jsonl (7.7MB)
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] Rotating state/portfolio_state.jsonl (7.8MB)
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: /root/stock-bot/deploy_supervisor.py:159: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] ----------------------------------------
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] SERVICE STATUS:
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC]   dashboard: RUNNING (health: OK)
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC]   trading-bot: RUNNING (health: OK)
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC]   v4-research: EXITED(0) (health: OK)
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC]   heartbeat-keeper: RUNNING (health: OK)
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] OVERALL SYSTEM HEALTH: OK
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] Uptime: 480 minutes
Apr 02 02:37:41 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [SUPERVISOR] [2026-04-02 02:37:41 UTC] ----------------------------------------
Apr 02 02:37:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:37:44,180 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:37:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:37:44,479 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:37:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:37:44,479 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:38:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:38:02 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 427 (iter_count=455)
Apr 02 02:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 456
Apr 02 02:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:38:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ✅ DIAGNOSTIC: Alpaca API connected - Buying Power: $162,500.88, Equity: $47,219.59
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] CRITICAL: Exit checker calling evaluate_exits()
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:18,821 [CACHE-ENRICH] INFO: signal_open_position: evaluated AAPL -> 3.3450
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6772: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:18,854 [CACHE-ENRICH] INFO: signal_open_position: evaluated C -> 3.8180
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:18,876 [CACHE-ENRICH] INFO: signal_open_position: evaluated CAT -> 3.7560
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:18,897 [CACHE-ENRICH] INFO: signal_open_position: evaluated COIN -> 3.9500
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:18,916 [CACHE-ENRICH] INFO: signal_open_position: evaluated COP -> 3.4890
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:18,936 [CACHE-ENRICH] INFO: signal_open_position: evaluated CVX -> 3.3240
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:18,959 [CACHE-ENRICH] INFO: signal_open_position: evaluated F -> 3.3260
Apr 02 02:38:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:18,980 [CACHE-ENRICH] INFO: signal_open_position: evaluated GM -> 3.8010
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:18,999 [CACHE-ENRICH] INFO: signal_open_position: evaluated GOOGL -> 3.2090
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,019 [CACHE-ENRICH] INFO: signal_open_position: evaluated HD -> 3.0070
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,039 [CACHE-ENRICH] INFO: signal_open_position: evaluated HOOD -> 3.9920
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,058 [CACHE-ENRICH] INFO: signal_open_position: evaluated JNJ -> 3.1710
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,076 [CACHE-ENRICH] INFO: signal_open_position: evaluated JPM -> 3.4610
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,095 [CACHE-ENRICH] INFO: signal_open_position: evaluated LCID -> 3.9810
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,115 [CACHE-ENRICH] INFO: signal_open_position: evaluated LOW -> 3.0170
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,134 [CACHE-ENRICH] INFO: signal_open_position: evaluated MA -> 3.2820
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,154 [CACHE-ENRICH] INFO: signal_open_position: evaluated MRNA -> 3.6690
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,173 [CACHE-ENRICH] INFO: signal_open_position: evaluated MS -> 3.6270
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,194 [CACHE-ENRICH] INFO: signal_open_position: evaluated MSFT -> 3.7050
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,215 [CACHE-ENRICH] INFO: signal_open_position: evaluated NIO -> 3.7760
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,243 [CACHE-ENRICH] INFO: signal_open_position: evaluated NVDA -> 3.8630
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,266 [CACHE-ENRICH] INFO: signal_open_position: evaluated PFE -> 3.4320
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,285 [CACHE-ENRICH] INFO: signal_open_position: evaluated PLTR -> 3.9140
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,305 [CACHE-ENRICH] INFO: signal_open_position: evaluated RIVN -> 3.9390
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,324 [CACHE-ENRICH] INFO: signal_open_position: evaluated SLB -> 3.4800
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,345 [CACHE-ENRICH] INFO: signal_open_position: evaluated SOFI -> 3.9810
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,365 [CACHE-ENRICH] INFO: signal_open_position: evaluated TGT -> 3.3620
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,385 [CACHE-ENRICH] INFO: signal_open_position: evaluated UNH -> 3.5840
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,405 [CACHE-ENRICH] INFO: signal_open_position: evaluated WFC -> 3.3900
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,424 [CACHE-ENRICH] INFO: signal_open_position: evaluated WMT -> 3.0760
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,444 [CACHE-ENRICH] INFO: signal_open_position: evaluated XLK -> 3.5280
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:19,463 [CACHE-ENRICH] INFO: signal_open_position: evaluated XOM -> 3.3120
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:6876: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   now = datetime.utcnow()
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SOFI using Alpaca P&L: -0.0218% (entry=$15.61, current=$15.27)
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: COIN using Alpaca P&L: -0.0331% (entry=$173.75, current=$168.00)
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: PLTR using Alpaca P&L: -0.0222% (entry=$146.50, current=$143.25)
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: LCID using Alpaca P&L: -0.0187% (entry=$9.61, current=$9.43)
Apr 02 02:38:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: HOOD using Alpaca P&L: -0.0345% (entry=$70.15, current=$67.73)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: RIVN using Alpaca P&L: -0.0207% (entry=$15.01, current=$14.70)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MRNA using Alpaca P&L: 0.0194% (entry=$50.10, current=$49.13)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MSFT using Alpaca P&L: 0.0137% (entry=$369.55, current=$364.50)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: UNH using Alpaca P&L: 0.0142% (entry=$273.95, current=$270.05)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: COP using Alpaca P&L: -0.0361% (entry=$128.33, current=$132.96)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: PFE using Alpaca P&L: 0.0066% (entry=$28.57, current=$28.38)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MA using Alpaca P&L: -0.0108% (entry=$492.23, current=$486.91)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: WMT using Alpaca P&L: 0.0017% (entry=$124.91, current=$124.70)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: F using Alpaca P&L: -0.0137% (entry=$11.66, current=$11.50)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: XOM using Alpaca P&L: -0.0221% (entry=$161.58, current=$165.15)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: AAPL using Alpaca P&L: 0.0081% (entry=$255.38, current=$253.32)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: CVX using Alpaca P&L: -0.0219% (entry=$197.94, current=$202.28)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: GM using Alpaca P&L: 0.0124% (entry=$74.90, current=$73.97)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: NIO using Alpaca P&L: 0.0146% (entry=$6.17, current=$6.08)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: LOW using Alpaca P&L: 0.0085% (entry=$236.54, current=$234.52)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: HD using Alpaca P&L: -0.0004% (entry=$329.84, current=$329.97)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: NVDA using Alpaca P&L: 0.0234% (entry=$176.22, current=$172.09)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: GOOGL using Alpaca P&L: 0.0220% (entry=$297.79, current=$291.24)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: JNJ using Alpaca P&L: 0.0046% (entry=$244.12, current=$242.99)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: SLB using Alpaca P&L: 0.0242% (entry=$50.10, current=$51.31)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: TGT using Alpaca P&L: 0.0218% (entry=$121.23, current=$118.59)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: C using Alpaca P&L: 0.0177% (entry=$115.29, current=$113.25)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: MS using Alpaca P&L: 0.0183% (entry=$166.35, current=$163.30)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: XLK using Alpaca P&L: 0.0193% (entry=$135.12, current=$132.51)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: JPM using Alpaca P&L: 0.0195% (entry=$295.31, current=$289.56)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: WFC using Alpaca P&L: 0.0190% (entry=$81.02, current=$79.48)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: CAT using Alpaca P&L: -0.0252% (entry=$735.10, current=$716.60)
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Found 32 positions to close: ['SOFI', 'COIN', 'PLTR', 'LCID', 'HOOD', 'RIVN', 'MRNA', 'MSFT', 'UNH', 'COP', 'PFE', 'MA', 'WMT', 'F', 'XOM', 'AAPL', 'CVX', 'GM', 'NIO', 'LOW', 'HD', 'NVDA', 'GOOGL', 'JNJ', 'SLB', 'TGT', 'C', 'MS', 'XLK', 'JPM', 'WFC', 'CAT']
Apr 02 02:38:20 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing SOFI (decision_px=15.27, entry=15.61, hold=434.9min)
Apr 02 02:38:22 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SOFI (attempt 1/3): close_position_api_once returned None
Apr 02 02:38:25 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SOFI (attempt 2/3): close_position_api_once returned None
Apr 02 02:38:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close SOFI (attempt 3/3): close_position_api_once returned None
Apr 02 02:38:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close SOFI failed
Apr 02 02:38:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: SOFI could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:38:31 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing COIN (decision_px=168.00, entry=173.75, hold=434.9min)
Apr 02 02:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COIN (attempt 1/3): close_position_api_once returned None
Apr 02 02:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:38:33 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:38:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COIN (attempt 2/3): close_position_api_once returned None
Apr 02 02:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:39,021 [CACHE-ENRICH] INFO: Starting self-healing cycle
Apr 02 02:38:39 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:39,214 [CACHE-ENRICH] INFO: No issues detected - system healthy
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close COIN (attempt 3/3): close_position_api_once returned None
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close COIN failed
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: COIN could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7856: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts = info.get("ts", datetime.utcnow())
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7859: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   holding_period_min = (datetime.utcnow() - entry_ts).total_seconds() / 60.0
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing PLTR (decision_px=143.25, entry=146.50, hold=435.0min)
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:7891: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:38:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   entry_ts_dt = info.get("ts", datetime.utcnow())
Apr 02 02:38:43 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 1/3): close_position_api_once returned None
Apr 02 02:38:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:44,491 [CACHE-ENRICH] INFO: Starting cache enrichment cycle
Apr 02 02:38:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:44,783 [CACHE-ENRICH] INFO: Enriched 53 symbols, updated 0 with computed signals
Apr 02 02:38:44 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] 2026-04-02 02:38:44,783 [CACHE-ENRICH] INFO: Cache enrichment complete: 53 symbols
Apr 02 02:38:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 2/3): close_position_api_once returned None
Apr 02 02:38:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close PLTR (attempt 3/3): close_position_api_once returned None
Apr 02 02:38:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close PLTR failed
Apr 02 02:38:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: PLTR could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:38:52 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing LCID (decision_px=9.43, entry=9.61, hold=435.1min)
Apr 02 02:38:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 1/3): close_position_api_once returned None
Apr 02 02:38:57 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 2/3): close_position_api_once returned None
Apr 02 02:39:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper] /root/stock-bot/heartbeat_keeper.py:459: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:39:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [heartbeat-keeper]   result["_dt"] = datetime.utcnow().isoformat()
Apr 02 02:39:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close LCID (attempt 3/3): close_position_api_once returned None
Apr 02 02:39:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: All 3 attempts to close LCID failed
Apr 02 02:39:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] WARNING EXITS: LCID could not be verified as closed after 3 attempts - keeping in tracking for retry
Apr 02 02:39:03 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG EXITS: Closing HOOD (decision_px=67.73, entry=70.15, hold=435.0min)
Apr 02 02:39:05 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 1/3): close_position_api_once returned None
Apr 02 02:39:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] ERROR EXITS: Failed to close HOOD (attempt 2/3): close_position_api_once returned None
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker woke up, stop_evt.is_set()=False
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Worker loop iteration 428 (iter_count=456)
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Starting iteration 457
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: About to check market status...
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: is_market_open_now() returned: False
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: Market open check: False (SIMULATE_MARKET_OPEN=False)
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot] /root/stock-bot/main.py:12816: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 02 02:39:11 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1847215]: [trading-bot]   audit_seg("run_once", "ERROR", {"error": str(e), "type": type(e).__name__})
Apr 02 02:
```

## Paper-only proof

- **paper endpoint / mode in sample:** **True**
- **Code:** `main.py` `submit_entry` → `try_paper_exec_ab_entry` (after AUDIT_DRY_RUN); strict gateway inside `paper_exec_mode_runtime.py`.
- **`paper_exec_mode_runtime.py`:** uses `executor._submit_order_guarded` only (no `api.submit_order`).
- **`main.py` `submit_order` occurrences (file-wide):** mission grep count informational only; live path unchanged for non-paper.
