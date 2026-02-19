# Systemd Audit (Droplet)

## Architecture note

This codebase does **not** use separate systemd units for predictive_engine, ensemble_predictor, signal_resolver, or feature_builder. Production runs:

- **One systemd service:** `trading-bot.service` or `stockbot.service` (see SYSTEMD_BEST_PRACTICES.md, README.md)
- **Entry point:** `deploy_supervisor.py` (or `systemd_start.sh` → deploy_supervisor.py)
- **Child processes:** dashboard (Flask :5000), uw-daemon (uw_flow_daemon.py), trading-bot (main.py)

Optional separate units if installed:

- `deploy/stock-bot-dashboard.service` — dashboard only
- `deploy/systemd/uw-flow-daemon.service` — UW daemon only

## Checklist (run on droplet)

1. **List units:** `systemctl list-units --all | grep -E 'stock|trading|uw|dashboard'`
2. **Status:** For each unit: `systemctl status <unit>`
3. **Active:** `systemctl is-active trading-bot.service` (or stockbot.service)
4. **Journal:** `journalctl -u trading-bot.service -n 50 --no-pager`
5. **Restart loops:** `journalctl -u trading-bot.service --since "1 hour ago" | grep -c "Started\|Stopped"` (high count = restart loop)
6. **Import errors:** `journalctl -u trading-bot.service -n 200 | grep -i "Error\|ImportError\|ModuleNotFoundError"`
7. **NaN/Inf:** `journalctl -u trading-bot.service -n 500 | grep -i "nan\|inf\|warning"`

## Expected state

- **active (running)** for the main bot service
- No repeated Start/Stop in last hour
- No ImportError in recent logs
- uw-daemon (or supervisor’s uw process) writing to data/uw_flow_cache.json

*Raw output from droplet run stored in this directory when scripts/run_scoring_integrity_audit_on_droplet.py is executed.*
