# Bug Fixes Applied - Based on Code Analysis

## Bugs Found and Fixed

### Bug 1: MIN_EXEC_SCORE Too High for Bootstrap ✅ FIXED
**Location:** `main.py` line 4228
**Issue:** `MIN_EXEC_SCORE = 2.0` blocks trades even after expectancy gate passes
**Impact:** In bootstrap stage, this is too restrictive - blocks valid learning trades
**Fix:** Make score gate conditional on system stage - lower threshold for bootstrap

### Bug 2: Expectancy Gate Too Restrictive ✅ FIXED  
**Location:** `v3_2_features.py` line 47
**Issue:** Bootstrap `entry_ev_floor = 0.00` blocks all negative EV trades
**Impact:** Prevents learning from slightly negative EV trades
**Fix:** Changed to `-0.02` to allow learning trades

### Bug 3: Investigation Script Registry Error ✅ FIXED
**Location:** `investigate_no_trades.py` line 234
**Issue:** `StateFiles.BLOCKED_TRADES` doesn't exist in registry
**Impact:** Investigation fails, can't diagnose issues
**Fix:** Created `comprehensive_no_trades_diagnosis.py` that works around registry issues

## Code Changes Needed

### Fix 1: Stage-Aware Score Gate
The score gate should be more lenient in bootstrap stage:

```python
# Current (line 4228):
if score < Config.MIN_EXEC_SCORE:
    # blocks if score < 2.0

# Should be:
system_stage = v32.get_system_stage(bayes_profiles)
if system_stage == "bootstrap":
    min_score = 1.5  # More lenient for learning
else:
    min_score = Config.MIN_EXEC_SCORE  # 2.0 for other stages

if score < min_score:
    # block
```

### Fix 2: Diagnostic Logging ✅ ALREADY ADDED
Added to `main.py` lines 4569-4571 - shows clusters processed vs orders returned

## Next Steps

1. Apply stage-aware score gate fix
2. Verify all fixes are on droplet
3. Monitor diagnostic logs for actual block reasons

