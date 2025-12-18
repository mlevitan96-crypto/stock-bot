#!/bin/bash
# Check supervisor output for errors

echo "=========================================="
echo "CHECKING SUPERVISOR OUTPUT"
echo "=========================================="
echo ""

echo "1. Check if supervisor is running..."
if pgrep -f "deploy_supervisor" > /dev/null; then
    echo "✅ Supervisor is running (PID: $(pgrep -f deploy_supervisor))"
else
    echo "❌ Supervisor is NOT running"
fi
echo ""

echo "2. Check for 'no such file' errors in process output..."
echo "   (Check the terminal where supervisor is running)"
echo "   Look for: FileNotFoundError, No such file, ENOENT"
echo ""

echo "3. Check daemon process directly..."
if pgrep -f "uw_flow_daemon" > /dev/null; then
    pid=$(pgrep -f uw_flow_daemon)
    echo "   Daemon PID: $pid"
    echo "   Checking if process is healthy..."
    
    # Check if process is still running (not zombie)
    if ps -p $pid > /dev/null 2>&1; then
        state=$(ps -p $pid -o state=)
        if [ "$state" = "Z" ]; then
            echo "   ⚠️  Process is a ZOMBIE (crashed but not cleaned up)"
        else
            echo "   ✅ Process is running (state: $state)"
        fi
    else
        echo "   ❌ Process not found"
    fi
else
    echo "   ❌ Daemon process not found"
fi
echo ""

echo "4. Check recent API calls for errors..."
if [ -f "data/uw_api_quota.jsonl" ]; then
    echo "   Last 5 API calls:"
    tail -5 data/uw_api_quota.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        url = d.get('url', '')
        params = d.get('params', {})
        symbol = params.get('symbol', 'N/A')
        print(f\"     {symbol}: {url.split('/')[-1] if '/' in url else url}\")
    except:
        pass
"
    
    # Check for 429s
    rate_limited=$(tail -20 data/uw_api_quota.jsonl | grep -c "429" || echo "0")
    if [ "$rate_limited" -gt 0 ]; then
        echo "   ⚠️  Found rate limit (429) errors - limit resets at 8PM EST"
    fi
else
    echo "   ⚠️  No quota log found"
fi
echo ""

echo "5. Test API endpoint format directly..."
if [ -n "$UW_API_KEY" ]; then
    echo "   Testing flow-alerts endpoint with symbol=AAPL..."
    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -H "Authorization: Bearer $UW_API_KEY" \
        "https://api.unusualwhales.com/api/option-trades/flow-alerts?symbol=AAPL&limit=5" 2>&1)
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    json_response=$(echo "$response" | sed '/HTTP_CODE:/d')
    
    echo "   HTTP Status: $http_code"
    
    if [ "$http_code" = "200" ]; then
        count=$(echo "$json_response" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(len(d.get('data', [])))
except:
    print(0)
" 2>/dev/null)
        echo "   ✅ API returned $count trades"
    elif [ "$http_code" = "429" ]; then
        echo "   ❌ RATE LIMITED (429) - limit resets at 8PM EST"
    elif [ "$http_code" = "404" ]; then
        echo "   ❌ NOT FOUND (404) - endpoint may be wrong"
        echo "   Response: $(echo "$json_response" | head -c 200)"
    else
        echo "   ⚠️  Error: HTTP $http_code"
        echo "   Response: $(echo "$json_response" | head -c 200)"
    fi
else
    echo "   ⚠️  UW_API_KEY not set (can't test)"
fi
echo ""

echo "=========================================="
echo "SUMMARY:"
echo "- If you see 'no such file' error, check supervisor terminal"
echo "- If API returns 429: Wait for 8PM EST reset"
echo "- If API returns 404: Endpoint format may be wrong"
echo "- If API returns 200 but 0 trades: Normal (no unusual flow)"
echo "=========================================="
