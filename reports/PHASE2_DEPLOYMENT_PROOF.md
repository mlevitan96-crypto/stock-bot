# Phase-2 Deployment Proof

**Generated:** 2026-01-27T01:46:08.356582+00:00

## Pre/Post commit
- Pre: `8425a9ae9698`
- Post: `6447fd67e481`

## Restart
- Time: 2026-01-27T01:44:37.358800+00:00
- systemctl restart rc: 0

## systemctl status (excerpt)
```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf
     Active: active (running) since Tue 2026-01-27 01:44:37 UTC; 1min 30s ago
   Main PID: 1846142 (systemd_start.s)
      Tasks: 20 (limit: 2318)
     Memory: 991.8M (peak: 1.1G)
        CPU: 22.602s
     CGroup: /system.slice/stock-bot.service
             ├─1846142 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1846143 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1846153 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1846165 /root/stock-bot/venv/bin/python uw_flow_daemon.py
             ├─1846167 /root/stock-bot/venv/bin/python -u main.py
             └─1846181 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Jan 27 01:46:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:46) - will use longer polling intervals
Jan 27 01:46:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "insider:PLTR", "time_remaining": 60624.921625852585}
Jan 27 01:46:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:46) - will use longer polling intervals
Jan 27 01:46:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "calendar:PLTR", "base_endpoint": "calendar", "force_first": false, "last": 1769279892.2665958, "interval": 604800, "time_since_last": 198473.89929056168}
Jan 27 01:46:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:46) - will use longer polling intervals
Jan 27 01:46:06 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca sy
```

## journalctl (last 200 lines excerpt)
```
Jan 27 01:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "insider:GS", "time_remaining": 62384.297626018524}
Jan 27 01:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:45) - will use longer polling intervals
Jan 27 01:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "calendar:GS", "base_endpoint": "calendar", "force_first": false, "last": 1769279855.8351545, "interval": 604800, "time_since_last": 198497.3467655182}
Jan 27 01:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:45) - will use longer polling intervals
Jan 27 01:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "calendar:GS", "time_remaining": 406302.6532344818}
Jan 27 01:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:45) - will use longer polling intervals
Jan 27 01:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "institutional_ownership:GS", "base_endpoint": "institutional_ownership", "force_first": false, "last": 1769454550.5914605, "interval": 86400, "time_since_last": 23802.5925989151}
Jan 27 01:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:45) - will use longer polling intervals
Jan 27 01:45:53 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "institutional_ownership:GS", "time_remaining": 62597.4074010849}
Jan 27 01:45:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:45) - will use longer polling intervals
Jan 27 01:45:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:45) - will use longer polling intervals
Jan 27 01:45:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:45) - will use longer polling intervals
Jan 27 01:45:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:45) - will use longer polling intervals
Jan 27 01:45:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 20:45) - will use longer polling intervals
Jan 27 01:45:54 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1846143]: [uw-daemon] [UW-DAEMON] Ma
```