#!/bin/bash
# Test daemon with comprehensive log collection

cd ~/stock-bot

echo "=========================================="
echo "TESTING DAEMON AND COLLECTING LOGS"
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

# Verify debug log path is writable
echo "[3] Testing debug log path..."
python3 << 'PYEOF'
from pathlib import Path
import os

debug_path = Path("uw_flow_daemon.py").parent / ".cursor" / "debug.log"
print(f"Debug log path: {debug_path}")
print(f"Parent exists: {debug_path.parent.exists()}")
print(f"Parent is writable: {os.access(debug_path.parent, os.W_OK) if debug_path.parent.exists() else 'N/A'}")

try:
    debug_path.parent.mkdir(parents=True, exist_ok=True)
    with debug_path.open("w") as f:
        f.write("TEST\n")
    print(f"✅ Successfully wrote test to {debug_path}")
    debug_path.unlink()  # Remove test file
except Exception as e:
    print(f"❌ Failed to write test: {e}")
PYEOF

echo ""
echo "[4] Starting daemon for 15 seconds..."
source venv/bin/activate
python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo ""

# Monitor for 15 seconds
for i in {1..15}; do
    sleep 1
    if ! kill -0 $DAEMON_PID 2>/dev/null; then
        echo "⚠️  Daemon died after $i seconds"
        break
    fi
    if [ $((i % 3)) -eq 0 ]; then
        echo "  Still running after $i seconds..."
    fi
done

# Check if still running
if kill -0 $DAEMON_PID 2>/dev/null; then
    echo "✅ Daemon still running after 15 seconds"
    kill $DAEMON_PID 2>/dev/null
    sleep 1
else
    echo "❌ Daemon exited"
fi

echo ""
echo "[5] Analyzing logs..."
echo "---"

if [ -f "logs/uw_daemon.log" ]; then
    echo "Daemon log (full):"
    cat logs/uw_daemon.log
    echo ""
    echo "---"
    echo "Checking for debug messages in stderr:"
    grep -i "\[DEBUG\]\|\[DEBUG-ERROR\]\|\[MAIN\]" logs/uw_daemon.log || echo "No debug messages found"
else
    echo "⚠️  No daemon log file"
fi

echo ""
echo "[6] Debug log file analysis:"
if [ -f ".cursor/debug.log" ]; then
    echo "✅ Debug log exists ($(wc -l < .cursor/debug.log) lines)"
    echo ""
    echo "First 20 lines:"
    head -20 .cursor/debug.log
    echo ""
    echo "Last 20 lines:"
    tail -20 .cursor/debug.log
    echo ""
    echo "Parsing JSON entries:"
    python3 << 'PYEOF'
import json
from pathlib import Path

log_file = Path(".cursor/debug.log")
if log_file.exists():
    events = []
    with log_file.open() as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception as e:
                print(f"  Line {line_num} parse error: {e}")
                print(f"    Content: {line[:100]}")
    
    print(f"\nTotal valid events: {len(events)}")
    if events:
        print("\nEvents by hypothesis:")
        by_hyp = {}
        for e in events:
            h = e.get("hypothesisId", "unknown")
            if h not in by_hyp:
                by_hyp[h] = []
            by_hyp[h].append(e)
        
        for hyp, evts in sorted(by_hyp.items()):
            print(f"  {hyp}: {len(evts)} events")
            for e in evts[:3]:
                print(f"    - {e.get('location')}: {e.get('message')}")
        
        print("\nAll events (chronological):")
        for e in events:
            print(f"  [{e.get('hypothesisId', '?')}] {e.get('location', 'unknown')}: {e.get('message', '')}")
else
    echo "❌ Debug log file does not exist"
    echo "Checking if directory exists:"
    ls -la .cursor/ 2>/dev/null || echo "  .cursor directory does not exist"
fi

echo ""
echo "[7] Process check:"
ps aux | grep -E "uw.*daemon|uw_flow_daemon" | grep -v grep || echo "No daemon processes"
