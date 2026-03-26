# Alpaca dashboard — restart + status

**Timestamp:** 20260326_1815Z  
**Unit:** `stock-bot-dashboard.service`

## Commands

```bash
sudo systemctl restart stock-bot-dashboard.service
systemctl status stock-bot-dashboard.service --no-pager
```

## `systemctl status` (capture)

```
● stock-bot-dashboard.service - STOCK-BOT Dashboard (Flask :5000)
     Loaded: loaded (/etc/systemd/system/stock-bot-dashboard.service; enabled; preset: enabled)
     Active: active (running) since Thu 2026-03-26 17:37:40 UTC
   Main PID: 1580958 (python3)
     Memory: 239.0M (peak: 283.6M)
   CGroup: /system.slice/stock-bot-dashboard.service
           └─1580958 /usr/bin/python3 /root/stock-bot/dashboard.py
```

(Service was restarted again after `dashboard.py` scp; final proof run used active PID **1580958** / start **17:37:40 UTC**.)
