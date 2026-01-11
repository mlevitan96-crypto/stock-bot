#!/bin/bash
# Quick check of UW daemon status

echo "=========================================="
echo "UW DAEMON STATUS CHECK"
echo "=========================================="
echo ""

echo "1. Is daemon running?"
if pgrep -f "uw_flow_daemon" > /dev/null; then
    echo "✅ YES - PID: $(pgrep -f uw_flow_daemon)"
else
    echo "❌ NO - daemon not running"
    exit 1
fi
echo ""

echo "2. Check daemon output (last 30 lines)..."
echo "--- Looking for 'Retrieved', 'Stored', 'Polling' ---"
tail -30 logs/uw-daemon-pc.log 2>/dev/null | grep -E "Retrieved|Stored|Polling|flow_trades|Error" || echo "No daemon log found - check supervisor output"
echo ""

echo "3. Check cache for flow_trades..."
if [ -f "data/uw_flow_cache.json" ]; then
    count=$(python3 -c "
import json
try:
    cache = json.load(open('data/uw_flow_cache.json'))
    tickers_with_trades = [k for k, v in cache.items() if isinstance(v, dict) and 'flow_trades' in v and v.get('flow_trades')]
    print(len(tickers_with_trades))
except:
    print(0)
" 2>/dev/null)
    if [ "$count" -gt 0 ]; then
        echo "✅ Cache has flow_trades for $count tickers"
        echo "   Tickers: $(python3 -c \"import json; cache=json.load(open('data/uw_flow_cache.json')); print([k for k,v in cache.items() if isinstance(v,dict) and 'flow_trades' in v and v.get('flow_trades')][:5])\" 2>/dev/null)"
    else
        echo "❌ Cache does NOT have flow_trades yet"
        echo "   Daemon may still be polling (wait 2-3 minutes)"
    fi
else
    echo "❌ Cache file doesn't exist"
fi
echo ""

echo "4. Check API quota usage..."
if [ -f "check_uw_api_usage.sh" ]; then
    ./check_uw_api_usage.sh
else
    echo "⚠️  Script not found"
fi
echo ""

echo "5. Market status..."
TZ=America/New_York hour=$(date +%H)
if [ "$hour" -ge 9 ] && [ "$hour" -lt 16 ]; then
    echo "✅ Market should be open"
else
    echo "⚠️  Market likely CLOSED (hour: $hour ET)"
    echo "   No flow data during off-hours"
fi
echo ""

echo "=========================================="
echo "RECOMMENDATION:"
if [ "$count" -eq 0 ]; then
    echo "Wait 2-3 minutes for daemon to poll, then check again"
    echo "Run: ./CHECK_DAEMON_STATUS.sh"
else
    echo "✅ Daemon is working - trades should appear in next cycle"
fi
echo "=========================================="

