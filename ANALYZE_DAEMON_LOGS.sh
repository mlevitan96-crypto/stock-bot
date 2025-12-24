#!/bin/bash
# Analyze daemon logs to understand why endpoints aren't working

cd ~/stock-bot

echo "=========================================="
echo "ANALYZING DAEMON LOGS"
echo "=========================================="
echo ""

# Check if test log exists
if [ -f "logs/uw_daemon_test.log" ]; then
    echo "[1] Test log analysis:"
    echo "---"
    
    # Check for debug messages
    echo "Debug messages:"
    grep -i "\[DEBUG\]" logs/uw_daemon_test.log | tail -30
    echo ""
    
    # Check for API calls
    echo "API call attempts:"
    grep -i "API call attempt\|get_market_tide\|Calling get_market_tide" logs/uw_daemon_test.log | tail -20
    echo ""
    
    # Check for API responses
    echo "API responses:"
    grep -i "API call success\|get_market_tide response\|Raw API response\|Extracted data" logs/uw_daemon_test.log | tail -20
    echo ""
    
    # Check for polling decisions
    echo "Polling decisions:"
    grep -i "Polling decision\|should_poll\|First poll allowed\|Polling allowed" logs/uw_daemon_test.log | tail -20
    echo ""
    
    # Check for market_tide specific
    echo "Market tide activity:"
    grep -i "market_tide" logs/uw_daemon_test.log | tail -20
    echo ""
    
    # Check for errors
    echo "Errors:"
    grep -i "error\|exception\|traceback\|failed" logs/uw_daemon_test.log | tail -20
    echo ""
else
    echo "⚠️  No test log found. Run TEST_DAEMON_AND_COLLECT_LOGS.sh first"
fi

# Check debug log
echo "[2] Debug log analysis:"
if [ -f ".cursor/debug.log" ]; then
    echo "Found $(wc -l < .cursor/debug.log) debug log entries"
    echo "---"
    # Parse and show key events
    python3 << 'PYEOF'
import json
from pathlib import Path

log_file = Path(".cursor/debug.log")
if log_file.exists():
    events = []
    with log_file.open() as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                events.append(event)
            except:
                pass
    
    # Group by hypothesis
    by_hyp = {}
    for e in events:
        h = e.get("hypothesisId", "unknown")
        if h not in by_hyp:
            by_hyp[h] = []
        by_hyp[h].append(e)
    
    print(f"Total events: {len(events)}")
    print(f"By hypothesis: {dict((k, len(v)) for k, v in by_hyp.items())}")
    print("")
    
    # Show key events
    print("Key events:")
    for e in events[-30:]:  # Last 30 events
        print(f"  {e.get('location', 'unknown')}: {e.get('message', '')} {e.get('data', {})}")
else:
    print("⚠️  No debug log found")
PYEOF
else
    echo "⚠️  No debug log found"
fi

echo ""
echo "[3] Checking cache for market_tide:"
python3 << 'PYEOF'
import json
from pathlib import Path

cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache = json.loads(cache_file.read_text())
    market_tide = cache.get("_market_tide", {})
    if market_tide:
        print(f"✅ market_tide found in cache")
        print(f"  Keys: {list(market_tide.keys())}")
        print(f"  Has data: {bool(market_tide.get('data'))}")
        print(f"  Last update: {market_tide.get('last_update', 'unknown')}")
    else:
        print("❌ market_tide not in cache")
else:
    print("⚠️  Cache file not found")
PYEOF
