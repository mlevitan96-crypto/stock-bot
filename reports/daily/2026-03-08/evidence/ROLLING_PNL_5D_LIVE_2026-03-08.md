# 5D Rolling PnL — Live on Droplet 2026-03-08

## Completed

1. **Pushed to GitHub:** `4cc4f16..4a17d98` main → origin/main
2. **Deployed via DropletClient:** git fetch/reset, pytest spine, kill stale dashboard, `sudo systemctl restart stock-bot`, uw_flow_daemon restart, dashboard listening on :5000
3. **Cron added on droplet:** `*/10 * * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/performance/update_rolling_pnl_5d.py >> logs/rolling_pnl_5d.log 2>&1`
4. **Script run twice on droplet:** `reports/state/rolling_pnl_5d.jsonl` has 2 lines (idempotence OK)
5. **Dashboard:** Health 200; `/api/rolling_pnl_5d` returns (auth required — use dashboard login)

## Restarts performed

- **stock-bot** (systemd): restarted by deploy — supervisor + dashboard + main.py + uw_flow_daemon children
- **uw-flow-daemon.service:** restarted by deploy
- Stale `dashboard.py` processes killed before restart so only one dashboard binds to port 5000

## User

- **Hard-refresh browser** (Ctrl+Shift+R or Ctrl+F5) when opening http://104.236.102.57:5000/
- Open **Executive Summary** → select **5D (rolling)** to see the 5-day performance line (or “No rolling 5d data yet” until more points exist).
