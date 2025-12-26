# Unusual Whales API Endpoint Verification

**Date:** 2025-12-26  
**Purpose:** Verify all UW API endpoints are correct per official documentation  
**Reference:** https://api.unusualwhales.com/docs#/ and https://unusualwhales.com/information/how-to-fix-404-errors-when-using-ai-tools-with-the-unusual-whales-api

## Current Endpoints in Code

### ✅ VERIFIED WORKING (from logs)
1. `/api/option-trades/flow-alerts` - ✅ Working (returns data)
2. `/api/darkpool/{ticker}` - ✅ Working (returns data, status 200)
3. `/api/stock/{ticker}/greeks` - ✅ Working (returns data)
4. `/api/stock/{ticker}/greek-exposure` - ✅ Working
5. `/api/market/top-net-impact` - ✅ Working
6. `/api/market/market-tide` - ✅ Working (returns data)
7. `/api/stock/{ticker}/iv-rank` - ✅ Working (returns data)
8. `/api/insider/{ticker}` - ✅ Working (returns data)
9. `/api/stock/{ticker}/max-pain` - ✅ Working (returns data)
10. `/api/stock/{ticker}/oi-change` - ✅ Working (returns data)

### ❌ VERIFIED NOT WORKING (404 errors from logs)
1. `/api/congress/{ticker}` - ❌ 404 NOT FOUND (per-ticker endpoint doesn't exist)
2. `/api/institutional/{ticker}` - ❌ 404 NOT FOUND (per-ticker endpoint doesn't exist)

### ⚠️ NEEDS VERIFICATION
1. `/api/etfs/{ticker}/in-outflow` - Returns 200 but empty data (may be expected for some tickers)
2. `/api/calendar/{ticker}` - Returns 200 but empty data (may be expected)
3. `/api/shorts/{ticker}/ftds` - Need to verify

## Fixes Required

### 1. Congress Endpoint
**Current:** `/api/congress/{ticker}` (404)  
**Action:** Remove per-ticker congress polling OR find correct endpoint  
**Note:** Congress data may be market-wide only, not per-ticker

### 2. Institutional Endpoint  
**Current:** `/api/institutional/{ticker}` (404)  
**Action:** Remove per-ticker institutional polling OR find correct endpoint  
**Note:** Institutional data may be market-wide only, not per-ticker

### 3. ETF Flow
**Current:** `/api/etfs/{ticker}/in-outflow` (200 but empty)  
**Action:** Verify this is correct endpoint - may return empty for non-ETF tickers  
**Note:** This endpoint may only work for ETF symbols, not individual stocks

## Next Steps

1. Test alternative endpoints for congress/institutional
2. Verify ETF flow endpoint is correct
3. Update code to remove 404 endpoints
4. Document correct endpoints in code comments
5. Update all documentation files

