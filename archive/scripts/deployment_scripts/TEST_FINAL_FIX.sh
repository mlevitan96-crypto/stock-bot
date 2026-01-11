#!/bin/bash
# Final comprehensive test of the daemon fix

cd ~/stock-bot

echo "=========================================="
echo "FINAL DAEMON FIX TEST"
echo "=========================================="
echo ""

# Pull latest code
echo "[1] Pulling latest code..."
git pull origin main

# Verify fix is present
echo ""
echo "[2] Verifying fix..."
if grep -q "LOOP ENTERED" uw_flow_daemon.py && grep -q "_loop_entered = True" uw_flow_daemon.py; then
    echo "✅ Fix verified in code"
else
    echo "❌ Fix not found - code may need to be updated"
    exit 1
fi

# Stop everything
echo ""
echo "[3] Stopping existing processes..."
pkill -f "uw.*daemon|uw_flow_daemon|deploy_supervisor" 2>/dev/null
sleep 3

# Clear cache and logs
echo "[4] Clearing cache and logs..."
rm -f data/uw_flow_cache.json logs/uw_daemon_final_test.log 2>/dev/null
mkdir -p data logs

# Start daemon
echo ""
echo "[5] Starting daemon for 2 minutes..."
source venv/bin/activate
python3 -u uw_flow_daemon.py > logs/uw_daemon_final_test.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo "Waiting 120 seconds..."
sleep 120

# Check results
echo ""
echo "=========================================="
echo "RESULTS"
echo "=========================================="
echo ""

if ps -p $DAEMON_PID > /dev/null 2>&1; then
    echo "✅ Daemon still running"
    
    # Check for loop entry
    if grep -q "LOOP ENTERED" logs/uw_daemon_final_test.log; then
        echo "✅ Daemon entered main loop"
        LOOP_TIME=$(grep "LOOP ENTERED" logs/uw_daemon_final_test.log | head -1 | sed 's/.*\[UW-DAEMON\] //')
        echo "   Entry message: $LOOP_TIME"
    else
        echo "❌ Daemon never entered main loop"
    fi
    
    # Check for ignored signals
    IGNORED_COUNT=$(grep -c "IGNORING.*before loop entry" logs/uw_daemon_final_test.log 2>/dev/null || echo "0")
    if [ "$IGNORED_COUNT" -gt 0 ]; then
        echo "✅ Fix working - $IGNORED_COUNT premature signals ignored"
    fi
    
    # Check cache
    if [ -f "data/uw_flow_cache.json" ]; then
        TICKER_COUNT=$(python3 -c "import json; from pathlib import Path; cache = json.loads(Path('data/uw_flow_cache.json').read_text()); print(len([k for k in cache.keys() if not k.startswith('_')]))" 2>/dev/null || echo "0")
        echo "✅ Cache file created with $TICKER_COUNT tickers"
    else
        echo "⚠️  Cache file not created"
    fi
    
    # Check for polling activity
    POLL_COUNT=$(grep -c "Polling" logs/uw_daemon_final_test.log 2>/dev/null || echo "0")
    if [ "$POLL_COUNT" -gt 0 ]; then
        echo "✅ Polling activity detected ($POLL_COUNT occurrences)"
    else
        echo "⚠️  No polling activity detected"
    fi
    
    kill $DAEMON_PID 2>/dev/null
else
    echo "❌ Daemon exited during test"
    echo ""
    echo "Last 50 lines of log:"
    tail -50 logs/uw_daemon_final_test.log
fi

echo ""
echo "Full log: logs/uw_daemon_final_test.log"
echo ""
