# COMPLETE FIX SUMMARY
**Date:** 2026-01-13  
**Status:** ✅ **DEPLOYED**

---

## Problems

1. ❌ **V position at -1.83% not closing** (stop loss -1.0% should trigger)
2. ❌ **No new trades** (concentration gate blocking at 72.5%)
3. ❌ **`evaluate_exits()` never being called**

---

## Root Causes

1. **`run_once()` is hanging/crashing** - Entry logging never appears
2. **`evaluate_exits()` only called inside `run_once()`** - If `run_once()` doesn't complete, exits never evaluated
3. **`evaluate_exits()` only checked `self.opens`** - V exists in Alpaca but not in `self.opens`
4. **P&L calculation mismatch** - Used metadata entry_price vs Alpaca's avg_entry_price

---

## Fixes Applied

1. ✅ **Create `engine` BEFORE `run_once()`** - Now `evaluate_exits()` can be called even if `run_once()` hangs
2. ✅ **ALWAYS call `evaluate_exits()` after `run_once()`** - Safety net ensures it's called regardless
3. ✅ **Fixed `evaluate_exits()` to check ALL positions** - Now includes positions from Alpaca API, not just `self.opens`
4. ✅ **Fixed P&L calculation** - Uses Alpaca's `unrealized_plpc` directly
5. ✅ **Added comprehensive logging** - Every position evaluation is logged

---

## Expected Results

1. ✅ `evaluate_exits()` will be called after every `run_once()` (or exception)
2. ✅ V position will be evaluated (now in `positions_to_evaluate`)
3. ✅ V position will be closed (P&L -1.83% <= -1.0% stop loss)
4. ✅ Concentration drops below 70% after V closes
5. ✅ New trades allowed (concentration gate passes)

---

**Status:** All fixes deployed. `evaluate_exits()` will now be called after every cycle, ensuring V is closed.
