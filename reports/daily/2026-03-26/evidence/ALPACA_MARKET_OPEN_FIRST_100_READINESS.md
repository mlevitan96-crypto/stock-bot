# Alpaca: Market open & first 100-trade CSA readiness

**Purpose:** Checklist so the first batch of 100 trade events triggers CSA and everything is live when the market opens.

---

## Confirmed

- **Telegram:** Operator confirmed receipt of E2E audit message. Governance notifications (venv/.alpaca_env → .env, E2E runner) are working.
- **E2E governance:** Full chain (Tier 1→2→3→convergence→promotion gate→heartbeat) ran on droplet with real data; artifacts and CSA/SRE reviews in place.

---

## Before market open (on droplet)

Run **once** so the next 100 trade events trigger the first CSA:

```bash
cd /root/stock-bot && source /root/.alpaca_env 2>/dev/null; source venv/bin/activate && python scripts/reset_csa_trade_count_for_today.py
```

This will:

1. Set `reports/state/TRADE_CSA_STATE.json` to zeros (`total_trade_events`, `last_csa_trade_count`).
2. Clear `reports/state/trade_events.jsonl` so the next 100 events count toward the first CSA.
3. Regenerate `reports/board/PROFITABILITY_COCKPIT.md` (dashboard shows “Trades until next CSA: 100”).

---

## What’s live

| Item | Where | Notes |
|------|--------|------|
| **stock-bot.service** | Droplet | deploy_supervisor → dashboard, main.py, uw_flow_daemon. Confirm: `sudo systemctl status stock-bot`. |
| **CSA 100-trade trigger** | Trading engine + optional backup cron | Engine calls `record_trade_event()` → increments state; every 100 events runs CSA. Backup: `scripts/csa_backup_trigger_every_100.py` (cron optional). |
| **Dashboard** | http://droplet:5000 | Profitability & Learning tab reads TRADE_CSA_STATE + CSA_VERDICT_LATEST; after reset shows X/100 → next CSA at 100. |
| **Governance chain** | Manual or scheduled | Tier 1/2/3, convergence, gate, heartbeat, Telegram — run via E2E script or individual scripts with --telegram. |

---

## Quick sanity check (on droplet)

```bash
# Service up
sudo systemctl is-active stock-bot

# State ready for first 100 (after reset)
cat reports/state/TRADE_CSA_STATE.json   # total_trade_events: 0, last_csa_trade_count: 0

# Cockpit shows next at 100
grep -i "next CSA\|trades until" reports/board/PROFITABILITY_COCKPIT.md || true
```

---

## Summary

- **Telegram:** Confirmed received.
- **First 100:** Reset already run on droplet; `total_trade_events: 0`, next CSA at 100.
- **Live:** Services, state paths, and dashboard as above.
- **Droplet confirmed active:** See `reports/audit/ALPACA_DROPLET_ACTIVE_AND_READY_CONFIRMED.md` (service active, 4 processes, dashboard 200 on profitability_learning, CSA state 0/100). **Ready to go at market open.**
