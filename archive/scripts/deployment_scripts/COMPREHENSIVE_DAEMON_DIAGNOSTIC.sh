#!/bin/bash
# Comprehensive diagnostic to understand EXACTLY why daemon isn't entering loop

cd ~/stock-bot

echo "=========================================="
echo "COMPREHENSIVE DAEMON DIAGNOSTIC"
echo "=========================================="
echo ""

# Step 1: Verify fix is in code
echo "[1] Verifying fix is present..."
if grep -q "_loop_entered" uw_flow_daemon.py; then
    echo "✅ _loop_entered flag found"
    if grep -q "IGNORING.*before loop entry" uw_flow_daemon.py; then
        echo "✅ Signal ignore logic found"
    else
        echo "❌ Signal ignore logic NOT found"
    fi
else
    echo "❌ Fix NOT in code - need to pull from git"
fi

# Step 2: Check what the actual log shows
echo ""
echo "[2] Analyzing actual daemon log..."
if [ -f "logs/uw_daemon_fix_test.log" ]; then
    echo "--- Full log content ---"
    cat logs/uw_daemon_fix_test.log
    echo ""
    echo "--- Key events ---"
    echo "Step messages:"
    grep -E "Step [0-9]" logs/uw_daemon_fix_test.log || echo "No step messages"
    echo ""
    echo "Signal messages:"
    grep -E "Signal|IGNORING|shutting down" logs/uw_daemon_fix_test.log || echo "No signal messages"
    echo ""
    echo "Loop entry:"
    grep -E "INSIDE|SUCCESS.*Entered|Loop entry flag" logs/uw_daemon_fix_test.log || echo "No loop entry messages"
    echo ""
    echo "Last 20 lines:"
    tail -20 logs/uw_daemon_fix_test.log
else
    echo "⚠️  Log file not found"
fi

# Step 3: Test with maximum verbosity
echo ""
echo "[3] Running fresh test with maximum verbosity..."
pkill -f "uw.*daemon|uw_flow_daemon" 2>/dev/null
sleep 2

rm -f data/uw_flow_cache.json logs/uw_daemon_diagnostic.log 2>/dev/null
mkdir -p data logs

source venv/bin/activate
python3 -u uw_flow_daemon.py > logs/uw_daemon_diagnostic.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo "Waiting 30 seconds and monitoring..."
for i in {1..6}; do
    sleep 5
    if ! ps -p $DAEMON_PID > /dev/null 2>&1; then
        echo "❌ Daemon exited after $((i * 5)) seconds"
        break
    fi
    echo "  Still running at $((i * 5)) seconds..."
done

# Check what happened
echo ""
echo "[4] Diagnostic results:"
if ps -p $DAEMON_PID > /dev/null 2>&1; then
    echo "✅ Daemon still running"
    kill $DAEMON_PID 2>/dev/null
else
    echo "❌ Daemon exited"
fi

echo ""
echo "--- Diagnostic log (last 100 lines) ---"
tail -100 logs/uw_daemon_diagnostic.log

echo ""
echo "--- Sequence analysis ---"
python3 << PYEOF
from pathlib import Path
import re

log_file = Path("logs/uw_daemon_diagnostic.log")
if log_file.exists():
    content = log_file.read_text()
    lines = content.split('\n')
    
    # Find key events
    events = []
    for i, line in enumerate(lines, 1):
        if "Step" in line or "INSIDE" in line or "Signal" in line or "IGNORING" in line or "shutting down" in line or "loop entry" in line or "Loop entry flag" in line:
            events.append((i, line.strip()))
    
    print("Key events in sequence:")
    for line_num, event in events[:30]:  # First 30 events
        print(f"  Line {line_num}: {event}")
    
    # Check for loop entry
    if any("INSIDE while loop" in e[1] or "SUCCESS.*Entered main loop" in e[1] for e in events):
        print("\n✅ Loop entry detected")
    else:
        print("\n❌ Loop entry NOT detected")
    
    # Check for ignored signals
    ignored = [e for e in events if "IGNORING" in e[1]]
    if ignored:
        print(f"\n✅ Found {len(ignored)} ignored signals:")
        for line_num, event in ignored:
            print(f"  Line {line_num}: {event}")
    else:
        print("\n⚠️  No ignored signals found (either no signals or fix not working)")
    
    # Check for shutdown signals
    shutdowns = [e for e in events if "shutting down" in e[1] or "Received signal" in e[1]]
    if shutdowns:
        print(f"\n⚠️  Found {len(shutdowns)} shutdown signals:")
        for line_num, event in shutdowns:
            print(f"  Line {line_num}: {event}")
PYEOF

echo ""
echo "=========================================="
echo "DIAGNOSTIC COMPLETE"
echo "=========================================="
