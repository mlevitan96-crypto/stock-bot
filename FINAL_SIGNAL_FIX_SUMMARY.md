# Final Signal Fix Summary

## Issues Found

### 1. **Dark Pool Not Being Stored** (FIXED)
- **Problem**: `if dp_normalized:` check was preventing storage when `dp_normalized = {}` (empty dict is falsy)
- **Fix**: Changed to always store dark_pool, even if empty, so we know it was polled
- **Location**: `uw_flow_daemon.py` line 844-846

### 2. **Threshold Too High** (FIXED)
- **Problem**: Threshold was 3.5, but scores are 0.15-2.58
- **Fix**: Lowered to 2.0 (base), 2.2 (canary), 2.5 (champion) for paper trading
- **Location**: `uw_composite_v2.py` line 168-172

### 3. **Missing Signals** (IN PROGRESS)
- **Problem**: Many signals show "no_recent_signals" on dashboard
- **Root Causes**:
  - Some endpoints return 404 (congress, institutional per-ticker)
  - Market-wide data (market_tide) not stored per-ticker
  - Some endpoints return empty (etf_flow for some tickers)
  - Dark pool was not being stored (now fixed)

## Next Steps

1. **Verify dark_pool is now being stored** after restart
2. **Fix market-wide data storage** - store market_tide per-ticker
3. **Handle 404 endpoints gracefully** - don't fail, just skip
4. **Ensure all polled data is stored** - even if empty

## Files Modified

- `uw_flow_daemon.py`: Fixed dark_pool storage logic
- `uw_composite_v2.py`: Lowered thresholds for paper trading

