# Alpaca Notifier Cron Safety — Confirmed (SRE)

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

## Safety checks

| Check | Result |
|-------|--------|
| **Cron job installed** | **PASS** — entry present |
| **No duplicate entries** | **PASS** — single entry only |
| **Script path unchanged** | **PASS** — still `scripts/notify_alpaca_trade_milestones.py` |
| **Environment sourcing** | **PASS** — still uses `source /root/.alpaca_env` |
| **Log redirection** | **PASS** — still logs to `logs/notify_milestones.log` |
| **Two-phase guard active** | **PASS** — code enforces no notifications on state mutation |

---

## Safety guarantees

**Two-phase execution:**
- State mutations (watermark init, baseline confirmation) trigger immediate exit
- No threshold evaluation occurs in same run as state mutation
- Prevents premature milestone notifications

**Baseline confirmation:**
- 0-trade baseline confirmed and verified
- `baseline_confirmed = true` prevents duplicate baseline messages
- Only NEW exits after watermark will be counted

**Cron safety:**
- Script path unchanged (no breaking changes)
- Environment requirements unchanged
- Log location unchanged (monitoring intact)

---

## Expected cron behavior

**First run after deployment:**
1. Watermark initialization (if missing)
2. Exit immediately (no notifications)

**Second run:**
1. Baseline confirmation (if `count == 0` and `baseline_confirmed == false`)
2. Exit immediately (no threshold evaluation)

**Subsequent runs:**
1. Count trades where `exit_ts >= counting_started_utc`
2. Evaluate thresholds (100, 500)
3. Send notifications if thresholds reached (once each)

---

## Monitoring

**Log location:** `logs/notify_milestones.log`

**Expected log entries:**
- `"Initialized counting watermark: <timestamp>"` (first run only)
- `"Sent 0-trade baseline confirmation"` (baseline confirmation run)
- `"Current count: <n> (since <watermark>)"` (normal runs)
- `"Sent 100-trade notification (count=<n>)"` (when threshold reached)
- `"Sent 500-trade notification (count=<n>)"` (when threshold reached)

---

*SRE — cron safety confirmed; two-phase guard active; baseline confirmed; ready for hands-off operation.*
