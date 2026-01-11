# UW Daemon Missing Endpoints Fix

## Problem Identified

The UW daemon (`uw_flow_daemon.py`) is only fetching 4 endpoints, but `config/uw_signal_contracts.py` defines 7 endpoints that should be fetched.

### Currently Fetched (in `uw_flow_daemon.py`):
1. ✅ `/api/option-trades/flow-alerts` - Option flow
2. ✅ `/api/darkpool/{ticker}` - Dark pool
3. ⚠️ `/api/stock/{ticker}/greeks` - Greeks (WRONG endpoint - should be `/greek-exposure`)
4. ✅ `/api/market/top-net-impact` - Top net impact

### Missing Endpoints (defined in `config/uw_signal_contracts.py`):
1. ❌ `/api/market/market-tide` → `market_tide` signal
2. ❌ `/api/stock/{ticker}/oi-change` → `oi_change` signal
3. ❌ `/api/etfs/{ticker}/in-outflow` → `etf_flow` signal
4. ❌ `/api/stock/{ticker}/iv-rank` → `iv_rank` signal
5. ❌ `/api/shorts/{ticker}/ftds` → `ftd_pressure` signal
6. ❌ `/api/stock/{ticker}/max-pain` → `greeks_gamma` signal (additional data)

### Wrong Endpoint:
- Currently using: `/api/stock/{ticker}/greeks`
- Should use: `/api/stock/{ticker}/greek-exposure` (per contract)

## Impact

This is why enriched signals show "no data" in the cache:
- `market_tide`: Not fetched
- `etf_flow`: Not fetched
- `oi_change`: Not fetched
- `iv_rank`: Not fetched
- `ftd_pressure`: Not fetched
- `greeks_gamma`: Using wrong endpoint, may not have correct data structure

## Solution

Update `uw_flow_daemon.py` to:
1. Add methods to fetch all missing endpoints
2. Fix greeks endpoint to use `/greek-exposure`
3. Store data in cache using the correct keys per `uw_signal_contracts.py`
4. Add polling intervals to `SmartPoller` for new endpoints

## Implementation Plan

1. Add client methods for each missing endpoint
2. Add polling logic in `_poll_ticker()` method
3. Update `SmartPoller` intervals for new endpoints
4. Map response fields using `translate_response_fields()` from contracts
5. Store in cache with correct keys

## Rate Limit Considerations

Per `API_ENDPOINT_ANALYSIS.md`:
- Current usage: ~13,000 calls/day
- Limit: 15,000 calls/day
- Need to add polling intervals that don't exceed limit

Recommended intervals:
- `market_tide`: Every 5 minutes (market-wide, not per-ticker)
- `oi_change`: Every 15 minutes per ticker
- `etf_flow`: Every 30 minutes per ticker
- `iv_rank`: Every 30 minutes per ticker
- `shorts_ftds`: Every 60 minutes per ticker
- `max_pain`: Every 15 minutes per ticker
