# Deployment Guide: Composite Close Reason Feature

## Pre-Deployment Checklist

✅ **Code Changes Complete**
- `build_composite_close_reason()` function added
- `evaluate_exits()` updated to collect exit signals
- All exit paths updated to use composite close reasons
- Displacement exit updated

✅ **Files Modified**
- `main.py` - Core exit logic with composite close reasons
- `COMPOSITE_CLOSE_REASON_FIX.md` - Documentation

## Deployment Steps

### Option 1: Quick Deploy (Recommended)

**On your local machine (where you have git access):**

```bash
# 1. Commit the changes
git add main.py COMPOSITE_CLOSE_REASON_FIX.md DEPLOY_COMPOSITE_CLOSE_REASON.md
git commit -m "Add composite close reasons for better exit tracking and learning"
git push origin main
```

**On your droplet:**

```bash
cd /root/stock-bot

# 2. Pull latest code
git pull origin main --no-rebase

# 3. Restart supervisor (will restart all services)
pkill -f deploy_supervisor
sleep 2
source venv/bin/activate
venv/bin/python deploy_supervisor.py
```

### Option 2: Using FIX_NOW.sh Script

**On your droplet:**

```bash
cd /root/stock-bot
chmod +x FIX_NOW.sh
./FIX_NOW.sh
```

This script will:
1. Resolve any git conflicts
2. Pull latest code
3. Restart supervisor

### Option 3: Manual Step-by-Step (If you want more control)

**On your droplet:**

```bash
cd /root/stock-bot

# 1. Check current status
ps aux | grep deploy_supervisor
ps aux | grep "python.*main.py"

# 2. Pull latest code
git pull origin main --no-rebase

# 3. Verify changes were pulled
git log -1 --oneline
# Should show: "Add composite close reasons..."

# 4. Stop supervisor (gracefully)
pkill -f deploy_supervisor
sleep 3

# 5. Verify services stopped
ps aux | grep "python.*main.py" | grep -v grep
# Should show nothing

# 6. Activate venv and start supervisor
source venv/bin/activate
venv/bin/python deploy_supervisor.py
```

## Verification Steps

After deployment, verify the changes are working:

### 1. Check Supervisor Started
```bash
ps aux | grep deploy_supervisor | grep -v grep
# Should show the supervisor process
```

### 2. Check Services Running
```bash
ps aux | grep -E "(dashboard|uw-daemon|trading-bot|heartbeat)" | grep -v grep
# Should show all services
```

### 3. Check Logs for Composite Close Reasons
```bash
# Watch for new exit events with composite close reasons
tail -f logs/*.log | grep -i "close_reason\|exit.*reason"

# Or check recent attribution logs
tail -20 logs/attribution.jsonl | python3 -m json.tool | grep close_reason
```

### 4. Test Executive Summary
```bash
# Generate executive summary to verify fields are populated
python3 executive_summary_generator.py | python3 -m json.tool | grep -A 5 "close_reason"
```

### 5. Monitor Dashboard
- Open dashboard at `http://your-server:5000`
- Check Executive Summary tab
- Verify `hold_minutes`, `entry_score`, and `close_reason` fields are populated
- Close reasons should show composite format like: `"time_exit(72h)+signal_decay(0.65)"`

## Expected Behavior After Deployment

### New Exits Will Show:
- **Composite close reasons** instead of simple strings
- **Multiple signals** when applicable (e.g., `"time_exit(72h)+signal_decay(0.65)+flow_reversal"`)
- **All fields populated**: `hold_minutes`, `entry_score`, `close_reason`

### Example Close Reasons:
- `"time_exit(72h)"` - Simple time-based exit
- `"trail_stop(-2.5%)+signal_decay(0.70)"` - Trail stop with signal decay
- `"profit_target(5%)+signal_decay(0.80)"` - Profit target hit
- `"time_exit(72h)+signal_decay(0.65)+flow_reversal"` - Multiple signals

## Rollback Plan (If Needed)

If something goes wrong:

```bash
cd /root/stock-bot

# 1. Stop supervisor
pkill -f deploy_supervisor
sleep 2

# 2. Revert to previous commit
git log --oneline -5  # Find the commit before this one
git reset --hard <previous-commit-hash>

# 3. Restart supervisor
source venv/bin/activate
venv/bin/python deploy_supervisor.py
```

## Troubleshooting

### Issue: Git conflicts
```bash
# Resolve conflicts
git checkout --theirs <file>
git pull origin main --no-rebase
```

### Issue: Supervisor won't start
```bash
# Check for port conflicts
lsof -i :5000
lsof -i :8081

# Kill any processes on those ports
kill -9 <PID>

# Try again
venv/bin/python deploy_supervisor.py
```

### Issue: Services not starting
```bash
# Check supervisor logs
tail -50 logs/supervisor.jsonl

# Check individual service logs
tail -50 logs/trading-bot.log
tail -50 logs/uw-daemon.log
```

### Issue: Missing fields in executive summary
- **Old trades**: Will show 0/unknown (expected - they were logged before this feature)
- **New trades**: Should show populated fields
- **Verify**: Check `logs/attribution.jsonl` for recent exits - should have composite close reasons

## Post-Deployment Monitoring

Monitor for the first few hours:
1. **Check exit logs** - Should see composite close reasons
2. **Check executive summary** - Fields should populate for new trades
3. **Check for errors** - No new exceptions related to exit logic
4. **Verify trading continues** - Bot should continue trading normally

## Success Criteria

✅ Supervisor starts without errors
✅ All services running (dashboard, uw-daemon, trading-bot, heartbeat-keeper)
✅ New exits show composite close reasons in logs
✅ Executive summary shows populated fields for new trades
✅ No new exceptions in logs
✅ Trading continues normally

## Notes

- **Zero downtime**: The supervisor will restart services gracefully
- **Old trades**: Will still show 0/unknown (this is expected)
- **New trades**: Will have full composite close reasons
- **Learning system**: Will now have better exit signal data for analysis
