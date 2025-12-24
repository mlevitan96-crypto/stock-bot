#!/bin/bash
# Run daemon for 2 minutes and collect evidence

cd ~/stock-bot

echo "=========================================="
echo "RUNNING DAEMON AND COLLECTING EVIDENCE"
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

# Start daemon in background
echo "[3] Starting daemon in background..."
source venv/bin/activate
python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &
DAEMON_PID=$!

echo "Daemon started with PID: $DAEMON_PID"
echo ""

# Wait 2 minutes for it to run
echo "[4] Waiting 2 minutes for daemon to poll endpoints..."
sleep 120

# Kill gracefully
echo "[5] Stopping daemon gracefully..."
kill $DAEMON_PID 2>/dev/null
sleep 2

# Check what happened
echo ""
echo "[6] Analysis:"
echo "---"

# Check if daemon ran
if [ -f "logs/uw_daemon.log" ]; then
    echo "Daemon log size: $(wc -l < logs/uw_daemon.log) lines"
    echo ""
    echo "Last 50 lines:"
    tail -50 logs/uw_daemon.log
    echo ""
    echo "Market tide activity:"
    grep -i "market_tide\|Polling market_tide\|Updated market_tide" logs/uw_daemon.log | tail -10
    echo ""
    echo "API calls:"
    grep -i "API call\|get_market_tide\|Calling get_market_tide" logs/uw_daemon.log | tail -10
    echo ""
    echo "Errors:"
    grep -i "error\|exception\|traceback" logs/uw_daemon.log | tail -10
else
    echo "⚠️  No daemon log found"
fi

echo ""
echo "Debug log:"
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
    print("\nLast 20 events:")
    for e in events[-20:]:
        print(f"  [{e.get('hypothesisId', '?')}] {e.get('location', 'unknown')}: {e.get('message', '')}")
        data = e.get('data', {})
        if data and len(str(data)) < 200:
            print(f"      {data}")
PYEOF
else
    echo "⚠️  No debug log"
fi

echo ""
echo "[7] Cache check:"
python3 << 'PYEOF'
import json
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache = json.loads(cache_file.read_text())
    market_tide = cache.get("_market_tide", {})
    if market_tide:
        print(f"✅ market_tide in cache")
        print(f"  Has data: {bool(market_tide.get('data'))}")
        print(f"  Last update: {market_tide.get('last_update', 'unknown')}")
    else:
        print("❌ market_tide not in cache")
else:
    print("⚠️  Cache file not found")
PYEOF
