# FINAL ROOT CAUSE AND FIX
**Date:** 2026-01-13  
**Status:** 🔧 **IN PROGRESS**

---

## Problem

1. ❌ **V position at -1.83% not closing** (stop loss -1.0% should trigger)
2. ❌ **No new trades** (concentration gate blocking)
3. ❌ **`evaluate_exits()` not being called**

---

## Root Cause

**`run_once()` is being called but NOT completing.**

Evidence:
- ✅ "About to call run_once()" appears in logs
- ❌ "decide_and_execute returned" does NOT appear
- ❌ "Calling evaluate_exits" does NOT appear
- ❌ "RUN_ONCE COMPLETE" does NOT appear

**This means `run_once()` is crashing/hanging before reaching `evaluate_exits()`.**

---

## Fixes Applied

1. ✅ Added entry logging to `run_once()` to trace execution path
2. ✅ Added logging before `evaluate_exits()` call
3. ✅ Added force check for `engine.executor.evaluate_exits()` availability
4. ✅ Added comprehensive position evaluation logging
5. ✅ Fixed `evaluate_exits()` to check ALL positions from Alpaca API
6. ✅ Fixed P&L calculation to use Alpaca's `unrealized_plpc` directly

---

## Next Steps

1. Wait for next cycle and check `logs/worker_debug.log` for:
   - "run_once() ENTRY"
   - "run_once() inside try block"
   - "run_once() creating UWClient and engine"
   - "decide_and_execute returned"
   - "About to call evaluate_exits()"
   - "Calling evaluate_exits()"
   - "EVALUATING V"
   - "STOP LOSS HIT: V"

2. If execution stops before any of these, that's where the crash/hang is happening.

---

**Status:** Logging deployed. Waiting for execution trace to identify where `run_once()` stops.
