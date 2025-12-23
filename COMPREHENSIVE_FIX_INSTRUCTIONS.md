# Comprehensive Fix Instructions

## Issues Found

1. **Dashboard heartbeat reading bug**: Dashboard was checking `last_heartbeat` instead of `last_heartbeat_ts` (the actual field name)
2. **Last order reading bug**: Dashboard only checked `data/live_orders.jsonl`, but orders might be in `logs/orders.jsonl` or `logs/trading.jsonl`
3. **Self-healing may not be triggering**: Need to verify heartbeat freshness and self-healing mechanisms

## Fixes Applied

### 1. Dashboard Heartbeat Fix
- Changed to check `last_heartbeat_ts` first (the actual field used by `main.py`)
- Falls back to other timestamp fields if needed

### 2. Dashboard Last Order Fix  
- Now checks multiple files: `data/live_orders.jsonl`, `logs/orders.jsonl`, `logs/trading.jsonl`
- Ensures we find the most recent order regardless of which file it's in

## Run on Droplet

```bash
cd ~/stock-bot

# Pull latest fixes
git pull origin main

# Run comprehensive fix script
chmod +x FIX_DASHBOARD_AND_HEALTH.sh
./FIX_DASHBOARD_AND_HEALTH.sh

# Restart dashboard
pkill -f dashboard.py
python3 dashboard.py > logs/dashboard.log 2>&1 &

# Verify fixes
sleep 2
curl -s http://localhost:5000/api/health_status | python3 -m json.tool

# Export fresh logs to verify
./push_to_github_clean.sh \
    state/bot_heartbeat.json \
    logs/run.jsonl \
    logs/orders.jsonl \
    "After dashboard fixes"
```

## What to Check

1. **Dashboard Doctor/Heartbeat**: Should now show correct age (should be < 5 minutes if bot is running)
2. **Dashboard Last Order**: Should show correct time from the most recent order in any log file
3. **Heartbeat File**: Should be fresh (check `state/bot_heartbeat.json` - `last_heartbeat_ts` should be recent)
4. **UW Endpoints**: Check SRE monitoring tab in dashboard to see UW API endpoint health

## If Issues Persist

1. Check if bot is actually running: `ps aux | grep "python.*main.py"`
2. Check heartbeat file directly: `cat state/bot_heartbeat.json | python3 -m json.tool`
3. Check order logs: `tail -20 logs/orders.jsonl | python3 -m json.tool`
4. Check UW cache: `ls -lh data/uw_flow_cache.json` (should be recent)
