# Unusual Whales API Endpoints - Official Documentation

**Last Updated:** 2025-12-26  
**Reference:** https://api.unusualwhales.com/docs#/  
**404 Error Guide:** https://unusualwhales.com/information/how-to-fix-404-errors-when-using-ai-tools-with-the-unusual-whales-api

## ✅ VERIFIED WORKING ENDPOINTS

All endpoints below have been verified to return status 200 and contain data.

### Core Trading Signals
1. **Option Flow Alerts**
   - Endpoint: `/api/option-trades/flow-alerts`
   - Params: `symbol={ticker}`, `limit={number}`
   - Returns: List of option trades
   - Status: ✅ WORKING

2. **Dark Pool Levels**
   - Endpoint: `/api/darkpool/{ticker}`
   - Returns: List of dark pool prints
   - Fields: `price`, `lit_volume`, `off_lit_volume`, `total_volume`, `side`, `timestamp`
   - Status: ✅ WORKING
   - **FIXED:** Normalization now uses actual fields (volume/price) instead of non-existent "premium"

3. **Greeks**
   - Endpoint: `/api/stock/{ticker}/greeks`
   - Returns: Greek exposure data
   - Status: ✅ WORKING

4. **Greek Exposure (Detailed)**
   - Endpoint: `/api/stock/{ticker}/greek-exposure`
   - Returns: Detailed gamma/delta exposure
   - Status: ✅ WORKING

5. **Max Pain**
   - Endpoint: `/api/stock/{ticker}/max-pain`
   - Returns: Max pain strike price
   - Status: ✅ WORKING

### Market-Wide Data
6. **Top Net Impact**
   - Endpoint: `/api/market/top-net-impact`
   - Params: `limit={number}`
   - Returns: Top symbols by net impact
   - Status: ✅ WORKING

7. **Market Tide**
   - Endpoint: `/api/market/market-tide`
   - Returns: Market-wide options sentiment
   - Fields: `net_call_premium`, `net_put_premium`, `net_volume`, `timestamp`, `date`
   - Status: ✅ WORKING
   - **FIXED:** Now stored per-ticker for scoring access

### Stock-Specific Data
8. **IV Rank**
   - Endpoint: `/api/stock/{ticker}/iv-rank`
   - Returns: Implied volatility rank
   - Status: ✅ WORKING

9. **Open Interest Change**
   - Endpoint: `/api/stock/{ticker}/oi-change`
   - Returns: Open interest delta changes
   - Status: ✅ WORKING

10. **Insider Trading**
    - Endpoint: `/api/insider/{ticker}`
    - Returns: Insider trading activity
    - Status: ✅ WORKING

11. **Shorts/FTDs**
    - Endpoint: `/api/shorts/{ticker}/ftds`
    - Returns: Fails-to-deliver data
    - Status: ✅ WORKING

### ETF Data
12. **ETF Flow**
    - Endpoint: `/api/etfs/{ticker}/in-outflow`
    - Returns: ETF inflow/outflow (may be empty for non-ETF tickers)
    - Status: ⚠️ Returns 200 but may be empty (expected for non-ETF symbols)

### Calendar/Events
13. **Calendar Events**
    - Endpoint: `/api/calendar/{ticker}`
    - Returns: Earnings dates, events (may be empty if no events)
    - Status: ⚠️ Returns 200 but may be empty (expected if no events)

## ❌ ENDPOINTS THAT DON'T EXIST (404)

These endpoints return 404 and should NOT be used:

1. **Congress (Per-Ticker)**
   - Attempted: `/api/congress/{ticker}`
   - Status: ❌ 404 NOT FOUND
   - **Action:** Removed from active polling (returns empty gracefully)
   - **Note:** Congress data may be market-wide only, not per-ticker

2. **Institutional (Per-Ticker)**
   - Attempted: `/api/institutional/{ticker}`
   - Status: ❌ 404 NOT FOUND
   - **Action:** Removed from active polling (returns empty gracefully)
   - **Note:** Institutional data may be market-wide only, not per-ticker

## Implementation Notes

### Dark Pool Normalization
**FIXED:** The dark pool API returns volume/price data, not premium. Normalization now:
- Uses `price`, `off_lit_volume`, `total_volume`, `side` fields
- Calculates notional value (volume × price) as proxy for premium
- Tracks buy/sell volume for sentiment

### Market Tide Storage
**FIXED:** Market tide is now stored both:
- Globally in `_market_tide` metadata
- Per-ticker for scoring access

### Error Handling
All endpoints now:
- Handle 404 gracefully (return empty dict)
- Log errors for debugging
- Never mask errors - fix root causes

## Rate Limits

- **Daily Limit:** 15,000 calls/day
- **Per-Minute:** ~120 calls/min (varies by endpoint)
- **Implementation:** Token bucket algorithm in `api_management/token_bucket.py`

## Data Flow

1. **UW Flow Daemon** (`uw_flow_daemon.py`) polls endpoints
2. **Smart Poller** manages intervals to stay under limits
3. **Normalization** converts API responses to standard format
4. **Cache Storage** (`data/uw_flow_cache.json`) stores per-ticker data
5. **Main Bot** (`main.py`) reads cache for scoring

## Verification Status

- ✅ All working endpoints verified
- ✅ 404 endpoints identified and handled
- ✅ Normalization functions use actual API fields
- ✅ Documentation updated with correct endpoints
- ✅ Error handling prevents masking issues

