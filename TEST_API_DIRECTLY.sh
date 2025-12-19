#!/bin/bash
# Test UW API directly to see what it's actually returning

echo "=========================================="
echo "TESTING UW API DIRECTLY"
echo "=========================================="
echo ""

cd /root/stock-bot

# Load .env if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -z "$UW_API_KEY" ]; then
    echo "❌ UW_API_KEY not found in environment or .env"
    echo "   Check if .env file exists and has UW_API_KEY"
    exit 1
fi

echo "✅ UW_API_KEY found"
echo ""

echo "Testing AAPL flow-alerts endpoint..."
response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -H "Authorization: Bearer $UW_API_KEY" \
    "https://api.unusualwhales.com/api/option-trades/flow-alerts?symbol=AAPL&limit=10")

http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
json_response=$(echo "$response" | sed '/HTTP_CODE:/d')

echo "HTTP Status: $http_code"
echo ""

if [ "$http_code" != "200" ]; then
    echo "❌ API returned non-200 status: $http_code"
    echo "Response:"
    echo "$json_response" | head -20
    exit 1
fi

echo "Response structure:"
echo "$json_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'Top-level keys: {list(data.keys())}')
    
    if 'data' in data:
        trades = data['data']
        print(f'Number of trades in response: {len(trades)}')
        
        if len(trades) > 0:
            print(f'\n✅ API RETURNED {len(trades)} TRADES')
            print(f'\nFirst trade structure:')
            first = trades[0]
            print(f'  Keys: {list(first.keys())[:15]}')
            print(f'\nFirst trade sample:')
            for key in list(first.keys())[:10]:
                val = first.get(key)
                if isinstance(val, str) and len(val) > 50:
                    val = val[:50] + '...'
                print(f'  {key}: {val}')
        else:
            print(f'\n⚠️  API returned empty data array')
            print(f'Full response:')
            print(json.dumps(data, indent=2)[:500])
    else:
        print(f'\n⚠️  Response missing \"data\" key')
        print(f'Full response:')
        print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f'Error parsing JSON: {e}')
    print(f'Raw response (first 500 chars):')
    print(sys.stdin.read()[:500])
"

echo ""
echo "=========================================="
echo "Testing with different limit..."
response2=$(curl -s -H "Authorization: Bearer $UW_API_KEY" \
    "https://api.unusualwhales.com/api/option-trades/flow-alerts?symbol=AAPL&limit=100")

count2=$(echo "$response2" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(len(d.get('data', [])))
except:
    print(0)
" 2>/dev/null)

echo "With limit=100: $count2 trades"
echo ""

echo "Testing MSFT..."
response3=$(curl -s -H "Authorization: Bearer $UW_API_KEY" \
    "https://api.unusualwhales.com/api/option-trades/flow-alerts?symbol=MSFT&limit=10")

count3=$(echo "$response3" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(len(d.get('data', [])))
except:
    print(0)
" 2>/dev/null)

echo "MSFT: $count3 trades"
echo ""

echo "=========================================="
echo "SUMMARY:"
echo "- If API returns 0 trades for multiple tickers during market hours:"
echo "  1. API may require different parameters (time window, etc.)"
echo "  2. API may only return 'unusual' flow (not all flow)"
echo "  3. There may genuinely be no unusual flow right now"
echo "  4. API endpoint or format may have changed"
echo "=========================================="

