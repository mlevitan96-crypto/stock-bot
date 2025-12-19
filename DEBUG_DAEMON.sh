#!/bin/bash
# Debug why daemon isn't storing flow_trades

echo "=========================================="
echo "DEBUGGING UW DAEMON"
echo "=========================================="
echo ""

echo "1. Check cache structure (what IS in cache?)..."
cd /root/stock-bot
python3 -c "
import json
try:
    cache = json.load(open('data/uw_flow_cache.json'))
    print(f'Cache has {len([k for k in cache.keys() if not k.startswith(\"_\")])} tickers')
    
    # Check first ticker structure
    for ticker, data in cache.items():
        if not ticker.startswith('_') and isinstance(data, dict):
            print(f'\n{ticker} has keys: {list(data.keys())[:10]}')
            if 'flow_trades' in data:
                trades = data.get('flow_trades', [])
                print(f'  flow_trades: {len(trades) if isinstance(trades, list) else \"not a list\"} items')
            if 'sentiment' in data:
                print(f'  sentiment: {data.get(\"sentiment\")}')
            break
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
"
echo ""

echo "2. Check recent API quota entries..."
if [ -f "data/uw_api_quota.jsonl" ]; then
    echo "Last 5 API calls:"
    tail -5 data/uw_api_quota.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        print(f\"  {d.get('ts', 0)}: {d.get('url', '')} - {d.get('params', {})}\")
    except:
        pass
"
else
    echo "No quota log"
fi
echo ""

echo "3. Check if daemon is seeing errors..."
echo "Look in supervisor output for:"
echo "  - [UW-DAEMON] Retrieved X flow trades"
echo "  - [UW-DAEMON] Error"
echo "  - UW_API_ERROR"
echo ""

echo "4. Test API directly (if UW_API_KEY is set)..."
if [ -n "$UW_API_KEY" ]; then
    echo "Testing API for AAPL..."
    response=$(curl -s -H "Authorization: Bearer $UW_API_KEY" \
        "https://api.unusualwhales.com/api/option-trades/flow-alerts?symbol=AAPL&limit=5")
    
    count=$(echo "$response" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    data = d.get('data', [])
    print(len(data))
    if len(data) > 0:
        print(f'First trade keys: {list(data[0].keys())[:10]}')
except:
    print(0)
" 2>/dev/null)
    
    if [ "$count" -gt 0 ]; then
        echo "✅ API returned $count trades"
    else
        echo "❌ API returned 0 trades"
        echo "   Response preview: $(echo "$response" | head -c 200)"
    fi
else
    echo "⚠️  UW_API_KEY not set"
fi
echo ""

echo "=========================================="
echo "NEXT STEPS:"
echo "1. Check supervisor output for daemon messages"
echo "2. If API test returned 0 trades, API may be rate limited"
echo "3. Check cache structure above to see what IS being stored"
echo "=========================================="

