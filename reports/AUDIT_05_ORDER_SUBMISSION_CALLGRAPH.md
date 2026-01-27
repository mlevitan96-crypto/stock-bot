# Order Submission Call Graph

**Generated:** 2026-01-27

## Direct API Calls (Lowest Layer)

All order submissions ultimately call `self.api.submit_order()` where `self.api` is `tradeapi.REST` (Alpaca client).

### Call Sites in main.py

1. **Line 4099** - `AlpacaExecutor.submit_entry()` - Limit order with backoff retry
   - Context: Inside `submit_entry`, after `AUDIT_DRY_RUN` check (line 4051)
   - Guard: Has `AUDIT_DRY_RUN` check but may be bypassed
   - Logs: Uses `log_order()` for audit_dry_run

2. **Line 4257** - `AlpacaExecutor.submit_entry()` - Limit order fallback path
   - Context: Inside `submit_entry`, after POST_ONLY retry loop
   - Guard: **MISSING** - No audit guard
   - Logs: Uses `log_order()` for real orders

3. **Line 4403** - `AlpacaExecutor.submit_entry()` - Market order fallback
   - Context: Inside `submit_entry`, market order path
   - Guard: **MISSING** - No audit guard
   - Logs: Uses `log_order()` for real orders

4. **Line 5333** - `AlpacaExecutor._scale_out_partial()` - Scale out partial position
   - Context: Exit logic, partial position close
   - Guard: **MISSING** - No audit guard
   - Logs: Uses `log_order()` for scale_out

5. **Line 5347** - `AlpacaExecutor.market_buy()` - Market buy helper
   - Context: Direct market buy
   - Guard: **MISSING** - No audit guard
   - Logs: **MISSING** - No logging

6. **Line 5350** - `AlpacaExecutor.market_sell()` - Market sell helper
   - Context: Direct market sell
   - Guard: **MISSING** - No audit guard
   - Logs: **MISSING** - No logging

### Call Sites in alpaca_client.py

7. **Line 294** - `AlpacaClient.submit_order()` - Wrapper with retry logic
   - Context: Wrapper around `self.api.submit_order()`
   - Guard: **MISSING** - No audit guard
   - Logs: **MISSING** - No logging
   - Note: May not be used if main.py calls API directly

## Close Position Calls

- `self.api.close_position()` - Multiple call sites
  - Guard: Has `AUDIT_DRY_RUN` check in `close_position_with_retries` and `close_position_api_once`
  - Status: **PARTIALLY GUARDED**

## Current Guard Status

- **submit_entry**: Has `AUDIT_DRY_RUN` check at line 4051, but:
  - Check may not be reached if early returns occur
  - Fallback paths (lines 4257, 4403) bypass the check
  - No explicit logging of which branch was taken

- **Other paths**: No guards at all

## Required Fix

1. Add guard at lowest layer (wrap `self.api.submit_order` calls)
2. Add guard in `alpaca_client.py` if used
3. Add explicit logging in `submit_entry` to prove branch taken
4. Ensure all paths go through guard
