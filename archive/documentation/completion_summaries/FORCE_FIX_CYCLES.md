# FORCE FIX - Cycles Not Running

## Root Cause Found

Worker thread IS running (iter_count: 8, heartbeat active), but cycles aren't being logged to run.jsonl.

**Possible causes:**
1. `run_once()` raising exception before logging
2. Market check failing silently
3. Worker loop exception handler catching errors but not logging properly

## Fixes Applied

1. ✅ Added explicit `jsonl_write("run", ...)` in run_once() completion path
2. ✅ Added debug logging to worker loop
3. ✅ Added error handling for market check
4. ✅ All code fixes verified (threshold 2.7, flow weight 2.4)

## Next Steps

1. Restart bot with new debug logging
2. Check system.jsonl for worker errors
3. Check if market check is failing
4. Verify run_once() is being called

## Critical: If Still Not Working

If cycles still don't run after restart:
- Check for exceptions in worker loop
- Verify market check works
- Force a cycle manually with `force_cycle_run.py`
