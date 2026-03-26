# Telemetry deploy applied

**PROJ:** `/root/stock-bot`  **UTC:** 2026-03-18T20:40:24Z

## Commands
- git fetch: rc=0
- git reset --hard origin/main: rc=0
- systemctl restart stock-bot

## HEAD vs origin/main
```
c9f836a3baeb6851c8ec75b60872c10a816baf43
c9f836a3baeb6851c8ec75b60872c10a816baf43

```
**Mismatch:** False

## stock-bot is-active
```
active

```
**OK:** True

## Recent journal (tail)
```
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC] DEPLOYMENT SUPERVISOR V4 STARTING
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC] Python: /root/stock-bot/venv/bin/python
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC] Working dir: /root/stock-bot
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC] Time: 2026-03-18 20:40:38 UTC
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC] ============================================================
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC] Creating required directories...
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Created/verified: logs/
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Created/verified: state/
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Created/verified: data/
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Created/verified: config/
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Created/verified: state/heartbeats/
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC] Running startup cleanup...
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Truncating logs/exit_attribution.jsonl (17.3MB)
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: /root/stock-bot/deploy_supervisor.py:145: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Truncating logs/score_snapshot.jsonl (12.0MB)
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: /root/stock-bot/deploy_supervisor.py:145: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Truncating logs/signals.jsonl (13.3MB)
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: /root/stock-bot/deploy_supervisor.py:145: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Truncating logs/enrichment.log (11.1MB)
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: /root/stock-bot/deploy_supervisor.py:145: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Mar 18 20:40:38 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:38 UTC]   Truncating logs/uw_daemon.log (523.9MB)
Mar 18 20:40:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: /root/stock-bot/deploy_supervisor.py:145: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 18 20:40:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Mar 18 20:40:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:42 UTC]   Truncating state/portfolio_state.jsonl (26.3MB)
Mar 18 20:40:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: /root/stock-bot/deploy_supervisor.py:145: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
Mar 18 20:40:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]:   return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
Mar 18 20:40:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: [SUPERVISOR] [2026-03-18 20:40:42 UTC]   Truncating state/blocked_trades.jsonl (12.9MB)
Mar 18 20:40:42 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1217913]: /root/stock-bot/deploy_supervisor.py:145: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime
```
**traceback count (heuristic):** 0
