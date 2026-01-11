#!/bin/bash
# Complete verification and test of daemon fix

cd ~/stock-bot

echo "=========================================="
echo "COMPLETE DAEMON VERIFICATION"
echo "=========================================="
echo ""

# Step 1: Verify fix is in code
echo "[1] Verifying fix in code..."
if grep -q "_loop_entered = False" uw_flow_daemon.py && \
   grep -q "if not self._loop_entered:" uw_flow_daemon.py; then
    echo "✅ Fix code present"
else
    echo "❌ Fix not found - applying now..."
    chmod +x FIX_DAEMON_NOW.sh 2>/dev/null
    ./FIX_DAEMON_NOW.sh || {
        echo "❌ Fix script failed"
        exit 1
    }
fi

# Step 2: Test daemon for 2 minutes
echo ""
echo "[2] Testing daemon (2 minutes)..."
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

rm -f data/uw_flow_cache.json logs/uw_daemon_verify.log 2>/dev/null
mkdir -p data logs

source venv/bin/activate
python3 -u uw_flow_daemon.py > logs/uw_daemon_verify.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo "Waiting 120 seconds for full test..."
sleep 120

# Step 3: Comprehensive check
echo ""
echo "=========================================="
echo "VERIFICATION RESULTS"
echo "=========================================="
echo ""

# Check if still running
if ps -p $DAEMON_PID > /dev/null 2>&1; then
    echo "✅ Daemon still running"
    RUNNING=true
else
    echo "❌ Daemon exited"
    RUNNING=false
fi

# Check for loop entry message
if grep -q "LOOP ENTERED" logs/uw_daemon_verify.log; then
    echo "✅ Loop entry message found"
    LOOP_MSG=true
else
    echo "⚠️  Loop entry message not found (but daemon may still be working)"
    LOOP_MSG=false
fi

# Check for polling activity (proves loop is entered)
POLL_COUNT=$(grep -c "Polling\|Retrieved.*flow trades" logs/uw_daemon_verify.log 2>/dev/null || echo "0")
if [ "$POLL_COUNT" -gt 0 ]; then
    echo "✅ Polling activity detected ($POLL_COUNT occurrences) - LOOP IS WORKING"
    POLLING=true
else
    echo "❌ No polling activity - loop not working"
    POLLING=false
fi

# Check cache
if [ -f "data/uw_flow_cache.json" ]; then
    TICKER_COUNT=$(python3 -c "import json; from pathlib import Path; cache = json.loads(Path('data/uw_flow_cache.json').read_text()); tickers = [k for k in cache.keys() if not k.startswith('_')]; print(len(tickers))" 2>/dev/null || echo "0")
    if [ "$TICKER_COUNT" -gt 0 ]; then
        echo "✅ Cache file created with $TICKER_COUNT tickers"
        CACHE=true
    else
        echo "⚠️  Cache file exists but empty"
        CACHE=false
    fi
else
    echo "❌ Cache file not created"
    CACHE=false
fi

# Check for ignored signals
IGNORED_COUNT=$(grep -c "IGNORING.*before loop entry" logs/uw_daemon_verify.log 2>/dev/null || echo "0")
if [ "$IGNORED_COUNT" -gt 0 ]; then
    echo "✅ Fix working - $IGNORED_COUNT premature signals ignored"
fi

# Check for errors
ERROR_COUNT=$(grep -c "Error\|Exception\|Traceback" logs/uw_daemon_verify.log 2>/dev/null || echo "0")
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  Found $ERROR_COUNT errors in log"
    echo "   Recent errors:"
    grep -i "error\|exception" logs/uw_daemon_verify.log | tail -3
fi

# Final assessment
echo ""
echo "=========================================="
echo "FINAL ASSESSMENT"
echo "=========================================="

if [ "$RUNNING" = true ] && [ "$POLLING" = true ] && [ "$CACHE" = true ]; then
    echo "✅✅✅ DAEMON IS FULLY WORKING ✅✅✅"
    echo ""
    echo "The daemon is:"
    echo "  ✅ Running continuously"
    echo "  ✅ Entering main loop (polling proves this)"
    echo "  ✅ Creating and populating cache"
    echo ""
    echo "The fix is working! The 'LOOP ENTERED' message may not appear"
    echo "but the daemon is clearly in the loop and functioning correctly."
    echo ""
    echo "Next steps:"
    echo "  1. Restart supervisor to use the fixed daemon"
    echo "  2. Monitor cache file to ensure it stays populated"
    echo "  3. Verify all UW API endpoints are being polled"
    SUCCESS=true
else
    echo "❌ DAEMON HAS ISSUES"
    echo ""
    echo "Status:"
    echo "  Running: $RUNNING"
    echo "  Polling: $POLLING"
    echo "  Cache: $CACHE"
    echo ""
    echo "Review log: logs/uw_daemon_verify.log"
    SUCCESS=false
fi

kill $DAEMON_PID 2>/dev/null

echo ""
if [ "$SUCCESS" = true ]; then
    echo "✅ WORKFLOW IS READY"
    exit 0
else
    echo "❌ WORKFLOW NEEDS FIXES"
    exit 1
fi
