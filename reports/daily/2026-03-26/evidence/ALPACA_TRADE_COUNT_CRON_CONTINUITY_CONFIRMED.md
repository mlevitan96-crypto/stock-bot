# Alpaca Trade-Count Cron Continuity — Confirmed (SRE)

**Droplet:** `/root/stock-bot`  
**UTC:** 2026-03-20

---

## Cron verification

**Check:**
```bash
crontab -l | grep notify_alpaca_trade_milestones
```

**Result:** Cron entry present and unchanged.

---

## Cron entry

```cron
*/10 13-21 * * 1-5 cd /root/stock-bot && source /root/.alpaca_env && PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py >> logs/notify_milestones.log 2>&1
```

**Schedule:**
- **Frequency:** Every 10 minutes
- **Days:** Monday–Friday (1–5)
- **Hours:** 13:00–21:00 UTC

---

## Continuity checks

| Check | Result |
|-------|--------|
| **Cron job installed** | **PASS** — entry present |
| **No duplicate entries** | **PASS** — single entry only |
| **Script path unchanged** | **PASS** — still `scripts/notify_alpaca_trade_milestones.py` |
| **Environment sourcing** | **PASS** — still uses `source /root/.alpaca_env` |
| **Log redirection** | **PASS** — still logs to `logs/notify_milestones.log` |

---

## Impact of semantic correction

**No cron changes required:**
- Script path unchanged
- Environment requirements unchanged
- Log location unchanged
- Schedule unchanged

**Behavior change (automatic):**
- Next execution will use exit-time semantics (code change)
- State file reset ensures fresh count (no historical overlap)

---

## Monitoring

**Log location:** `logs/notify_milestones.log`

**Expected behavior:**
- Script runs every 10 minutes during market hours
- Counts trades with `exit_ts >= 2026-03-20T00:22:37Z` (exit-time semantics)
- Sends notifications at 100 and 500 thresholds (once each)

---

*SRE — cron continuity confirmed; no changes required; semantic correction active on next run.*
