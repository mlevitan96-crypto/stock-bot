# Troubleshooting Guide

## Issue: Dashboard Port 5000 Already in Use

**Symptom**: `Address already in use` error when starting dashboard

**Cause**: Either:
1. Dashboard proxy is already running on port 5000
2. Another dashboard instance is running

**Fix**:
```bash
# Check what's using port 5000
lsof -i :5000
# or
netstat -tulpn | grep 5000

# If it's the proxy, that's fine - dashboard should use 5001
# If it's a stale dashboard, kill it:
pkill -f dashboard.py

# Restart supervisor
pkill -f deploy_supervisor
venv/bin/python deploy_supervisor.py
```

## Issue: UW Daemon Not Running

**Symptom**: Cache is empty or stale, no daemon logs

**Check**:
```bash
# Check if daemon process exists
ps aux | grep uw_flow_daemon

# Check daemon logs
tail -f logs/uw-daemon-pc.log

# Check if cache is being updated
ls -la data/uw_flow_cache.json
stat data/uw_flow_cache.json  # Shows last modification time
```

**Fix**:
```bash
# If daemon is not running, check secrets
env | grep UW_API_KEY

# If secrets are set, restart supervisor
pkill -f deploy_supervisor
venv/bin/python deploy_supervisor.py
```

## Issue: Heartbeat Keeper Exits Immediately

**Symptom**: `heartbeat-keeper exited immediately with code 0`

**Cause**: Script was running as one-shot instead of daemon

**Fix**: Fixed in latest code - heartbeat_keeper.py now runs continuously when executed directly.

## Issue: v4-Research Exits Immediately

**Symptom**: `v4-research exited immediately with code 0`

**Cause**: This is expected - `v4_orchestrator.py` is a nightly script that runs once and exits.

**Fix**: Already fixed - marked as `one_shot: True` so supervisor won't keep restarting it.

## Issue: Cache Format Mismatch

**Symptom**: Cache exists but main.py shows "0 clusters" or signals are "no_data"

**Cause**: Cache format doesn't match what main.py expects

**Fix**: Fixed in latest code - daemon now writes `sentiment` and `conviction` at top level.

## Issue: No Trades/Clusters

**Symptom**: "clustering 0 trades" in logs

**Possible Causes**:
1. UW daemon not populating cache with flow data
2. Cache format mismatch
3. Market closed or no activity

**Check**:
```bash
# Check cache contents
cat data/uw_flow_cache.json | python3 -m json.tool | head -50

# Check if daemon is making API calls
./check_uw_api_usage.sh

# Check daemon logs for errors
tail -f logs/uw-daemon-pc.log
```

## Quick Health Check Commands

```bash
# 1. Check all processes
ps aux | grep -E "uw_flow_daemon|main.py|dashboard|heartbeat"

# 2. Check ports
netstat -tulpn | grep -E "5000|5001|5002|8081"

# 3. Check cache freshness
ls -la data/uw_flow_cache.json
stat data/uw_flow_cache.json

# 4. Check API usage
./check_uw_api_usage.sh

# 5. Check recent logs
tail -20 logs/*.log

# 6. Check supervisor status
ps aux | grep deploy_supervisor
```



