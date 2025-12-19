#!/bin/bash
# Comprehensive UW Daemon Diagnostic Script

echo "=========================================="
echo "UW DAEMON DIAGNOSTIC SCRIPT"
echo "=========================================="
echo ""

echo "1. CHECKING UW DAEMON PROCESS..."
if pgrep -f "uw_flow_daemon" > /dev/null; then
    echo "✅ UW daemon is RUNNING"
    ps aux | grep uw_flow_daemon | grep -v grep
else
    echo "❌ UW daemon is NOT running"
fi
echo ""

echo "2. CHECKING CACHE FILE..."
if [ -f "data/uw_flow_cache.json" ]; then
    echo "✅ Cache file exists"
    echo "   Size: $(ls -lh data/uw_flow_cache.json | awk '{print $5}')"
    echo "   Last modified: $(stat -c %y data/uw_flow_cache.json)"
    
    # Check if cache has flow_trades
    if python3 -c "import json; cache=json.load(open('data/uw_flow_cache.json')); trades=[k for k,v in cache.items() if isinstance(v,dict) and 'flow_trades' in v]; print(f'Found flow_trades in {len(trades)} tickers: {trades[:5]}')" 2>/dev/null; then
        echo "✅ Cache contains flow_trades"
    else
        echo "❌ Cache does NOT contain flow_trades"
    fi
else
    echo "❌ Cache file does NOT exist"
fi
echo ""

echo "3. CHECKING API QUOTA USAGE..."
if [ -f "check_uw_api_usage.sh" ]; then
    ./check_uw_api_usage.sh
else
    echo "⚠️  check_uw_api_usage.sh not found"
fi
echo ""

echo "4. CHECKING DAEMON LOGS (last 20 lines)..."
if [ -f "logs/uw-daemon-pc.log" ]; then
    echo "--- Last 20 lines of daemon log ---"
    tail -20 logs/uw-daemon-pc.log
else
    echo "❌ Daemon log file not found"
fi
echo ""

echo "5. CHECKING TRADING BOT LOGS FOR TRADES..."
if [ -f "logs/trading-bot-pc.log" ]; then
    echo "--- Recent clustering messages ---"
    grep -i "clustering.*trades\|flow_trades\|normalized" logs/trading-bot-pc.log | tail -10
else
    echo "⚠️  Trading bot log not found (check supervisor output)"
fi
echo ""

echo "6. TESTING UW API DIRECTLY..."
if [ -n "$UW_API_KEY" ]; then
    echo "Testing API call for AAPL..."
    response=$(curl -s -H "Authorization: Bearer $UW_API_KEY" \
        "https://api.unusualwhales.com/api/option-trades/flow-alerts?symbol=AAPL&limit=5")
    count=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('data', [])))" 2>/dev/null || echo "0")
    if [ "$count" -gt 0 ]; then
        echo "✅ API is working - got $count trades"
    else
        echo "❌ API returned 0 trades (might be rate limited or market closed)"
        echo "   Response: $(echo "$response" | head -c 200)"
    fi
else
    echo "⚠️  UW_API_KEY not set in environment"
fi
echo ""

echo "7. CHECKING MARKET HOURS..."
TZ=America/New_York date
hour=$(TZ=America/New_York date +%H)
if [ "$hour" -ge 9 ] && [ "$hour" -lt 16 ]; then
    echo "✅ Market should be open (9:30 AM - 4:00 PM ET)"
else
    echo "⚠️  Market is likely CLOSED (current hour: $hour ET)"
fi
echo ""

echo "=========================================="
echo "DIAGNOSTIC COMPLETE"
echo "=========================================="


