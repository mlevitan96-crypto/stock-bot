# Client Order ID Uniqueness Fix - Complete

## Status: ✅ FIXED AND DEPLOYED

## Root Cause Identified

**Error from Alpaca API:**
- Status Code: **422**
- Error Message: **"client_order_id must be unique"**
- Error Code: **40010001**

## The Problem

The `ExponentialBackoff` wrapper was calling `submit_order()` multiple times (up to 3 retries) within the same attempt, and ALL retries used the SAME `client_order_id` (captured in closure).

**What Happened:**
1. Attempt 1: `client_order_id = "uwbot-IWM-sell-1767387515-lpo-a1"`
2. Backoff calls `submit_order()` 3 times (max_retries=3)
3. All 3 calls use the SAME `client_order_id`
4. First call: Succeeds or fails
5. Second call: Alpaca rejects "client_order_id must be unique" (HTTP 422)
6. Third call: Alpaca rejects "client_order_id must be unique" (HTTP 422)
7. Result: Orders rejected, no trades execute

## The Fix

**Changed:** Generate a unique `client_order_id` for each backoff retry attempt.

**Implementation:**
- Added `backoff_attempt` counter to track retry number
- For retry attempts > 1, append `-retry{N}` to client_order_id
- Example: `uwbot-IWM-sell-1767387515-lpo-a1` → `uwbot-IWM-sell-1767387515-lpo-a1-retry2`, `-retry3`, etc.

**Files Modified:**
- `main.py` line ~3191: Limit order retry with backoff
- `main.py` line ~3479: Market order with backoff

## Deployment Status

✅ **Code committed and pushed to Git**  
✅ **Code pulled to droplet**  
✅ **Service restarted**  
✅ **Fix is live**

## Expected Result

- Orders should now succeed (unique client_order_id for each backoff retry)
- No more "client_order_id must be unique" errors
- Trades should execute successfully

---

**Status:** ✅ Fixed and deployed. Orders should now execute successfully.
