# Execution Bridge Audit & Truth Verification

## Critical Issue

**User Report:** ZERO trades in Alpaca portal, but logs claim trades are executing.

**This is a CRITICAL FAILURE of the execution bridge.**

## Diagnostic Requirements Applied

### 1. ✅ Added Comprehensive Error Logging to submit_order Calls

**Changes Made:**
- Added RAW API error response logging to all `submit_order` exception handlers
- Created dedicated log file: `logs/critical_api_failure.log`
- Captures:
  - HTTP status codes (400, 401, 403, etc.)
  - Response body (RAW JSON from Alpaca)
  - Exception types and messages
  - Order construction parameters (qty, side, symbol, limit_price)

**Locations Modified:**
- Line ~3239: Limit order retry exception handler
- Line ~3325: Limit order final exception handler  
- Line ~3394: Market order exception handler
- Line ~3208: Order submission with no ID detection
- Line ~3296: Final limit order with no ID detection
- Line ~3374: Market order with no ID detection

### 2. Order Object Construction Validation

**Current Validation:**
- Line 3111: `notional = qty * ref_price` - validates notional >= MIN_NOTIONAL_USD
- Line 3112-3116: Blocks if notional < MIN_NOTIONAL_USD
- Line 3093-3096: Blocks if ref_price <= 0

**Potential Issues:**
- If `qty` is 0 or NaN, order will be rejected
- If `ref_price` is stale/invalid, calculated qty may be wrong

### 3. Process Collisions Check

**From Process List:**
- PID 1033018: `python main.py` (trading bot)
- PID 1033010: `python -u dashboard.py` (dashboard)
- PID 1033016: `python uw_flow_daemon.py` (UW daemon)
- PID 1033030: `python heartbeat_keeper.py` (health monitor)

**Analysis:**
- Only ONE instance of `main.py` running (PID 1033018)
- No duplicate trading bot processes detected
- Multiple processes but they serve different purposes

### 4. API Endpoint Verification

**Status:** PENDING - Need to verify actual API URL in running process

## Next Steps

1. **Deploy Error Logging:** Push changes to droplet
2. **Monitor `logs/critical_api_failure.log`:** This will show RAW Alpaca API errors
3. **Verify API Endpoints:** Check if paper URL is being used with live keys (or vice versa)
4. **Check Order Construction:** Verify qty calculations are correct

## Expected Output

After deployment, `logs/critical_api_failure.log` will contain entries like:

```
2026-01-05T18:30:00+00:00 | limit_retry_failed | {"symbol": "AAPL", "qty": 10, "side": "buy", "status_code": 403, "response_json": {"code": 40310000, "message": "insufficient buying power"}}
```

This will reveal WHY Alpaca is rejecting the orders.
