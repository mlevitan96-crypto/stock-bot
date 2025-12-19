#!/bin/bash
# Diagnose why API is returning empty trades

echo "=========================================="
echo "DIAGNOSING EMPTY TRADES"
echo "=========================================="
echo ""

cd /root/stock-bot

echo "1. Check daemon logs (last 20 lines)..."
echo "   Look for: '[UW-DAEMON] API returned 0 trades'"
echo ""

echo "2. Check API quota usage..."
if [ -f "data/uw_api_quota.jsonl" ]; then
    total=$(wc -l < data/uw_api_quota.jsonl)
    last_hour=$(tail -60 data/uw_api_quota.jsonl 2>/dev/null | wc -l)
    echo "   Total API calls: $total"
    echo "   Last hour: $last_hour"
    echo ""
    echo "   Last 5 API calls:"
    tail -5 data/uw_api_quota.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        params = d.get('params', {})
        symbol = params.get('symbol', 'N/A')
        print(f\"     {d.get('ts', 0)}: {symbol}\")
    except:
        pass
"
else
    echo "   ⚠️  No quota log found"
fi
echo ""

echo "3. Check for API errors..."
if [ -f "data/uw_flow_cache_log.jsonl" ]; then
    errors=$(tail -20 data/uw_flow_cache_log.jsonl | grep -i "error" | wc -l)
    echo "   Recent errors: $errors"
    if [ "$errors" -gt 0 ]; then
        echo "   Last error:"
        tail -20 data/uw_flow_cache_log.jsonl | grep -i "error" | tail -1 | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(f\"     {d.get('error', 'N/A')}\")
except:
    pass
"
    fi
else
    echo "   ✅ No error log (good)"
fi
echo ""

echo "4. Test API directly (if UW_API_KEY is set)..."
if [ -n "$UW_API_KEY" ]; then
    echo "   Testing AAPL..."
    response=$(curl -s -H "Authorization: Bearer $UW_API_KEY" \
        "https://api.unusualwhales.com/api/option-trades/flow-alerts?symbol=AAPL&limit=5" 2>&1)
    
    # Check HTTP status
    http_code=$(echo "$response" | grep -oP 'HTTP/\d\.\d \K\d+' | tail -1 || echo "200")
    
    # Extract JSON if present
    json_part=$(echo "$response" | python3 -c "
import sys
text = sys.stdin.read()
# Try to find JSON part
if '{' in text:
    start = text.find('{')
    print(text[start:])
else:
    print(text[:500])
" 2>/dev/null)
    
    count=$(echo "$json_part" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    data = d.get('data', [])
    print(len(data))
except:
    print(0)
" 2>/dev/null)
    
    if [ "$count" -gt 0 ]; then
        echo "   ✅ API returned $count trades for AAPL"
    else
        echo "   ❌ API returned 0 trades for AAPL"
        echo "   HTTP code: $http_code"
        echo "   Response preview: $(echo "$json_part" | head -c 200)"
    fi
else
    echo "   ⚠️  UW_API_KEY not set (can't test)"
fi
echo ""

echo "5. Check market hours..."
TZ=America/New_York hour=$(date +%H)
TZ=America/New_York minute=$(date +%M)
echo "   Current time ET: $hour:$minute"
if [ "$hour" -ge 9 ] && [ "$hour" -lt 16 ]; then
    if [ "$hour" -eq 9 ] && [ "$minute" -lt 30 ]; then
        echo "   ⚠️  Market not open yet (opens 9:30 AM ET)"
    else
        echo "   ✅ Market should be open"
    fi
else
    echo "   ⚠️  Market likely CLOSED"
fi
echo ""

echo "=========================================="
echo "SUMMARY:"
echo "- Cache has flow_trades keys: ✅ WORKING"
echo "- API returning data: ❓ CHECK ABOVE"
echo ""
echo "If API test returned 0 trades:"
echo "  1. Market may be closed or no recent flow"
echo "  2. API may be rate limited (check quota)"
echo "  3. API endpoint may have changed"
echo "=========================================="

