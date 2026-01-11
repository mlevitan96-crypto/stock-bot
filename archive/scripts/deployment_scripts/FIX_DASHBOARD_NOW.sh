#!/bin/bash
# Quick fix for dashboard startup issues

cd ~/stock-bot

echo "Checking dashboard error..."
if [ -f "logs/dashboard.log" ]; then
    echo "Last 20 lines of dashboard.log:"
    tail -20 logs/dashboard.log
    echo ""
fi

echo "Checking for syntax errors..."
python3 -m py_compile dashboard.py 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Dashboard syntax is valid"
else
    echo "❌ Syntax error found!"
    exit 1
fi

echo ""
echo "Killing any existing dashboard processes..."
pkill -f dashboard.py
sleep 2

echo "Starting dashboard..."
python3 dashboard.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
sleep 3

if ps -p $DASHBOARD_PID > /dev/null; then
    echo "✓ Dashboard started (PID: $DASHBOARD_PID)"
    echo ""
    echo "Testing health_status endpoint..."
    sleep 2
    curl -s http://localhost:5000/api/health_status | python3 -m json.tool || echo "⚠️  Endpoint returned invalid JSON"
else
    echo "❌ Dashboard failed to start"
    echo "Error log:"
    tail -30 logs/dashboard.log
    exit 1
fi

echo ""
echo "Dashboard should now be running at http://localhost:5000"
