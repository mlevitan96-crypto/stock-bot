#!/bin/bash
# Test daemon startup and collect all logs

cd ~/stock-bot

echo "=========================================="
echo "TESTING DAEMON AND COLLECTING LOGS"
echo "=========================================="
echo ""

# Stop any existing daemon
echo "[1] Stopping existing daemon..."
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

# Clear old logs
echo "[2] Clearing old logs..."
rm -f logs/uw_daemon.log .cursor/debug.log 2>/dev/null
mkdir -p .cursor logs

# Start daemon in foreground for 30 seconds to capture startup
echo "[3] Starting daemon (will run for 30 seconds)..."
timeout 30 python3 uw_flow_daemon.py 2>&1 | tee logs/uw_daemon_test.log || true

echo ""
echo "[4] Checking what was logged..."
echo ""

# Check daemon log
echo "Daemon log (last 50 lines):"
tail -50 logs/uw_daemon_test.log 2>/dev/null || echo "No daemon log"

echo ""
echo "Debug log:"
if [ -f ".cursor/debug.log" ]; then
    echo "Found $(wc -l < .cursor/debug.log) lines:"
    cat .cursor/debug.log
else
    echo "⚠️  No debug log created"
fi

echo ""
echo "[5] Checking for errors in stderr..."
grep -i "error\|exception\|traceback\|failed" logs/uw_daemon_test.log 2>/dev/null | tail -20 || echo "No errors found"
