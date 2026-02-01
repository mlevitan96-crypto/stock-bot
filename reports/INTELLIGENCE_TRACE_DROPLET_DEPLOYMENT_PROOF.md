# Intelligence Trace Droplet Deployment Proof

**HEAD:**
2ae6b05226e3798f6eb7e532679facdeace9fd23

## systemctl status
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf
     Active: active (running) since Tue 2026-01-27 22:56:37 UTC; 342ms ago
   Main PID: 1868729 (systemd_start.s)
      Tasks: 2 (limit: 2318)
     Memory: 12.8M (peak: 13.0M)
        CPU: 213ms
     CGroup: /system.slice/stock-bot.service
             ├─1868729 /bin/bash /root/stock-bot/systemd_start.sh
             └─1868731 /root/stock-bot/venv/bin/python deploy_supervisor.py

Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] Time: 2026-01-27 22:56:37 UTC
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] ============================================================
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] Creating required directories...
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Created/verified: logs/
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Created/verified: state/
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Created/verified: data/
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Created/verified: config/

## journalctl -n 50
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [trading-bot] DEBUG: Worker loop EXITING (stop_evt was set)
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [SUPERVISOR] [2026-01-27 22:56:34 UTC] Shutdown signal received
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [SUPERVISOR] [2026-01-27 22:56:34 UTC] Terminating dashboard...
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [SUPERVISOR] [2026-01-27 22:56:34 UTC] Terminating uw-daemon...
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [SUPERVISOR] [2026-01-27 22:56:34 UTC] Terminating trading-bot...
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [SUPERVISOR] [2026-01-27 22:56:34 UTC] Terminating heartbeat-keeper...
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [UW-DAEMON] Signal handler called: signal 15
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [DEBUG] uw_flow_daemon.py:_signal_handler: Signal received {"signum": 15, "signal_name": "SIGTERM", "already_shutting_down": false, "running_before": true, "loop_entered": true}
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon]
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [UW-DAEMON] Received signal 15, shutting down...
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [DEBUG] uw_flow_daemon.py:_signal_handler: Signal handled - running set to False {"running": false, "shutting_down": true}
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 17:56) - will use longer polling intervals
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "calendar:BAC", "base_endpoint": "calendar", "force_first": false, "last": 1769279851.4898813, "interval": 604800, "time_since_last": 274743.38579440117}
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 17:56) - will use longer polling intervals
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "calendar:BAC", "time_remaining": 330056.61420559883}
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 17:56) - will use longer polling intervals
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "institutional_ownership:BAC", "base_endpoint": "institutional_ownership", "force_first": false, "last": 1769540959.9127245, "interval": 86400, "time_since_last": 13634.964705228806}
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 17:56) - will use longer polling intervals
Jan 27 22:56:34 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "institutional_ownership:BAC", "time_remaining": 72765.0352947712}
Jan 27 22:56:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [UW-DAEMON] Completed first poll cycle - all endpoints attempted
Jan 27 22:56:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [uw-daemon] [DEBUG] uw_flow_daemon.py:run: Normal sleep {"cycle": 1}
Jan 27 22:56:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [SUPERVISOR] [2026-01-27 22:56:36 UTC] Killing uw-daemon...
Jan 27 22:56:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [SUPERVISOR] [2026-01-27 22:56:36 UTC] Killing trading-bot...
Jan 27 22:56:36 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868521]: [SUPERVISOR] [2026-01-27 22:56:36 UTC] All services stopped
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot.service: Deactivated successfully.
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Stopped stock-bot.service - Algorithmic Trading Bot.
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: stock-bot.service: Consumed 28.940s CPU time, 12.4M memory peak, 0B memory swap peak.
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd[1]: Started stock-bot.service - Algorithmic Trading Bot.
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: /root/stock-bot/deploy_supervisor.py:140: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] WARNING: .env file (/root/stock-bot/.env) was modified after deploy_supervisor.py
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] This may indicate an accidental overwrite. Verify credentials are correct.
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] Droplet identity verified: 104.236.102.57
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] ============================================================
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] DEPLOYMENT SUPERVISOR V4 STARTING
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] Python: /root/stock-bot/venv/bin/python
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] Working dir: /root/stock-bot
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] Time: 2026-01-27 22:56:37 UTC
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] ============================================================
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] Creating required directories...
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Created/verified: logs/
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Created/verified: state/
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Created/verified: data/
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Created/verified: config/
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Created/verified: state/heartbeats/
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC] Running startup cleanup...
Jan 27 22:56:37 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:37 UTC]   Truncating logs/enrichment.log (12.2MB)
Jan 27 22:56:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: /root/stock-bot/deploy_supervisor.py:140: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Jan 27 22:56:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Jan 27 22:56:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1868731]: [SUPERVISOR] [2026-01-27 22:56:38 UTC]   Truncating logs/uw_daemon.log (551.5MB)
