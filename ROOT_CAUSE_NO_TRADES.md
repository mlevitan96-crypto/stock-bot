# ROOT CAUSE: No Trades Executing

## Date: 2026-01-05

## CRITICAL FINDING

**BLOCKER IDENTIFIED: NO_RUN_ONCE**

The diagnostic script revealed:
- **run_once calls: 0** - The bot loop is NOT running
- Signals: 3717 total (signals are being generated)
- Orders: 38 total (last one at 14:32:20 UTC)
- Freeze state: OK (not frozen)
- Trading armed: OK (no blocks)

## The Problem

**The `run_once()` function is not being called.** This means:
1. The main trading loop is not executing
2. No new signals are being processed
3. No new orders are being placed
4. The bot is essentially idle

## Why This Matters

`run_once()` is the core function that:
- Reads UW cache/API data
- Clusters signals
- Runs composite scoring
- Calls `decide_and_execute()`
- Submits orders

**Without `run_once()` running, the entire trading workflow is stopped.**

## Next Steps to Fix

1. **Check if main.py process is running**
   ```bash
   pgrep -f python.*main.py
   ```

2. **Check service status**
   ```bash
   systemctl status trading-bot.service
   ```

3. **Check service logs**
   ```bash
   journalctl -u trading-bot.service -n 100
   ```

4. **Check if main.py has a main loop**
   - Look for `if __name__ == "__main__"`
   - Check for watchdog/main loop code
   - Verify service is calling the correct entry point

5. **Check recent system logs**
   - Look for errors or crashes
   - Check if process exited
   - Verify process is actually running

## Expected Behavior

`run_once()` should be called:
- Every `RUN_INTERVAL_SEC` (default: 60 seconds)
- By the main loop or watchdog
- Logged to `logs/system.jsonl` with "run_once" in the message

## Status

**ROOT CAUSE IDENTIFIED: Bot loop not running**
**NEXT ACTION: Investigate why run_once() is not being called**
