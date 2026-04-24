# ALPACA_250_THRESHOLD_CONTEXT

- **ET date (folder):** `2026-04-01`
- **git HEAD:** `40c361d9b39e08cddb75886de1e4386c1edf7984`
- **UTC now:** `2026-04-01 16:48:16 UTC`

## systemctl status stock-bot

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Tue 2026-03-31 21:11:35 UTC; 19h ago
   Main PID: 1807948 (systemd_start.s)
      Tasks: 35 (limit: 9483)
     Memory: 874.8M (peak: 915.8M)
        CPU: 1h 6min 4.455s
     CGroup: /system.slice/stock-bot.service
             ├─1807948 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1807950 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1807960 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1808026 /root/stock-bot/venv/bin/python -u main.py
             └─1808043 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot]   now = datetime.utcnow()
Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] /root/stock-bot/main.py:6797: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot]   entry_ts = datetime.utcnow()  # Unknown entry time
Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG EXITS: INTC using Alpaca P&L: 0.0066% (entry=$48.54, current=$48.22)
Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] /root/stock-bot/main.py:7455: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot]   entry_ts_info = info.get("ts", datetime.utcnow())
Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] /root/stock-bot/main.py:7458: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot]   position_age_sec = (datetime.utcnow() - entry_ts_info).total_seconds()
Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG EXITS: XOM using Alpaca P&L: 0.0017% (entry=$161.18, current=$160.91)
Apr 01 16:48:16 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1807950]: [trading-bot] DEBUG EXITS: HOOD using Alpaca P&L: 0.0011% (entry=$70.30, current=$70.38)

```
