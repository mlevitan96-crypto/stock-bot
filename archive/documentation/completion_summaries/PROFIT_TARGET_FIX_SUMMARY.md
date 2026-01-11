# Profit Target Fix Summary

## Problem Identified
Diagnostic showed: **"Profit targets: NOT FOUND"** - No profit target exits found in recent exits.

## Root Cause
1. **Targets not persisted**: `_persist_position_metadata()` didn't save `targets` to metadata
2. **Targets lost on reload**: When positions reloaded from metadata, targets were re-initialized fresh (all "hit": False)
3. **State not preserved**: If a target was hit before reload, that state was lost

## Fix Applied

### 1. Persist Targets to Metadata
**Location**: `_persist_position_metadata()` (line ~3443)
- Now saves `targets` to metadata if position is already open
- Preserves "hit" state across restarts

### 2. Restore Targets on Reload
**Location**: `reload_positions_from_metadata()` (line ~3492, ~3514)
- Restores targets from metadata if available
- Preserves "hit" state
- Only re-initializes if targets missing

### 3. Re-initialize if Missing
**Location**: `evaluate_exits()` (line ~3704)
- Checks if targets exist before checking profit targets
- Re-initializes if missing (defensive)
- Logs when re-initialization occurs

### 4. Update Metadata When Target Hit
**Location**: `evaluate_exits()` (line ~3706)
- Updates metadata immediately when target is hit
- Ensures state is preserved even if bot restarts

## Expected Behavior After Fix

1. **Targets persist across restarts**: Targets and their "hit" state are preserved
2. **Profit targets trigger**: When position hits 2%, 5%, or 10%, scale-out occurs
3. **State preserved**: If position hits 2% target, that state is saved and won't trigger again

## Verification

After deployment, check:
```bash
# Check if targets are in metadata
cat state/position_metadata.json | python3 -m json.tool | grep -A 10 targets

# Check recent exits for profit targets
tail -100 logs/exit.jsonl | grep profit_target

# Run diagnostic again
python3 diagnose_learning_and_exits.py
```

## Additional Notes

**Why profit targets weren't triggering before:**
- Most exits showed "time_or_trail" - positions closing via time exits (4 hours) or stops before hitting 2% profit
- This is actually normal behavior if positions aren't profitable
- However, the fix ensures that when positions DO become profitable, profit targets will trigger correctly

**Next Steps:**
1. Monitor for profit target exits after fix
2. Consider adjusting time exits if positions need more time to reach profit targets
3. Consider lowering first profit target from 2% to 1% if needed
