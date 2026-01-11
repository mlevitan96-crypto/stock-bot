#!/bin/bash
# Check daemon status and why trades aren't happening

echo "=========================================="
echo "DIAGNOSING: No Trades & File Errors"
echo "=========================================="
echo ""

cd /root/stock-bot

echo "1. Check if daemon is running..."
if pgrep -f "uw_flow_daemon" > /dev/null; then
    echo "✅ Daemon is running (PID: $(pgrep -f uw_flow_daemon))"
else
    echo "❌ Daemon is NOT running"
fi
echo ""

echo "2. Check daemon logs (last 20 lines)..."
echo "   Look for errors, rate limits, or API issues:"
if [ -f "logs/uw-daemon-pc.log" ]; then
    tail -20 logs/uw-daemon-pc.log | grep -E "ERROR|RATE|429|404|FileNotFound|Exception" || echo "   No errors in log file"
else
    echo "   ⚠️  Log file not found - check supervisor output"
fi
echo ""

echo "3. Check cache for flow_trades..."
python3 -c "
import json
try:
    cache = json.load(open('data/uw_flow_cache.json'))
    tickers_with_trades = [t for t, v in cache.items() 
                          if isinstance(v, dict) and v.get('flow_trades') and len(v.get('flow_trades', [])) > 0]
    print(f'   Tickers with actual trades: {len(tickers_with_trades)}')
    if tickers_with_trades:
        for t in tickers_with_trades[:5]:
            count = len(cache[t]['flow_trades'])
            print(f'     {t}: {count} trades')
    else:
        print('   ⚠️  No tickers have trades in cache')
        # Check if keys exist but are empty
        tickers_with_keys = [t for t, v in cache.items() 
                            if isinstance(v, dict) and 'flow_trades' in v]
        print(f'   Tickers with flow_trades key: {len(tickers_with_keys)}')
except Exception as e:
    print(f'   ❌ Error reading cache: {e}')
"
echo ""

echo "4. Check API quota usage..."
if [ -f "data/uw_api_quota.jsonl" ]; then
    recent=$(tail -10 data/uw_api_quota.jsonl 2>/dev/null | wc -l)
    echo "   Recent API calls (last 10): $recent"
    
    # Check for 404s or errors
    errors=$(tail -50 data/uw_api_quota.jsonl | python3 -c "
import sys, json
count = 0
for line in sys.stdin:
    try:
        d = json.loads(line)
        url = d.get('url', '')
        if '404' in url or 'error' in str(d).lower():
            count += 1
    except:
        pass
print(count)
" 2>/dev/null)
    if [ "$errors" -gt 0 ]; then
        echo "   ⚠️  Found $errors potential errors in recent calls"
    fi
else
    echo "   ⚠️  No quota log found"
fi
echo ""

echo "5. Check for missing files..."
missing_count=0
if [ ! -f "data/uw_flow_cache.json" ]; then
    echo "   ❌ Missing: data/uw_flow_cache.json"
    missing_count=$((missing_count + 1))
fi
if [ ! -f "uw_flow_daemon.py" ]; then
    echo "   ❌ Missing: uw_flow_daemon.py"
    missing_count=$((missing_count + 1))
fi
if [ ! -f "test_uw_endpoints.py" ]; then
    echo "   ❌ Missing: test_uw_endpoints.py"
    missing_count=$((missing_count + 1))
fi

if [ $missing_count -eq 0 ]; then
    echo "   ✅ All expected files exist"
fi
echo ""

echo "6. Check trading bot logs for 'clustering' messages..."
if [ -f "logs/trading-bot-pc.log" ]; then
    echo "   Recent clustering results:"
    tail -50 logs/trading-bot-pc.log | grep -E "clustering|Found.*raw trades|No flow_trades" | tail -5 || echo "   No clustering messages found"
else
    echo "   ⚠️  Trading bot log not found - check supervisor output"
fi
echo ""

echo "=========================================="
echo "NEXT STEPS:"
echo "1. If daemon not running: Restart supervisor"
echo "2. If rate limited: Wait for 8PM EST reset"
echo "3. If 404 errors: Check endpoint names match API docs"
echo "4. If no trades: Check if market is open and API returning data"
echo "=========================================="
