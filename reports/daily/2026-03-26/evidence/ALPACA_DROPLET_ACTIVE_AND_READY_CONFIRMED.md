# Droplet active and ready for market open — CONFIRMED

**Checked:** 2026-03-16 (via DropletClient from local).  
**Verdict:** All systems active and ready.

---

## Service

| Check | Result |
|-------|--------|
| **stock-bot.service** | `active` |
| **Processes** | 4 (deploy_supervisor, dashboard, main.py) |
| **Branch** | main |
| **Disk** | 31% |
| **Memory** | 2.4Gi/7.8Gi |
| **Uptime** | Up 2+ weeks |

---

## Mode (masked)

- **TRADING_MODE** and **ALPACA_BASE_URL** present in `.env` (values not logged).  
- Per MEMORY_BANK: paper-only; engine refuses entries if not Alpaca paper endpoint.

---

## First 100-trade CSA

- **TRADE_CSA_STATE.json:** `total_trade_events: 0`, `last_csa_trade_count: 0`.
- **trades_until_next:** 100 (first batch).
- Reset was run; next 100 events will trigger first CSA.

---

## Dashboard

- **api/ping:** HTTP 401 (Basic Auth required — expected).
- **api/profitability_learning:** HTTP 200.
- **health:** HTTP 401 (auth required).
- Dashboard is up and serving; Profitability & Learning tab will show 0/100 → next CSA at 100.

---

## Processes (confirmed)

- `deploy_supervisor.py` (venv)
- `dashboard.py` (venv)
- `main.py` (venv)

---

## Summary

- **Service:** Active.  
- **Trading engine:** Running (main.py).  
- **Dashboard:** Up; key endpoints respond.  
- **CSA:** Reset for first 100; state ready.  
- **Config:** TRADING_MODE and Alpaca URL set (masked).

**Ready to go at market open.**
