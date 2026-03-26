# Alpaca Telegram Notifier — Scheduling (SRE)

---

## Execution options

### Option A: Alpaca venv scheduler / loop

If the Alpaca paper engine has a **main loop** or **periodic task runner**, add:

```python
# In main loop (every N minutes during market hours)
if market_open:
    subprocess.run(
        ["python3", "scripts/notify_alpaca_trade_milestones.py"],
        cwd="/root/stock-bot",
        env=os.environ,
        timeout=60,
    )
```

**Pros:** Uses same venv / env vars; no cron dependency.  
**Cons:** Requires code change in main engine.

---

### Option B: Lightweight cron (recommended)

**Cron entry** (runs every **5–10 minutes** during market hours):

```bash
# Alpaca trade milestone notifications (every 10 min, market hours only)
*/10 13-21 * * 1-5 cd /root/stock-bot && source /root/.alpaca_env && PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py >> logs/notify_milestones.log 2>&1
```

**Schedule:** Mon–Fri, 13:00–21:00 UTC (covers US market hours 09:00–17:00 ET).

**Install:**
```bash
# On droplet
crontab -e
# Add line above
```

---

### Option C: systemd timer (if preferred)

Create `/etc/systemd/system/alpaca-trade-notifier.timer` and `.service` (not shown; standard systemd pattern).

---

## Telegram credentials

**Source:** `/root/.alpaca_env` (per MEMORY_BANK) or Alpaca venv activation.

**Verify:**
```bash
source /root/.alpaca_env
python3 -c "import os; print('TOKEN' if os.getenv('TELEGRAM_BOT_TOKEN') else 'MISSING')"
```

---

## Recommended: Option B (cron)

- **No code changes** to main engine.
- **Simple** to install / remove.
- **Aligned** with existing Alpaca cron patterns (EOD, etc.).

**Install command (on droplet):**
```bash
(crontab -l 2>/dev/null; echo "*/10 13-21 * * 1-5 cd /root/stock-bot && source /root/.alpaca_env && PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py >> logs/notify_milestones.log 2>&1") | crontab -
```

---

*SRE — scheduling via cron recommended; no systemd dependency.*
