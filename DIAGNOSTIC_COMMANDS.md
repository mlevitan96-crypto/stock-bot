# Diagnostic Commands for UW Daemon Issues

Run these on your droplet to diagnose the "no data" and "no trades" issues:

## 1. Check UW Daemon Status
```bash
# Check if daemon is running
ps aux | grep uw_flow_daemon | grep -v grep

# Check daemon logs
tail -50 logs/uw-daemon-pc.log

# Check if daemon is making API calls
./check_uw_api_usage.sh
```

## 2. Check Cache Contents
```bash
# View cache structure
cat data/uw_flow_cache.json | python3 -m json.tool | head -100

# Check specific ticker (e.g., AAPL)
cat data/uw_flow_cache.json | python3 -m json.tool | grep -A 20 '"AAPL"'

# Check cache freshness
stat data/uw_flow_cache.json
ls -lh data/uw_flow_cache.json
```

## 3. Check API Quota
```bash
# Check API usage
./check_uw_api_usage.sh

# Check quota log directly
tail -20 data/uw_api_quota.jsonl | python3 -m json.tool
```

## 4. Check What Main.py Sees
```bash
# Check trading bot logs for cache reads
grep -i "cache\|clustering\|trades" logs/trading-bot-pc.log | tail -20

# Check for errors
grep -i "error\|warning\|failed" logs/trading-bot-pc.log | tail -20
```

## 5. Test UW API Directly
```bash
# Test if API is working (replace YOUR_KEY)
curl -H "Authorization: Bearer $UW_API_KEY" \
  "https://api.unusualwhales.com/api/option-trades/flow-alerts?symbol=AAPL&limit=5"
```

## 6. Check Market Hours
```bash
# Check if market is open (ET timezone)
TZ=America/New_York date
```

## Expected Issues:
1. **Cache has sentiment but no raw trades** - Daemon stores summaries, not individual trades
2. **API quota exhausted** - Check with `./check_uw_api_usage.sh`
3. **Market closed** - No flow data during off-hours
4. **Daemon not polling** - Check daemon logs for errors
