# ALPACA POST-MARKET AUDIT — CONTEXT & SAFETY

- Captured UTC: `2026-03-30T20:30:01Z`
- ET calendar date (folder): **`2026-03-30`**

## Market session (Alpaca clock API)

- **Market closed (Alpaca):** `True`
- is_open=False next_open=2026-03-31 09:30:00-04:00 next_close=2026-03-31 16:00:00-04:00

## systemctl status stock-bot

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Mon 2026-03-30 18:32:35 UTC; 1h 57min ago
   Main PID: 1756284 (systemd_start.s)
      Tasks: 35 (limit: 9483)
     Memory: 770.4M (peak: 827.2M)
        CPU: 1h 9min 29.964s
     CGroup: /system.slice/stock-bot.service
             ├─1756284 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1756285 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1756316 /root/stock-bot/venv/bin/python -u main.py
             ├─1756339 /root/stock-bot/venv/bin/python heartbeat_keeper.py
             └─1757855 /root/stock-bot/venv/bin/python -u dashboard.py

Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] DEBUG WORKER: After market check, market_open=False, about to check if block...
Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] DEBUG: Market is CLOSED - skipping trading
Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] /root/stock-bot/main.py:12672: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot]   day = datetime.utcnow().strftime("%Y-%m-%d")
Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] /root/stock-bot/main.py:12809: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot]   "last_heartbeat_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] /root/stock-bot/main.py:12813: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot]   "last_attempt_dt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] DEBUG: Heartbeat file OK: state/bot_heartbeat.json (iter 80)
Mar 30 20:29:47 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1756285]: [trading-bot] DEBUG: Worker sleeping for 59.9s (target=60.0s, elapsed=0.1s)

```

## Git commit (droplet repo)

- `HEAD` = `5a3eae7a7d2806309979d3e90e4b44ce8e26520d` (exit 0)

## Timestamps (evidence)

- UTC (date -u): `2026-03-30T20:30:01Z`
- America/New_York: `2026-03-30 16:30:01 EDT`
