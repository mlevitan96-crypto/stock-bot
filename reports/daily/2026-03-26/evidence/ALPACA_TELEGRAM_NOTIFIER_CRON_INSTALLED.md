# Alpaca Telegram Notifier — Cron Installed (SRE)

**Droplet:** `/root/stock-bot`  
**Installation method:** `scripts/install_cron_alpaca_notifier.py`

---

## Cron entry

```cron
*/10 13-21 * * 1-5 cd /root/stock-bot && source /root/.alpaca_env && PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py >> logs/notify_milestones.log 2>&1
```

**Schedule:**
- **Frequency:** Every 10 minutes
- **Days:** Monday–Friday (1–5)
- **Hours:** 13:00–21:00 UTC (covers US market hours 09:00–17:00 ET)

---

## Verification

**Check cron entry:**
```bash
crontab -l | grep notify_alpaca_trade_milestones
```

**Expected output:** The cron line above.

**Log location:** `logs/notify_milestones.log` (append-only; check for errors if notifications don't fire).

---

## No duplicate jobs

**Verification:** `scripts/install_cron_alpaca_notifier.py` removes any existing `notify_alpaca_trade_milestones` entries before adding the new one.

**Installation confirmed:** Cron entry verified on droplet (2026-03-20T00:36Z).

---

## Environment

- **Uses Alpaca venv:** `source /root/.alpaca_env` ensures `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are available.
- **No systemd dependency:** Pure cron; no service restart required.

---

*SRE — cron installed; notifications will fire automatically at 100 and 500 trade thresholds.*
