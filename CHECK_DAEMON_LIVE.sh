#!/bin/bash
# Check what the daemon is actually seeing in real-time

echo "=========================================="
echo "LIVE DAEMON STATUS CHECK"
echo "=========================================="
echo ""

cd /root/stock-bot

echo "1. Check daemon process..."
if pgrep -f "uw_flow_daemon" > /dev/null; then
    pid=$(pgrep -f uw_flow_daemon)
    echo "✅ Daemon running (PID: $pid)"
    echo "   Process info:"
    ps -p $pid -o pid,state,etime,cmd | tail -1
else
    echo "❌ Daemon NOT running"
    exit 1
fi
echo ""

echo "2. Check recent API error log..."
if [ -f "data/uw_flow_cache_log.jsonl" ]; then
    echo "   Last 5 entries:"
    tail -5 data/uw_flow_cache_log.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        event = d.get('event', 'unknown')
        status = d.get('status', 'N/A')
        error = d.get('error', d.get('message', ''))[:100]
        print(f\"     {event}: {status} - {error}\")
    except:
        print(f\"     {line[:100]}\")
" 2>/dev/null || echo "   Could not parse log"
else
    echo "   ⚠️  No error log found (may be good - no errors)"
fi
echo ""

echo "3. Check if daemon is rate limited..."
if [ -f "data/uw_flow_cache_log.jsonl" ]; then
    rate_limited=$(tail -20 data/uw_flow_cache_log.jsonl | grep -c "RATE_LIMITED\|429" || echo "0")
    if [ "$rate_limited" != "0" ] && [ "$rate_limited" -gt 0 ] 2>/dev/null; then
        echo "   ⚠️  Found $rate_limited rate limit events"
        echo "   Last rate limit event:"
        tail -20 data/uw_flow_cache_log.jsonl | grep -i "rate_limit\|429" | tail -1 | python3 -c "
import sys, json
try:
    d = json.loads(sys.stdin.read())
    print(f\"     Time: {d.get('ts', 'N/A')}\")
    print(f\"     Message: {d.get('message', d.get('error', 'N/A'))[:150]}\")
except:
    pass
" 2>/dev/null
    else
        echo "   ✅ No rate limit events found"
    fi
fi
echo ""

echo "4. Test API with .env key..."
# Load .env
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -n "$UW_API_KEY" ]; then
    echo "   Testing flow-alerts endpoint..."
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
    data = d.get('data', [])
    print(len(data))
    if len(data) > 0:
        print('Sample trade keys: ' + ', '.join(list(data[0].keys())[:5]))
except Exception as e:
    print(f'0 (Error: {e})')
" 2>/dev/null)
        
        if [ "$count" != "0" ] && [ "$count" != "" ]; then
            echo "   ✅ API returned $count trades"
        else
            echo "   ⚠️  API returned 0 trades (empty data array)"
            echo "   This is normal if there's no unusual flow activity"
        fi
    elif [ "$http_code" = "429" ]; then
        echo "   ❌ RATE LIMITED (429)"
        echo "   Limit resets at 8PM EST / 5PM PST"
        error_msg=$(echo "$json_response" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('message', 'Daily limit hit')[:150])
except:
    print('Daily limit exceeded')
" 2>/dev/null)
        echo "   Message: $error_msg"
    elif [ "$http_code" = "404" ]; then
        echo "   ❌ NOT FOUND (404) - Endpoint may be wrong"
        echo "   Response: $(echo "$json_response" | head -c 200)"
    else
        echo "   ⚠️  HTTP $http_code"
        echo "   Response: $(echo "$json_response" | head -c 200)"
    fi
else
    echo "   ⚠️  UW_API_KEY not found in .env or environment"
    echo "   (But daemon must have it since it's making calls)"
fi
echo ""

echo "=========================================="
echo "SUMMARY:"
echo "- Check supervisor terminal for daemon output"
echo "- Look for: [UW-DAEMON] Retrieved X flow trades"
echo "- Or: [UW-DAEMON] API returned 0 trades"
echo "- Or: [UW-DAEMON] ❌ RATE LIMITED (429)"
echo "=========================================="
