# Alpaca dashboard — systemd service discovery

**Timestamp:** 20260326_1815Z  
**Host:** SSH `alpaca` → `ubuntu-s-1vcpu-2gb-nyc3-01-alpaca`

## Commands

```bash
systemctl list-units --type=service --all | egrep -i "dash|dashboard|stock-bot"
systemctl list-unit-files | egrep -i "dash|dashboard|stock-bot"
```

## Output (excerpt)

**list-units (service):**

- `stock-bot-dashboard-audit.service` — failed (nightly audit; separate)
- **`stock-bot-dashboard.service`** — **active (running)** — `STOCK-BOT Dashboard (Flask :5000)`
- `stock-bot.service` — active (trading bot)

**list-unit-files:**

- `stock-bot-dashboard.service` — enabled
- `stock-bot-dashboard-audit.service` / `.timer` — listed

## Selected dashboard unit

**`stock-bot-dashboard.service`** — serves Flask dashboard on port 5000.
