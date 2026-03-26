# Pre-deploy snapshot

**PROJ:** `/root/stock-bot`  **UTC:** 2026-03-18T20:40:24Z

## git HEAD
```
4231e63b811610b3b5676206a631488dbe9aaf45
4231e63 Daily Alpha Audit 2026-03-18 - MEMORY_BANK.md Specialist Tier Monitoring
```

## systemctl stock-bot
```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Wed 2026-03-18 06:35:54 UTC; 14h ago
   Main PID: 1194628 (systemd_start.s)
      Tasks: 35 (limit: 9483)
     Memory: 2.0G (peak: 3.0G)
        CPU: 4h 28min 25.166s
     CGroup: /system.slice/stock-bot.service
             ├─1194628 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1194630 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1194770 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1195106 /root/stock-bot/venv/bin/python -u main.py
             └─1195125 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Mar 18 20:40:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] ERROR EXITS: Failed to close JPM (attempt 3/3): close_position_api_once returned None
Mar 18 20:40:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] ERROR EXITS: All 3 attempts to close JPM failed
Mar 18 20:40:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] WARNING EXITS: JPM could not be verified as closed after 3 attempts - keeping in tracking for retry
Mar 18 20:40:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] DEBUG EXITS: Closing XOM (decision_px=157.91, entry=158.68, hold=158.1min)
Mar 18 20:40:19 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 1/3): close_position_api_once returned None
Mar 18 20:40:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 2/3): close_position_api_once returned None
Mar 18 20:40:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] ERROR EXITS: Failed to close XOM (attempt 3/3): close_position_api_once returned None
Mar 18 20:40:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] ERROR EXITS: All 3 attempts to close XOM failed
Mar 18 20:40:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] WARNING EXITS: XOM could not be verified as closed after 3 attempts - keeping in tracking for retry
Mar 18 20:40:28 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1194630]: [trading-bot] DEBUG EXITS: Closing UNH (decision_px=283.22, entry=286.86, hold=157.5min)
```

## Bot logs (tail)
```
```

## disk / inode
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda1       154G   49G  106G  32% /
Filesystem       Inodes  IUsed    IFree IUse% Mounted on
/dev/vda1      20840448 266022 20574426    2% /
```
