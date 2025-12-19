# Immediate Commands - No Git Pull Needed

## Check if daemon is working RIGHT NOW

### Command 1: Check if daemon process exists
```bash
ps aux | grep uw_flow_daemon | grep -v grep
```

### Command 2: Check cache file
```bash
cd /root/stock-bot
ls -lh data/uw_flow_cache.json
```

### Command 3: Check if cache has flow_trades
```bash
cd /root/stock-bot
python3 -c "
import json
try:
    cache = json.load(open('data/uw_flow_cache.json'))
    tickers = [k for k, v in cache.items() if isinstance(v, dict) and 'flow_trades' in v and v.get('flow_trades')]
    print(f'Found flow_trades in {len(tickers)} tickers')
    if tickers:
        print(f'Tickers: {tickers[:5]}')
except Exception as e:
    print(f'Error: {e}')
"
```

### Command 4: Check when cache was last updated
```bash
cd /root/stock-bot
stat data/uw_flow_cache.json | grep Modify
```

### Command 5: Check API quota usage
```bash
cd /root/stock-bot
if [ -f "data/uw_api_quota.jsonl" ]; then
    echo "Last hour: $(tail -60 data/uw_api_quota.jsonl 2>/dev/null | wc -l) calls"
    echo "Last 24h: $(tail -1440 data/uw_api_quota.jsonl 2>/dev/null | wc -l) calls"
else
    echo "No quota log - daemon may not have made API calls yet"
fi
```

### Command 6: Check market hours
```bash
TZ=America/New_York date
TZ=America/New_York hour=$(date +%H)
if [ "$hour" -ge 9 ] && [ "$hour" -lt 16 ]; then
    echo "✅ Market should be open"
else
    echo "⚠️  Market likely CLOSED - no flow data during off-hours"
fi
```

## What to Expect

### If daemon just started (< 2 minutes ago):
- Cache may not have flow_trades yet
- This is NORMAL - daemon polls every 60 seconds
- Wait 2-3 minutes and check again

### If daemon has been running > 3 minutes:
- Cache should have flow_trades for some tickers
- If not, check:
  1. Market hours (closed = no data)
  2. API quota (exhausted = no data)
  3. Daemon errors (check supervisor output)

## Check Supervisor Output Directly

The daemon logs to supervisor stdout. Look for:
- `[UW-DAEMON] Retrieved X flow trades for TICKER`
- `[UW-DAEMON] Stored X raw trades in cache for TICKER`

These messages appear in the supervisor terminal window.

