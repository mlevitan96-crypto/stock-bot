# IMMEDIATE FIX - Run These Commands Now

## Step 1: Pull Latest Code (with all fixes)

```bash
cd /root/stock-bot
git pull origin main --no-rebase
```

## Step 2: Restart Supervisor

```bash
pkill -f deploy_supervisor
sleep 2
source venv/bin/activate
venv/bin/python deploy_supervisor.py
```

## Step 3: Watch the Logs (in a new terminal or screen)

The new logging will show exactly what's happening. Look for:

```bash
# Watch for submit_entry calls
tail -f /dev/stdout | grep -E "submit_entry|EXCEPTION|Order SUBMITTED|Order IMMEDIATELY FILLED"
```

OR just watch the supervisor output directly - it will show all DEBUG messages.

## Step 4: Check What's Happening

After 1-2 minutes, check the logs for:

1. **Are submit_entry calls happening?**
   - Look for: `DEBUG SYMBOL: About to call submit_entry`
   - If you DON'T see this, there's an exception before submit_entry

2. **Are there exceptions?**
   - Look for: `DEBUG SYMBOL: EXCEPTION in submit_entry`
   - This will show the exact error

3. **What status is submit_entry returning?**
   - Look for: `DEBUG SYMBOL: submit_entry completed - entry_status=...`
   - This shows if orders are being submitted successfully

## Step 5: If Still No Trades

Run this diagnostic command:

```bash
cd /root/stock-bot
python3 -c "
import json
# Check if there are any recent order logs
import os
log_file = 'logs/order.jsonl'
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        lines = f.readlines()
        print(f'Recent orders (last 10):')
        for line in lines[-10:]:
            try:
                data = json.loads(line)
                print(f\"  {data.get('symbol', '?')}: {data.get('error', 'OK')} - {data.get('status', 'N/A')}\")
            except:
                pass
else:
    print('No order log file found')
"
```

## Common Issues & Fixes

### Issue 1: "EXCEPTION in submit_entry"
- **Check**: What's the error message?
- **Common causes**: 
  - Alpaca API connection issue
  - Invalid price data
  - Account restrictions

### Issue 2: "entry_status=error" or "entry_status=spread_too_wide"
- **Check**: What's the specific error?
- **Fix**: The error message will tell you what's blocking

### Issue 3: No submit_entry logs at all
- **Check**: Look for exceptions in execution router setup
- **Fix**: Check if get_nbbo is failing

## Quick Status Check

```bash
cd /root/stock-bot

# Check if supervisor is running
ps aux | grep deploy_supervisor | grep -v grep

# Check recent trading bot output
# (Look at the supervisor terminal output - it shows all DEBUG messages)

# Check if orders are being logged
tail -20 logs/order.jsonl 2>/dev/null | tail -5 || echo "No order log yet"
```

## What the New Logs Will Show

After deploying, you should see one of these patterns:

**Pattern 1: Orders Being Submitted**
```
DEBUG AMD: About to call submit_entry with qty=5, side=buy, regime=mixed
DEBUG AMD: submit_entry completed - res=True, order_type=limit, entry_status=submitted_unfilled, filled_qty=0
DEBUG AMD: Order SUBMITTED (not yet filled) - reconciliation will track fill
```

**Pattern 2: Exception Occurring**
```
DEBUG AMD: About to call submit_entry with qty=5, side=buy, regime=mixed
DEBUG AMD: EXCEPTION in submit_entry: [error message]
DEBUG AMD: Traceback: [full traceback]
```

**Pattern 3: Price Data Issue**
```
DEBUG AMD: WARNING - get_nbbo returned invalid bid/ask: bid=0, ask=0
DEBUG AMD: Using fallback bid/ask from last trade: bid=X, ask=Y
```

## Next Steps Based on Logs

1. **If you see exceptions**: Share the error message and I'll fix it
2. **If you see "submitted_unfilled"**: Orders are being submitted - reconciliation will pick them up
3. **If you see "error" status**: Check the specific error reason
4. **If no logs at all**: There's an exception before submit_entry - check execution router logs

Run these commands and share the output - I'll fix whatever is blocking trades.
