# Step-by-Step Deployment Guide

## CRITICAL: Copy and paste these commands EXACTLY as shown

### Step 1: Navigate to project directory
```bash
cd /root/stock-bot
```

### Step 2: Pull latest fixes
```bash
git pull origin main --no-rebase
```

### Step 3: Check if supervisor is running (and stop it if needed)
```bash
ps aux | grep deploy_supervisor | grep -v grep
```

If you see a process, stop it:
```bash
pkill -f deploy_supervisor
sleep 3
```

### Step 4: Activate virtual environment
```bash
source venv/bin/activate
```

### Step 5: Start supervisor
```bash
venv/bin/python deploy_supervisor.py
```

### Step 6: Wait 30 seconds, then check logs
Open a NEW terminal window (don't close the supervisor one) and run:

```bash
cd /root/stock-bot
tail -f logs/trading-bot-pc.log | grep -E "clustering|flow_trades|normalized|DEBUG"
```

### Step 7: Check if trades are being found
In another terminal:
```bash
cd /root/stock-bot
grep "clustering.*trades" logs/trading-bot-pc.log | tail -10
```

You should see numbers > 0 (e.g., "clustering 15 trades")

### Step 8: Check cache contents
```bash
cd /root/stock-bot
cat data/uw_flow_cache.json | python3 -m json.tool | grep -A 3 "flow_trades" | head -30
```

### Step 9: Check UW daemon logs
```bash
cd /root/stock-bot
tail -50 logs/uw-daemon-pc.log | grep -E "flow_trades|raw trades|Polling"
```

## If Cursor/Input Hangs

If you can't type commands:

1. **Press Ctrl+C** to stop the current command
2. **Press Ctrl+Z** to suspend (if needed)
3. **Type `fg`** to resume in foreground, or `bg` to run in background

## To Run Supervisor in Background

If you want your terminal back:

```bash
# Stop current supervisor (Ctrl+C)
nohup venv/bin/python deploy_supervisor.py > logs/supervisor.out 2>&1 &
```

Then check logs:
```bash
tail -f logs/supervisor.out
```

## Expected Output After Fix

You should see in logs:
- `[UW-DAEMON] Retrieved X flow trades for TICKER`
- `[UW-DAEMON] Stored X raw trades in cache for TICKER`
- `DEBUG: Found X raw trades for TICKER`
- `DEBUG: TICKER: X normalized, Y passed filter`
- `DEBUG: Fetched data, clustering X trades` (where X > 0)


