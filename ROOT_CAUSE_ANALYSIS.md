# Root Cause Analysis - Execution Bridge Failure

## Status: ✅ ROOT CAUSE IDENTIFIED

## The Problem

**User Report:** ZERO trades in Alpaca portal, but logs claim trades are executing.

## Root Cause: "client_order_id must be unique" Error

### Error Details from `logs/critical_api_failure.log`:

```
Status Code: 422
Error: "client_order_id must be unique"
Error Code: 40010001
```

### What's Happening:

1. **Orders ARE being submitted to Alpaca** ✅
2. **Alpaca REJECTS them** because `client_order_id` is not unique ❌
3. **Bot retries with SAME client_order_id** ❌
4. **Alpaca rejects again** (same ID) ❌
5. **Loop continues** - orders never succeed ❌

### Example from Logs:

```
Symbol: IWM, Side: sell
Client Order ID: "uwbot-IWM-sell-1767387515-lpo-a1"
Attempt: 1
Error: "client_order_id must be unique"
Status: 422

Then retries with SAME client_order_id multiple times - all rejected
```

### Why This Happens:

1. **First submission** with `client_order_id` fails (network error, timeout, etc.)
2. **Alpaca remembers** the `client_order_id` was used (even if order failed)
3. **Bot retries** with the SAME `client_order_id` 
4. **Alpaca rejects** - "client_order_id must be unique"
5. **Retry loop continues** with same ID

### The Fix Needed:

1. **Generate NEW client_order_id for each retry attempt** (not just append suffix)
2. **OR check if order exists** before retrying (code already has `_get_order_by_client_order_id` but may not be working)
3. **OR use timestamp/random component** to ensure uniqueness

### Current Code Issue:

The code generates client_order_id like:
- Base: `uwbot-IWM-sell-1767387515`
- Retry suffix: `-lpo-a1`, `-lpo-a2`, `-lpo-a3`

But the base ID uses a timestamp (`1767387515`) which is the same for all retries of the same signal, causing collisions.

### Next Steps:

1. Fix client_order_id generation to include retry attempt in base ID
2. OR ensure retry logic properly checks for existing orders
3. OR use UUID/random component for uniqueness

---

**Status:** Root cause identified. Fix needed for client_order_id generation/retry logic.
