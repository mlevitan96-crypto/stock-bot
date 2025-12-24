#!/bin/bash
# Comprehensive analysis of why daemon isn't working

cd ~/stock-bot

echo "=========================================="
echo "COMPREHENSIVE DAEMON ANALYSIS"
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

# Test Python import and basic execution
echo "[3] Testing Python module load..."
python3 << 'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

try:
    from uw_flow_daemon import UWFlowDaemon, main
    print("✅ Module imports successfully")
    
    # Try to create daemon instance
    try:
        daemon = UWFlowDaemon()
        print("✅ Daemon instance created")
        print(f"   Tickers: {len(daemon.tickers)}")
        print(f"   Running: {daemon.running}")
        print(f"   Has API key: {bool(daemon.client.api_key)}")
    except Exception as e:
        print(f"❌ Failed to create daemon: {e}")
        import traceback
        traceback.print_exc()
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "[4] Starting daemon and monitoring for 10 seconds..."
source venv/bin/activate
python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &
DAEMON_PID=$!

echo "Daemon PID: $DAEMON_PID"
echo ""

# Monitor for 10 seconds
for i in {1..10}; do
    sleep 1
    if ! kill -0 $DAEMON_PID 2>/dev/null; then
        echo "⚠️  Daemon died after $i seconds"
        break
    fi
    if [ $((i % 2)) -eq 0 ]; then
        echo "  Still running after $i seconds..."
    fi
done

# Check if still running
if kill -0 $DAEMON_PID 2>/dev/null; then
    echo "✅ Daemon still running after 10 seconds"
    kill $DAEMON_PID 2>/dev/null
    sleep 1
else
    echo "❌ Daemon exited"
fi

echo ""
echo "[5] Analyzing logs..."
echo "---"

if [ -f "logs/uw_daemon.log" ]; then
    echo "Log file size: $(wc -l < logs/uw_daemon.log) lines"
    echo ""
    echo "Full log:"
    cat logs/uw_daemon.log
    echo ""
else
    echo "⚠️  No log file"
fi

echo ""
echo "[6] Debug log analysis:"
if [ -f ".cursor/debug.log" ]; then
    echo "Found $(wc -l < .cursor/debug.log) entries"
    python3 << 'PYEOF'
import json
from pathlib import Path

log_file = Path(".cursor/debug.log")
if log_file.exists():
    events = []
    with log_file.open() as f:
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except:
                pass
    
    print(f"Total events: {len(events)}")
    print("\nAll events by hypothesis:")
    by_hyp = {}
    for e in events:
        h = e.get("hypothesisId", "unknown")
        if h not in by_hyp:
            by_hyp[h] = []
        by_hyp[h].append(e)
    
    for hyp, evts in by_hyp.items():
        print(f"\n  {hyp}: {len(evts)} events")
        for e in evts[:5]:  # First 5
            print(f"    - {e.get('location')}: {e.get('message')}")
        if len(evts) > 5:
            print(f"    ... and {len(evts) - 5} more")
    
    print("\n\nLast 30 events:")
    for e in events[-30:]:
        print(f"  [{e.get('hypothesisId', '?')}] {e.get('location', 'unknown')}: {e.get('message', '')}")
        data = e.get('data', {})
        if data:
            data_str = str(data)
            if len(data_str) < 150:
                print(f"      Data: {data_str}")
PYEOF
else
    echo "⚠️  No debug log - instrumentation may not be running"
fi

echo ""
echo "[7] Checking for process issues:"
ps aux | grep -E "uw.*daemon|uw_flow_daemon" | grep -v grep || echo "No daemon processes"

echo ""
echo "[8] Checking environment:"
echo "  UW_API_KEY: ${UW_API_KEY:+SET (hidden)}${UW_API_KEY:-NOT SET}"
echo "  Python: $(python3 --version)"
echo "  Working dir: $(pwd)"
