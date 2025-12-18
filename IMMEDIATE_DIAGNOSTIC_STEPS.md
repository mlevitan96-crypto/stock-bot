# IMMEDIATE DIAGNOSTIC STEPS

## Problem: "No such file exists" + No Trades

### Step 1: Run Comprehensive Diagnostic

```bash
cd /root/stock-bot
git pull origin main --no-rebase
chmod +x CHECK_DAEMON_AND_TRADES.sh
./CHECK_DAEMON_AND_TRADES.sh
```

This will check:
- Daemon running status
- Cache contents
- API quota/errors
- Missing files
- Trading bot clustering status

### Step 2: Check Supervisor Output

Look at the supervisor terminal for:
- `[UW-DAEMON] ❌ RATE LIMITED (429)` - API limit hit (resets 8PM EST)
- `[UW-DAEMON] Retrieved X flow trades` - API working
- `[UW-DAEMON] API returned 0 trades` - API working but no data
- Any `FileNotFoundError` or `No such file` messages

### Step 3: Verify Endpoint Format

According to UW API docs, the endpoint should be:
- **URL**: `https://api.unusualwhales.com/api/option-trades/flow-alerts`
- **Parameter**: `symbol` (not `ticker`)
- **Current code uses**: `params={"symbol": ticker, "limit": limit}` ✅ CORRECT

### Step 4: Check Rate Limit Status

```bash
cd /root/stock-bot
# Check if we're still rate limited
tail -20 data/uw_flow_cache_log.jsonl | grep -i "rate_limit\|429" | tail -3
```

If you see 429 errors, the limit resets at **8PM EST / 5PM PST**.

### Step 5: Test API Directly (After Limit Resets)

```bash
cd /root/stock-bot
source venv/bin/activate
python3 test_uw_endpoints.py
```

This will test which endpoints are available and show any 404 errors.

## Common Issues

### Issue 1: Rate Limited (429)
**Symptom**: API returns 429, no trades
**Solution**: Wait for 8PM EST reset, daemon will auto-resume

### Issue 2: 404 Errors
**Symptom**: "No such file" or endpoint not found
**Possible causes**:
- Endpoint name changed
- Parameter name wrong (should be `symbol`, not `ticker`)
- Subscription tier doesn't include endpoint

**Fix**: Check API documentation, verify endpoint format

### Issue 3: Empty Cache
**Symptom**: `flow_trades` keys exist but are empty arrays
**Possible causes**:
- Market closed
- No unusual flow activity
- API returning empty (but not erroring)

**Fix**: This is normal - system will process trades when API returns data

### Issue 4: Missing Files
**Symptom**: "No such file exists" error
**Check**:
```bash
ls -la data/uw_flow_cache.json
ls -la data/uw_api_quota.jsonl
ls -la uw_flow_daemon.py
```

If files missing, run:
```bash
mkdir -p data logs state
git pull origin main --no-rebase
```

## Next Steps After Diagnostic

1. **If rate limited**: Wait for 8PM EST, system will auto-resume
2. **If 404 errors**: Check endpoint format matches API docs
3. **If no trades but API working**: Normal - wait for unusual flow activity
4. **If files missing**: Pull latest code and restart supervisor
