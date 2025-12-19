#!/bin/bash
# Restart dashboard and bot to pick up code changes

cd ~/stock-bot

echo "=========================================="
echo "RESTARTING DASHBOARD AND BOT"
echo "=========================================="
echo ""

# 1. Stop existing processes
echo "1. Stopping existing processes..."
echo "----------------------------------------"
pkill -f "deploy_supervisor"
pkill -f "python.*dashboard.py"
pkill -f "python.*main.py"
sleep 3
echo "✅ Processes stopped"
echo ""

# 2. Start deploy_supervisor (which manages both)
echo "2. Starting deploy_supervisor..."
echo "----------------------------------------"
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"
sleep 5
echo "✅ Supervisor started"
echo ""

# 3. Verify processes are running
echo "3. Verifying processes are running..."
echo "----------------------------------------"
SUPERVISOR_PID=$(ps aux | grep "deploy_supervisor" | grep -v grep | awk '{print $2}')
DASHBOARD_PID=$(ps aux | grep "python.*dashboard.py" | grep -v grep | awk '{print $2}')
BOT_PID=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')

if [ ! -z "$SUPERVISOR_PID" ]; then
    echo "✅ Supervisor running (PID: $SUPERVISOR_PID)"
else
    echo "❌ Supervisor NOT running"
fi

if [ ! -z "$DASHBOARD_PID" ]; then
    echo "✅ Dashboard running (PID: $DASHBOARD_PID)"
else
    echo "❌ Dashboard NOT running"
fi

if [ ! -z "$BOT_PID" ]; then
    echo "✅ Bot running (PID: $BOT_PID)"
else
    echo "❌ Bot NOT running"
fi
echo ""

# 4. Test endpoints
echo "4. Testing endpoints..."
echo "----------------------------------------"
sleep 3

# Test dashboard
DASHBOARD_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null)
if [ "$DASHBOARD_TEST" = "200" ]; then
    echo "✅ Dashboard responding (HTTP $DASHBOARD_TEST)"
else
    echo "❌ Dashboard not responding (HTTP $DASHBOARD_TEST)"
fi

# Test SRE endpoint
SRE_TEST=$(curl -s http://localhost:5000/api/sre/health 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print('OK' if 'overall_health' in d else 'ERROR')" 2>/dev/null || echo "ERROR")
if [ "$SRE_TEST" = "OK" ]; then
    echo "✅ SRE endpoint responding with data"
else
    echo "❌ SRE endpoint error"
fi

# Test bot health
BOT_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/health 2>/dev/null)
if [ "$BOT_HEALTH" = "200" ]; then
    echo "✅ Bot health endpoint responding (HTTP $BOT_HEALTH)"
else
    echo "❌ Bot health endpoint not responding (HTTP $BOT_HEALTH)"
fi
echo ""

echo "=========================================="
echo "DONE!"
echo "=========================================="
echo ""
echo "Dashboard should be updated with new SRE monitoring display."
echo "Try refreshing the browser (hard refresh: Ctrl+Shift+R or Cmd+Shift+R)"
echo ""
echo "To view supervisor logs:"
echo "  screen -r supervisor"
echo ""
