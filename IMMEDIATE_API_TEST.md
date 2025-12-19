# IMMEDIATE API TEST - Run This Now

## Step 1: Test API Directly

```bash
cd /root/stock-bot
git pull origin main --no-rebase
chmod +x TEST_API_DIRECTLY.sh
./TEST_API_DIRECTLY.sh
```

This will:
- Test the API with your actual key
- Show the exact response structure
- Test multiple tickers
- Show if there are any errors

## Step 2: Check Daemon Logs

Look at the supervisor output for messages like:
- `[UW-DAEMON] Retrieved X flow trades for TICKER`
- `[UW-DAEMON] API returned 0 trades`
- Any error messages

## Step 3: Check Recent API Responses

```bash
cd /root/stock-bot
# Check the last few API calls and their responses
tail -20 data/uw_flow_cache_log.jsonl | grep -i "error\|data" | tail -5
```

## Possible Issues:

1. **API only returns "alerts" (unusual activity)** - If there's no unusual flow, it returns empty
2. **Time window required** - API might need `start_date`/`end_date` parameters
3. **API endpoint changed** - The endpoint structure might have changed
4. **Rate limiting** - Even though we're under limits, there might be soft limits

## What to Look For:

After running `TEST_API_DIRECTLY.sh`, check:
- Does it return trades? (count > 0)
- What's the response structure?
- Are there any error messages?
- Does it work for multiple tickers?

