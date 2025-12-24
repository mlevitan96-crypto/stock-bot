# UW Daemon Endpoint Fixes

## Issues Identified and Fixed

### 1. **Missing Immediate First Poll**
**Problem**: New endpoints weren't being polled immediately on daemon startup - had to wait for polling intervals (5-60 minutes).

**Fix**: 
- Added `force_first` parameter to `should_poll()` method
- Added `first_poll` flag in `run()` method to force market-wide endpoints (`market_tide`, `top_net_impact`) to poll immediately on startup
- Logs when first poll cycle completes

### 2. **Insufficient Logging**
**Problem**: When endpoints returned empty data or errors occurred, there was minimal logging, making it hard to debug.

**Fix**:
- Added "Polling..." messages before each endpoint call
- Added data size logging when data is successfully retrieved
- Added full traceback logging on errors
- Added detailed logging for empty responses (shows what keys are present for debugging)

### 3. **Better Error Visibility**
**Problem**: Errors were being caught but not fully logged.

**Fix**:
- All endpoint polling now includes full traceback on exceptions
- Shows response keys when data structure doesn't match expectations (e.g., max_pain)

## Changes Made

### `uw_flow_daemon.py`

1. **`SmartPoller.should_poll()` method**:
   - Added `force_first` parameter to allow immediate first poll
   - If `force_first=True` and no previous poll recorded, allows immediate poll

2. **`UWFlowDaemon.run()` method**:
   - Added `first_poll` flag
   - Market-wide endpoints (`market_tide`, `top_net_impact`) use `force_first=first_poll` on first cycle
   - Logs completion of first poll cycle

3. **All endpoint polling sections**:
   - Added "Polling..." log message before API call
   - Added data size/field count logging on success
   - Added full traceback on exceptions
   - Enhanced empty response logging

## Expected Behavior After Fix

1. **On Startup**:
   - Market-wide endpoints (`market_tide`, `top_net_impact`) poll immediately
   - Per-ticker endpoints poll on their first interval (15-60 minutes)

2. **Logging**:
   - Clear visibility into which endpoints are being polled
   - Clear visibility into API responses (success, empty, or error)
   - Full error details for debugging

3. **Cache Population**:
   - Market-wide data appears within seconds of startup
   - Per-ticker data appears within 15-60 minutes (based on polling intervals)

## Next Steps

1. **Restart UW daemon** with updated code:
   ```bash
   pkill -f "uw.*daemon|uw_flow_daemon"
   cd ~/stock-bot
   source venv/bin/activate
   nohup python3 uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &
   ```

2. **Monitor logs** for endpoint activity:
   ```bash
   tail -f logs/uw_daemon.log | grep -E "Polling|Updated|Error|market_tide|oi_change|etf_flow"
   ```

3. **Verify endpoints** are working:
   ```bash
   ./VERIFY_ALL_ENDPOINTS.sh
   ```

## Polling Intervals

- `market_tide`: 5 min (polls immediately on startup)
- `top_net_impact`: 5 min (polls immediately on startup)
- `oi_change`: 15 min
- `max_pain`: 15 min
- `greek_exposure`: 30 min
- `greeks`: 30 min
- `etf_flow`: 30 min
- `iv_rank`: 30 min
- `shorts_ftds`: 60 min
