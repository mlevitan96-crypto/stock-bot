#!/bin/bash
# Check actual UW API usage from quota log

QUOTA_LOG="data/uw_api_quota.jsonl"

if [ ! -f "$QUOTA_LOG" ]; then
    echo "No quota log found - no API calls tracked yet"
    exit 0
fi

echo "=== UW API Usage Analysis ==="
echo ""

# Count requests in last hour
now=$(date +%s)
one_hour_ago=$((now - 3600))
one_day_ago=$((now - 86400))

requests_1h=0
requests_24h=0
requests_today=0

today_date=$(date +%Y-%m-%d)

while IFS= read -r line; do
    if [ -z "$line" ]; then
        continue
    fi
    
    ts=$(echo "$line" | python3 -c "import sys, json; print(json.load(sys.stdin).get('ts', 0))" 2>/dev/null)
    if [ -z "$ts" ] || [ "$ts" = "0" ]; then
        continue
    fi
    
    if [ "$ts" -gt "$one_hour_ago" ]; then
        requests_1h=$((requests_1h + 1))
    fi
    
    if [ "$ts" -gt "$one_day_ago" ]; then
        requests_24h=$((requests_24h + 1))
    fi
    
    # Check if today
    call_date=$(date -d "@$ts" +%Y-%m-%d 2>/dev/null || echo "")
    if [ "$call_date" = "$today_date" ]; then
        requests_today=$((requests_today + 1))
    fi
done < "$QUOTA_LOG"

echo "Requests in last hour: $requests_1h"
echo "Requests in last 24h: $requests_24h"
echo "Requests today: $requests_today"
echo ""

# Calculate projected daily usage
if [ "$requests_1h" -gt 0 ]; then
    projected_daily=$((requests_1h * 24))
    echo "Projected daily usage (based on last hour): $projected_daily"
    echo ""
    
    if [ "$projected_daily" -gt 15000 ]; then
        echo "⚠️  WARNING: Projected usage ($projected_daily) exceeds daily limit (15,000)"
        echo "   Current usage: $requests_today / 15,000 ($((requests_today * 100 / 15000))%)"
    else
        echo "✅ Projected usage ($projected_daily) is within limit (15,000)"
        echo "   Current usage: $requests_today / 15,000 ($((requests_today * 100 / 15000))%)"
    fi
fi

echo ""
echo "=== Recent API Calls (last 10) ==="
tail -10 "$QUOTA_LOG" | python3 -c "
import sys, json
from datetime import datetime
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        ts = data.get('ts', 0)
        url = data.get('url', '')
        source = data.get('source', 'unknown')
        dt = datetime.fromtimestamp(ts).strftime('%H:%M:%S') if ts else 'unknown'
        # Extract endpoint from URL
        endpoint = url.split('/api/')[-1] if '/api/' in url else url
        print(f'{dt} | {source:15} | {endpoint[:50]}')
    except:
        pass
"



