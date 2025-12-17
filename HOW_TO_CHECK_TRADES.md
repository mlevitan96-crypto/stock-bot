# How to Check if Trades and Everything Are Working

## Quick Status Check

Based on your concerns about:
- **Last order is 3 hours old** (yellow indicator)
- **Doctor is 50 minutes** (yellow indicator)

Here's how to verify everything is working properly:

## Method 1: Check via API Endpoints (If System is Running)

If your trading bot is running, you can check these endpoints:

### Health Check (Doctor Status)
```bash
curl http://localhost:8081/health
# or
curl http://localhost:5000/health
```

This will show:
- `last_heartbeat_age_sec` - This is your "Doctor" indicator
- Health check status for all systems

### Recent Orders
```bash
curl http://localhost:8081/api/logs
# Look for the "orders" array - check the "_ts" (timestamp) of the last order
```

### Current Positions
```bash
curl http://localhost:8081/api/positions
```

### Account Status
```bash
curl http://localhost:8081/api/account
```

## Method 2: Check Files Directly

### Last Order Check
The last order timestamp is stored in:
- `data/live_orders.jsonl` - Check the last line for the most recent order

To check:
```bash
# On Linux/Mac:
tail -1 data/live_orders.jsonl | python -m json.tool

# On Windows PowerShell:
Get-Content data\live_orders.jsonl -Tail 1 | ConvertFrom-Json
```

### Doctor/Heartbeat Check
The heartbeat file is at:
- `state/system_heartbeat.json` (from process-compose.yaml)
- `state/heartbeat.json` (alternative location)

To check:
```bash
# On Linux/Mac:
cat state/system_heartbeat.json | python -m json.tool

# On Windows PowerShell:
Get-Content state\system_heartbeat.json | ConvertFrom-Json
```

Look for the `timestamp` or `_ts` field to see when the last heartbeat was recorded.

## Method 3: Use the Diagnostic Scripts

### System Health Check (File-based)
```bash
python check_system_health.py
```

This checks:
- Recent orders from files
- Heartbeat status
- Alpaca connectivity
- UW cache freshness
- Health supervisor status

### API-based Check (Requires requests module)
```bash
pip install requests
python check_trades_api.py
```

This queries the running system via HTTP endpoints.

## Understanding the Yellow Indicators

### Last Order: 3 Hours Old
**Is this a problem?**
- **During market hours (9:30 AM - 4:00 PM ET)**: This could indicate the bot isn't finding trading opportunities or there's an issue
- **Outside market hours**: This is normal - no trades should execute
- **Weekends**: This is normal

**What to check:**
1. Is the market currently open?
2. Are there any error messages in the logs?
3. Check if the bot is actively scanning: `curl http://localhost:8081/api/state`
4. Look at recent signals: Check `logs/signals.jsonl`

### Doctor: 50 Minutes
**Is this a problem?**
- **< 5 minutes**: Healthy
- **5-30 minutes**: Warning (yellow) - system may be slow but functioning
- **> 30 minutes**: Critical (red) - system may be stuck

**What to check:**
1. Is the `heartbeat-keeper` process running?
   ```bash
   # Check process-compose status
   process-compose ps
   ```
2. Check the heartbeat file timestamp
3. Look for errors in `logs/heartbeat-keeper-pc.log`

## What to Do If There Are Issues

### If Last Order is Old During Market Hours:

1. **Check if bot is running:**
   ```bash
   process-compose ps
   # or
   ps aux | grep "python main.py"
   ```

2. **Check for errors:**
   ```bash
   tail -50 logs/trading-bot-pc.log
   tail -50 logs/worker_error.jsonl
   ```

3. **Check if signals are being generated:**
   ```bash
   tail -20 logs/signals.jsonl
   ```

4. **Check Alpaca connectivity:**
   ```bash
   curl http://localhost:8081/api/account
   ```
   Look for `"trading_blocked": false` and `"status": "ACTIVE"`

5. **Check if circuit breaker is engaged:**
   ```bash
   cat state/circuit_breaker.json
   ```
   If `"engaged": true`, the bot has stopped trading due to performance issues.

### If Doctor/Heartbeat is Stale:

1. **Check if heartbeat-keeper is running:**
   ```bash
   process-compose ps | grep heartbeat
   ```

2. **Restart heartbeat-keeper if needed:**
   ```bash
   process-compose restart heartbeat-keeper
   ```

3. **Check for errors:**
   ```bash
   tail -50 logs/heartbeat-keeper-pc.log
   ```

## Normal Behavior

### During Market Hours:
- Last order should be < 1 hour old if bot is actively trading
- Doctor should be < 5 minutes old
- Signals should be generated regularly (check `logs/signals.jsonl`)

### Outside Market Hours:
- Last order can be hours/days old (normal)
- Doctor should still be < 5 minutes (heartbeat should continue)
- No new trades should execute

## Quick Health Check Command

Run this to get a quick overview:
```bash
echo "=== Health ===" && \
curl -s http://localhost:8081/health | python -m json.tool && \
echo -e "\n=== Last Order ===" && \
tail -1 data/live_orders.jsonl 2>/dev/null | python -m json.tool | grep -E "_ts|event|symbol" && \
echo -e "\n=== Heartbeat ===" && \
cat state/system_heartbeat.json 2>/dev/null | python -m json.tool | grep -E "timestamp|_ts"
```

## Summary

**Your current status:**
- Last order: 3 hours old - Check if market is open and if bot is generating signals
- Doctor: 50 minutes - This is in the warning range but not critical yet

**Action items:**
1. Check if market is currently open
2. Verify the bot is running: `process-compose ps`
3. Check for errors in logs
4. Verify Alpaca account is active and not blocked
5. Check if signals are being generated

If everything checks out and the market is closed or there are no trading opportunities, the yellow indicators are likely just warnings and not actual problems.
