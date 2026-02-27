# Baseline snapshot (Phase 0)

Generated: 2026-02-20 21:25 UTC

## DROPLET COMMANDS

```bash
cd /root/stock-bot   # or /root/stock-bot-current
python3 scripts/investigation_baseline_snapshot_on_droplet.py
```

## Service / process status

```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf
     Active: active (running) since Fri 2026-02-20 21:08:18 UTC; 17min ago
   Main PID: 2781778 (systemd_start.s)
      Tasks: 20 (limit: 2318)
     Memory: 1.0G (peak: 1.1G)
        CPU: 1min 50.451s
     CGroup: /system.slice/stock-bot.service
             ├─2781778 /bin/bash /root/stock-bot/systemd_start.sh
             ├─2781779 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─2781797 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─2781810 /root/stock-bot/venv/bin/python uw_flow_daemon.py
             ├─2781814 /root/stock-bot/venv/bin/python -u main.py
             └─2781828 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Feb 20 21:25:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[2781779]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 16:25) - will use longer polling intervals
Feb 20 21:25:49 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[2781779]: [uw-daemon] [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "insider:JNJ", "time_remaining": 80260.64099121094}
Feb 20 21:25:50 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[2781779]: [uw-daemon] [UW-DAEMON] Market is CLOSED (ET time: 16:25) - will use longer polling intervals
Feb 20 21:25:50 ubuntu-s-1vcpu-2gb-nyc
```

## Newest timestamps in key logs

| Log | Newest timestamp |
|-----|------------------|
| ledger | 2026-02-20T18:54:44+00:00 (epoch 1771613684) |
| snapshots | 2026-02-20T21:00:07+00:00 (epoch 1771621207) |
| uw_failure_events | N/A |
| orders | 2026-02-18T17:25:49+00:00 (epoch 1771435549) |
| submit_entry | 2026-02-18T17:23:12+00:00 (epoch 1771435392) |
| submit_order_called | N/A |
| expectancy_gate_truth | N/A |

## Last 24h counts

| Metric | Count |
|--------|-------|
| candidates (ledger events) | 2922 |
| expectancy gate pass (from ledger) | 0 |
| expectancy gate fail (from ledger) | 2922 |
| submit_entry.jsonl lines | 0 |
| SUBMIT_ORDER_CALLED lines | 0 |
| score_snapshot.jsonl lines | 2930 |
| expectancy_gate_truth.jsonl lines | 0 |
| orders.jsonl lines | 0 |