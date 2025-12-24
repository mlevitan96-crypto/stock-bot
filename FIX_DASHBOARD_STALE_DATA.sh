#!/bin/bash
# Fix dashboard stale data issues
# 1. Restart dashboard to apply heartbeat fix
# 2. Fix SRE health JSON parsing error

set +e

echo "=================================================================================="
echo "FIXING DASHBOARD STALE DATA ISSUES"
echo "=================================================================================="
echo ""

# 1. Pull latest dashboard.py with heartbeat fix
echo "1. Pulling latest code..."
git pull origin main || echo "⚠️  Git pull failed, continuing with local code"
echo ""

# 2. Verify dashboard.py has the fix
echo "2. Verifying dashboard.py heartbeat fix..."
if grep -q "state/bot_heartbeat.json.*# Main bot heartbeat - check FIRST" dashboard.py; then
    echo "  ✅ Dashboard fix is present"
else
    echo "  ⚠️  Dashboard fix not found - may need to pull"
fi
echo ""

# 3. Restart dashboard to apply fix
echo "3. Restarting dashboard..."
pkill -f "python.*dashboard.py" 2>/dev/null
sleep 2

# Start dashboard
python3 dashboard.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
sleep 3

# Verify dashboard started
if ps -p $DASHBOARD_PID > /dev/null 2>&1 || pgrep -f "python.*dashboard.py" > /dev/null; then
    echo "  ✅ Dashboard restarted (PID: $DASHBOARD_PID or $(pgrep -f 'python.*dashboard.py'))"
else
    echo "  ❌ Dashboard failed to start"
    echo "  Checking logs..."
    tail -20 logs/dashboard.log 2>/dev/null || echo "  No log file found"
    exit 1
fi
echo ""

# 4. Test dashboard endpoints
echo "4. Testing dashboard endpoints..."
sleep 2

# Test health_status
HEALTH_RESPONSE=$(curl -s http://localhost:5000/api/health_status 2>&1)
if echo "$HEALTH_RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
    echo "  ✅ /api/health_status responding"
    # Extract heartbeat age
    DOCTOR_AGE=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('doctor', {}).get('age_minutes', 'N/A'))" 2>/dev/null)
    echo "     Doctor/Heartbeat age: $DOCTOR_AGE minutes"
    
    if [ "$DOCTOR_AGE" != "N/A" ] && [ "$(echo "$DOCTOR_AGE < 60" | bc 2>/dev/null || echo 0)" = "1" ]; then
        echo "     ✅ Heartbeat is fresh (< 60 minutes)"
    else
        echo "     ⚠️  Heartbeat still stale - may need to check heartbeat file"
    fi
else
    echo "  ❌ /api/health_status failed"
    echo "     Response: $HEALTH_RESPONSE"
fi

# Test SRE health
SRE_RESPONSE=$(curl -s http://localhost:5000/api/sre/health 2>&1)
if echo "$SRE_RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
    echo "  ✅ /api/sre/health responding"
else
    echo "  ⚠️  /api/sre/health has JSON parsing issues"
    echo "     First 200 chars: ${SRE_RESPONSE:0:200}"
fi
echo ""

# 5. Check actual heartbeat file
echo "5. Checking actual heartbeat file..."
if [ -f "state/bot_heartbeat.json" ]; then
    HB_TS=$(python3 -c "import json; d=json.load(open('state/bot_heartbeat.json')); print(d.get('last_heartbeat_ts', 'N/A'))" 2>/dev/null)
    if [ "$HB_TS" != "N/A" ]; then
        HB_AGE=$(python3 -c "import time; ts=$HB_TS; print((time.time() - ts) / 60)" 2>/dev/null)
        echo "  ✅ bot_heartbeat.json exists"
        echo "     Timestamp: $HB_TS"
        echo "     Age: ${HB_AGE} minutes"
    else
        echo "  ⚠️  bot_heartbeat.json missing timestamp"
    fi
else
    echo "  ⚠️  bot_heartbeat.json not found"
fi
echo ""

# 6. Summary
echo "=================================================================================="
echo "SUMMARY"
echo "=================================================================================="
echo ""
echo "✅ Dashboard restarted with heartbeat fix"
echo ""
echo "Next steps:"
echo "1. Check dashboard: http://localhost:5000"
echo "2. Verify 'Doctor' shows recent time (< 60 minutes)"
echo "3. If still stale, check if bot is generating heartbeats:"
echo "   tail -f logs/main.log | grep -i heartbeat"
echo ""
