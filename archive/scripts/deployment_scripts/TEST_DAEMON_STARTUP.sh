#!/bin/bash
# Test daemon startup to see why it exits immediately

cd ~/stock-bot

echo "=========================================="
echo "TESTING DAEMON STARTUP"
echo "=========================================="
echo ""

# Stop existing
echo "[1] Stopping existing daemon..."
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

# Clear logs
echo "[2] Clearing logs..."
rm -f logs/uw_daemon.log .cursor/debug.log 2>/dev/null
mkdir -p .cursor logs

# Check for other processes that might kill it
echo "[3] Checking for processes that might interfere..."
ps aux | grep -E "health_supervisor|heartbeat_keeper|deploy_supervisor" | grep -v grep || echo "  No supervisor processes found"

echo ""
echo "[4] Starting daemon in foreground for 10 seconds..."
source venv/bin/activate
timeout 10 python3 uw_flow_daemon.py 2>&1 | tee logs/uw_daemon_test.log || true

echo ""
echo "[5] Checking what happened..."
if [ -f "logs/uw_daemon_test.log" ]; then
    echo "Log contents:"
    cat logs/uw_daemon_test.log
    echo ""
    echo "---"
    echo "Checking for signals:"
    grep -i "signal\|SIGTERM\|SIGINT\|shutting down" logs/uw_daemon_test.log || echo "  No signal messages"
    echo ""
    echo "Checking for errors:"
    grep -i "error\|exception\|traceback" logs/uw_daemon_test.log || echo "  No errors"
    echo ""
    echo "Checking for main loop entry:"
    grep -i "Entering main\|Cycle start\|Polling" logs/uw_daemon_test.log || echo "  Main loop never entered"
else
    echo "⚠️  No log file created"
fi

echo ""
echo "[6] Debug log:"
if [ -f ".cursor/debug.log" ]; then
    echo "Found $(wc -l < .cursor/debug.log) lines"
    head -20 .cursor/debug.log
else
    echo "⚠️  No debug log"
fi
