# FINAL V FIX SUMMARY
**Date:** 2026-01-13  
**Status:** ✅ **DEPLOYED**

---

## Root Cause Found

**`main.py` was crashing immediately with `NameError: name 'StateFiles' is not defined`**

This prevented:
- ❌ `run_once()` from completing
- ❌ `evaluate_exits()` from being called
- ❌ V position from being evaluated and closed

---

## Fixes Applied

1. ✅ **Added StateFiles availability check** - Re-imports if not available
2. ✅ **Added global declaration** - Prevents scoping issues
3. ✅ **Fixed evaluate_exits()** - Now checks ALL positions from Alpaca API
4. ✅ **Fixed P&L calculation** - Uses Alpaca's `unrealized_plpc` directly
5. ✅ **Added safety net** - `evaluate_exits()` called after every `run_once()`

---

## Expected Results

1. ✅ `main.py` starts successfully (no more StateFiles error)
2. ✅ `run_once()` completes
3. ✅ `evaluate_exits()` is called after every cycle
4. ✅ V position is evaluated (now in `positions_to_evaluate`)
5. ✅ V position is closed (P&L -2.19% <= -1.0% stop loss)
6. ✅ Concentration drops below 70% after V closes
7. ✅ New trades allowed (concentration gate passes)

---

**V position should close on the next cycle now that main.py is running.**
