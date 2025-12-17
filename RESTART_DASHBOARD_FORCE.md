# Force Restart Dashboard to Load New Code

## The Issue
The dashboard process is running but may be using old code. Python processes don't automatically reload when files change.

## Solution: Restart Dashboard Process

```bash
cd /root/stock-bot
# Kill the dashboard process
kill 206717
# Wait for supervisor to restart (or restart manually)
sleep 5
# Verify it restarted
ps aux | grep dashboard | grep -v grep
# Test the endpoint
curl -s http://localhost:5000/health | python3 -m json.tool
```

## If Supervisor Doesn't Auto-Restart

```bash
cd /root/stock-bot
source venv/bin/activate
# Kill old dashboard
pkill -f "python.*dashboard.py"
# Start new one
nohup python3 dashboard.py > logs/dashboard-restart.log 2>&1 &
sleep 3
# Verify
curl -s http://localhost:5000/health | python3 -m json.tool
```

## Verify New Code is Loaded

The new dashboard should have the `/api/health_status` endpoint. Test it:

```bash
curl -s http://localhost:5000/api/health_status | python3 -m json.tool
```

This should return accurate last_order and doctor data.
