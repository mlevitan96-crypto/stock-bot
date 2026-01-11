#!/bin/bash
# Diagnose why cache file isn't being created

cd ~/stock-bot

echo "=========================================="
echo "DIAGNOSING CACHE CREATION ISSUE"
echo "=========================================="
echo ""

echo "[1] Checking daemon logs (last 50 lines)..."
if [ -f "logs/uw_daemon.log" ]; then
    echo "--- Recent daemon activity ---"
    tail -50 logs/uw_daemon.log
    echo ""
    echo "--- Checking for errors ---"
    tail -100 logs/uw_daemon.log | grep -i "error\|exception\|traceback\|failed" | tail -10
    echo ""
    echo "--- Checking for polling activity ---"
    tail -100 logs/uw_daemon.log | grep -E "Polling|Retrieved|Cache for|Updated" | tail -10
else
    echo "❌ No daemon log file found"
fi

echo ""
echo "[2] Checking if daemon is actually in main loop..."
if [ -f "logs/uw_daemon.log" ]; then
    if grep -q "run() method called" logs/uw_daemon.log; then
        echo "✅ Daemon entered run() method"
    else
        echo "❌ Daemon never entered run() method"
    fi
    
    if grep -q "INSIDE while loop\|SUCCESS.*Entered main loop" logs/uw_daemon.log; then
        echo "✅ Daemon entered main loop"
    else
        echo "❌ Daemon never entered main loop"
    fi
    
    if grep -q "Retrieved.*flow trades\|Polling.*got.*trades" logs/uw_daemon.log; then
        echo "✅ Daemon is polling and getting data"
    else
        echo "❌ Daemon is not polling or getting data"
    fi
fi

echo ""
echo "[3] Checking cache directory permissions..."
if [ -d "data" ]; then
    echo "✅ data/ directory exists"
    ls -ld data/
    echo ""
    echo "Testing write permission..."
    touch data/test_write.tmp 2>&1
    if [ -f "data/test_write.tmp" ]; then
        echo "✅ data/ directory is writable"
        rm -f data/test_write.tmp
    else
        echo "❌ data/ directory is NOT writable"
    fi
else
    echo "❌ data/ directory does not exist"
    echo "Creating it..."
    mkdir -p data
    if [ -d "data" ]; then
        echo "✅ Created data/ directory"
    else
        echo "❌ Failed to create data/ directory"
    fi
fi

echo ""
echo "[4] Checking daemon process details..."
if pgrep -f "uw.*daemon|uw_flow_daemon" > /dev/null; then
    DAEMON_PID=$(pgrep -f "uw.*daemon|uw_flow_daemon" | head -1)
    echo "Daemon PID: $DAEMON_PID"
    echo "Process info:"
    ps aux | grep "$DAEMON_PID" | grep -v grep
    echo ""
    echo "Process working directory:"
    pwdx $DAEMON_PID 2>/dev/null || echo "Cannot determine working directory"
else
    echo "❌ Daemon process not found"
fi

echo ""
echo "[5] Testing cache write manually..."
python3 << PYEOF
import json
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
cache_file.parent.mkdir(parents=True, exist_ok=True)

test_data = {
    "_test": "manual_write_test",
    "_metadata": {
        "test": True
    }
}

try:
    cache_file.write_text(json.dumps(test_data, indent=2))
    print("✅ Manual cache write successful")
    
    # Verify read
    read_data = json.loads(cache_file.read_text())
    print(f"✅ Manual cache read successful: {read_data.get('_test')}")
    
    # Clean up test
    cache_file.unlink()
    print("✅ Test cache file removed")
except Exception as e:
    print(f"❌ Manual cache write failed: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "[6] Checking if daemon is stuck or waiting..."
if [ -f "logs/uw_daemon.log" ]; then
    LAST_LINE=$(tail -1 logs/uw_daemon.log)
    echo "Last log line: $LAST_LINE"
    
    # Check how long since last activity
    LAST_MOD=$(stat -c %Y logs/uw_daemon.log 2>/dev/null || stat -f %m logs/uw_daemon.log 2>/dev/null)
    NOW=$(date +%s)
    AGE=$((NOW - LAST_MOD))
    echo "Log file age: $AGE seconds"
    
    if [ $AGE -gt 300 ]; then
        echo "⚠️  Log file hasn't been updated in $AGE seconds (5+ minutes)"
        echo "   Daemon may be stuck or not actively running"
    else
        echo "✅ Log file is being updated (last update $AGE seconds ago)"
    fi
fi

echo ""
echo "=========================================="
echo "DIAGNOSIS COMPLETE"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the daemon logs above"
echo "2. If daemon is not polling, check if it's stuck"
echo "3. If cache directory is not writable, fix permissions"
echo "4. If daemon is running but not creating cache, restart it:"
echo "   pkill -f 'uw.*daemon|uw_flow_daemon'"
echo "   sleep 2"
echo "   nohup python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &"
