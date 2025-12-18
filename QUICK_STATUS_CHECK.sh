#!/bin/bash
# Quick status check - works without pulling new files

echo "=========================================="
echo "QUICK STATUS CHECK"
echo "=========================================="
echo ""

echo "1. Is daemon running?"
if pgrep -f "uw_flow_daemon" > /dev/null; then
    echo "✅ YES - PID: $(pgrep -f uw_flow_daemon)"
else
    echo "❌ NO"
fi
echo ""

echo "2. Is trading bot running?"
if pgrep -f "main.py" > /dev/null; then
    echo "✅ YES - PID: $(pgrep -f 'main.py')"
else
    echo "❌ NO"
fi
echo ""

echo "3. Check cache file..."
if [ -f "data/uw_flow_cache.json" ]; then
    echo "✅ Cache exists"
    size=$(ls -lh data/uw_flow_cache.json | awk '{print $5}')
    echo "   Size: $size"
    modified=$(stat -c %y data/uw_flow_cache.json | cut -d'.' -f1)
    echo "   Last modified: $modified"
    
    # Check for flow_trades
    count=$(python3 -c "
import json
try:
    cache = json.load(open('data/uw_flow_cache.json'))
    tickers = [k for k, v in cache.items() if isinstance(v, dict) and 'flow_trades' in v and v.get('flow_trades')]
    print(len(tickers))
except:
    print(0)
" 2>/dev/null)
    
    if [ "$count" -gt 0 ]; then
        echo "✅ Cache has flow_trades for $count tickers"
    else
        echo "⚠️  No flow_trades yet (daemon may still be polling)"
    fi
else
    echo "❌ Cache file doesn't exist"
fi
echo ""

echo "4. Check API quota..."
if [ -f "data/uw_api_quota.jsonl" ]; then
    recent=$(tail -60 data/uw_api_quota.jsonl 2>/dev/null | wc -l)
    echo "   Recent API calls (last hour): $recent"
else
    echo "⚠️  No quota log found"
fi
echo ""

echo "5. Market hours..."
TZ=America/New_York hour=$(date +%H)
if [ "$hour" -ge 9 ] && [ "$hour" -lt 16 ]; then
    echo "✅ Market should be open (hour: $hour ET)"
else
    echo "⚠️  Market likely CLOSED (hour: $hour ET)"
fi
echo ""

echo "=========================================="
echo "To see daemon activity, check supervisor output"
echo "or run: ps aux | grep uw_flow_daemon"
echo "=========================================="
