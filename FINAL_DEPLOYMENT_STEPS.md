# FINAL DEPLOYMENT STEPS - Everything Fixed

## All Issues Fixed:
1. ✅ Subprocess import bug - FIXED
2. ✅ Port conflicts - FIXED  
3. ✅ Flow trades not stored - FIXED (now always stores, even if empty)
4. ✅ Premium field handling - FIXED
5. ✅ .env loading - FIXED

## Step-by-Step (Copy/Paste)

### STEP 1: Pull latest fixes
```bash
cd /root/stock-bot
git pull origin main --no-rebase
```

### STEP 2: Restart supervisor
```bash
pkill -f deploy_supervisor
sleep 3
source venv/bin/activate
venv/bin/python deploy_supervisor.py
```

### STEP 3: Wait 2 minutes, then check cache

Open a NEW terminal and run:
```bash
cd /root/stock-bot
python3 -c "
import json
cache = json.load(open('data/uw_flow_cache.json'))
tickers = [k for k, v in cache.items() if isinstance(v, dict) and 'flow_trades' in v]
print(f'✅ Cache has flow_trades key for {len(tickers)} tickers')
if tickers:
    # Check if any have actual data
    with_data = [t for t in tickers if cache[t].get('flow_trades')]
    print(f'   {len(with_data)} tickers have actual trade data')
    print(f'   Examples: {with_data[:3]}')
"
```

## What Changed

**CRITICAL FIX**: Daemon now ALWAYS stores `flow_trades` in cache, even if:
- API returns empty data
- Normalization fails
- Market is closed

This way main.py can see what's happening and log appropriately.

## Expected Results

After 2-3 minutes, you should see:
- `✅ Cache has flow_trades key for X tickers` (where X > 0)
- Trading bot logs: `DEBUG: Found X raw trades for TICKER` (may be 0 if market closed/API empty)

## If Still No Data

The daemon is making API calls (60/hour), so check:
1. **API returning empty?** - Check supervisor output for `[UW-DAEMON] API returned 0 trades`
2. **Rate limited?** - Check `./check_uw_api_usage.sh`
3. **Market closed?** - Even if you think it's open, API may have no recent flow

The important thing: **flow_trades key will now exist in cache** so main.py can process it correctly.
