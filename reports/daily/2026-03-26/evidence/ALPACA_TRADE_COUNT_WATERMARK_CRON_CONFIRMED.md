# Alpaca Trade-Count Watermark — Cron Continuity Confirmed (SRE)

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

## Impact of watermark implementation

**No cron changes required:**
- Script path unchanged
- Environment requirements unchanged
- Log location unchanged
- Schedule unchanged

**Behavior change (automatic):**
- First run will initialize watermark and exit silently
- Subsequent runs will use watermark for filtering
- Only NEW exits after watermark will be counted

---

## First-run behavior (via cron)

**When cron executes for the first time after watermark implementation:**
1. Script runs
2. If `counting_started_utc` missing:
   - Sets watermark to current UTC
   - Persists state
   - Exits without notifications
   - Logs: `"Initialized counting watermark: <timestamp>"` and `"Exiting without notifications (first-run initialization)"`
3. Next cron run (10 minutes later):
   - Watermark present
   - Counts exits where `exit_ts >= counting_started_utc`
   - Sends notifications if thresholds reached

---

## Monitoring

**Log location:** `logs/notify_milestones.log`

**Expected behavior:**
- First run: Watermark initialization message (no notifications)
- Subsequent runs: Trade count and threshold checks (notifications if reached)
- All runs: Uses `counting_started_utc` for filtering (not `activated_utc`)

---

*SRE — cron continuity confirmed; no changes required; watermark logic active on next run.*
