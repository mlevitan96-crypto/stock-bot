# PROFIT_V2_BASELINE_CONTEXT

Evidence bundle: `_PROFIT_V2_DROPLET_RAW.json` (same directory). Session anchor (ET): **2026-04-01**.

## Git

- `git rev-parse HEAD` on droplet: **`e03f25ef06483e6e0157228d6821613aeac4085f`**

## systemd: `stock-bot`

- **FragmentPath:** `/etc/systemd/system/stock-bot.service`
- **ExecStart:** `/root/stock-bot/systemd_start.sh` (see `systemctl show` in raw JSON)
- **Environment (inline):** `EXPECTANCY_GATE_TRUTH_LOG=1`, `SIGNAL_SCORE_BREAKDOWN_LOG=1`, `MIN_EXEC_SCORE=2.7`, `TRUTH_ROUTER_ENABLED=1`, `TRUTH_ROUTER_MIRROR_LEGACY=1`, `STOCKBOT_TRUTH_ROOT=/var/lib/stock-bot/truth`
- **Active state (capture time):** `active (running)`; **Main PID** `systemd_start.sh` → `deploy_supervisor.py` → workers including **`main.py`** and `dashboard.py` (full `systemctl status` excerpt in raw JSON)

## Process snapshot

- `ps aux | grep stock-bot`: supervisor + `main.py` + dashboard + heartbeat (see `phase0.ps` in raw JSON)

## Journal

- `journalctl -u stock-bot --since '36 hours ago' | tail -n 800` stored under `phase0.journal` in raw JSON (~145 KB text)

## Profit discovery campaign (read-only)

- `PYTHONPATH=. python3 scripts/audit/run_alpaca_profit_discovery_campaign.py --root /root/stock-bot` completed with exit **0**; stdout is the evidence directory path (`/root/stock-bot/reports/daily/2026-04-01/evidence`).
- Pre-existing campaign artifacts in that directory include `ALPACA_PROFIT_INTEL_DATA_INVENTORY.md` and `ALPACA_PROFIT_DISCOVERY_META.json`.

## Live-trading touch surface (this mission)

- No `systemctl restart stock-bot` was performed for Profit V2.
- Subsequent work used **separate** Python processes (bars fetch, replay, uplift scripts) and **SFTP** of audit scripts only.
