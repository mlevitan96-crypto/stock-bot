# Graceful Degradation Fix - Trading Continues During Rate Limits

## Problem Identified

**Single Point of Failure**: When UW API rate limit is hit (429), the entire trading bot stops because:
- Daemon stops polling (no new data)
- Trading bot sees empty cache
- Bot skips trading completely

**Impact**: One API issue (rate limit) takes out the entire trading system.

## Solution: Graceful Degradation

### What Changed

1. **Trading Bot Now Uses Stale Cache**
   - If cache data is < 2 hours old, use it for trading
   - Allows trading to continue even when API is rate limited
   - Only skips trading if cache is completely empty or > 2 hours old

2. **Daemon Preserves Cache on Rate Limit**
   - When rate limited, daemon stops making NEW API calls
   - But does NOT clear existing cache data
   - Cache remains available for trading bot to use

3. **Better Logging**
   - Daemon logs status periodically when rate limited
   - Trading bot logs when using stale cache
   - Clear indication of graceful degradation mode

## How It Works

### Normal Operation (API Working)
1. Daemon polls API every 2.5 minutes
2. Fresh data stored in cache
3. Trading bot uses fresh data

### Rate Limited (API Blocked)
1. Daemon detects 429, stops new polling
2. **Cache data preserved** (not cleared)
3. Trading bot checks cache age:
   - **< 2 hours old**: Use stale cache, continue trading ✅
   - **> 2 hours old**: Skip trading (data too stale) ⚠️
   - **No cache**: Skip trading (no data available) ❌

### After Reset (8PM EST)
1. Daemon auto-resumes polling
2. Fresh data flows again
3. Trading bot uses fresh data

## Benefits

✅ **Resilience**: Trading continues with cached data during rate limits
✅ **No Single Point of Failure**: API issue doesn't kill entire bot
✅ **Smart Degradation**: Only uses data < 2 hours old (still relevant)
✅ **Automatic Recovery**: Resumes fresh data after limit resets

## Configuration

**Stale Data Threshold**: 2 hours (configurable)
- Data < 2 hours old: Considered usable
- Data > 2 hours old: Too stale, skip trading

This threshold balances:
- Data freshness (2 hours is reasonable for options flow)
- Resilience (allows trading during temporary API issues)

## Monitoring

Check logs for:
- `✅ Using stale cache for TICKER (age: X min)` - Graceful degradation active
- `⚠️  No usable stale cache - skipping trading` - Cache too old or empty
- `[UW-DAEMON] ⏳ Rate limited - monitoring for reset` - Daemon waiting for reset

## Expected Behavior

**During Rate Limit:**
- Daemon: Stops polling, preserves cache
- Trading Bot: Uses stale cache if < 2 hours old
- Result: Trading continues with last known good data ✅

**After Rate Limit Resets:**
- Daemon: Auto-resumes, gets fresh data
- Trading Bot: Uses fresh data
- Result: Normal operation resumes ✅

## Deployment

The fix is already in the code. After pulling and restarting:

```bash
cd /root/stock-bot
git pull origin main --no-rebase
pkill -f deploy_supervisor
source venv/bin/activate
venv/bin/python deploy_supervisor.py
```

## Testing

After deployment, when rate limit is hit:
1. Check trading bot logs for "Using stale cache" messages
2. Verify trades can still be placed (if cache < 2 hours old)
3. Verify daemon preserves cache (doesn't clear it)
