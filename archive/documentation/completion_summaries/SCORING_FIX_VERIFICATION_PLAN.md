# Scoring Fix Verification Plan

## Current Status: ⚠️ NOT CONFIRMED WORKING

### Test Results (Just Now)
- 861 signals in last 30 minutes
- ALL have score=0.00
- ALL have source=unknown
- **Fix is NOT working yet**

## Why Fix May Not Be Working

1. **Service may not have restarted properly**
2. **New signals haven't been generated yet** (fix only affects NEW clusters)
3. **Composite scoring may not be running** (use_composite=False?)
4. **Fix logic may have an issue**

## Verification Steps

### Step 1: Check Service Status
```bash
sudo systemctl status trading-bot.service
```

### Step 2: Check Recent Logs
```bash
journalctl -u trading-bot.service --since "10 minutes ago" | grep -E "composite|score|DEBUG.*Composite"
```

### Step 3: Wait for New Signals
- Fix only affects NEW signals generated AFTER deployment
- Old signals in logs will still show 0.00
- Need to wait 2-5 minutes for new cycle

### Step 4: Re-test
```bash
python3 check_recent_signal_scores.py
```
- Check signals from LAST 5 MINUTES only
- Should see scores > 0.0 and source="composite_v3"

## Monitoring Fixes Required

### Fix 1: Monitoring Guard (DONE)
- Now checks ALL clusters, not just composite ones
- Detects when ALL scores are 0.00
- Detects when ALL sources are "unknown"

### Fix 2: Dashboard Health (TODO)
- Add signal quality checks to SRE monitoring
- Show score distribution in dashboard
- Alert on score quality issues

## Next Actions

1. ✅ Fix monitoring guard (DONE)
2. ⏳ Wait for new signals and re-test
3. ⏳ Add dashboard health checks
4. ⏳ Verify fix is actually working

---

**Status:** Monitoring fixes applied, but original fix needs verification
