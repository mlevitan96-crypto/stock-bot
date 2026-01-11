# Profit Target Issue Analysis

## Problem
Diagnostic shows: **"Profit targets: NOT FOUND"** - No profit target exits found in recent exits.

## Root Cause Analysis

### Code Flow
1. **Targets Initialized** (line 3390-3392):
   ```python
   targets_state = [
       {"pct": t, "hit": False, "fraction": Config.SCALE_OUT_FRACTIONS[i]}
       for i, t in enumerate(Config.PROFIT_TARGETS)
   ]
   ```
   - Stored in `self.opens[symbol]["targets"]`
   - Default: [0.02, 0.05, 0.10] (2%, 5%, 10%)

2. **Targets Checked** (line 3703-3705):
   ```python
   ret_pct = _position_return_pct(info["entry_price"], current_price, info.get("side", "buy"))
   for tgt in info.get("targets", []):
       if not tgt["hit"] and ret_pct >= tgt["pct"]:
   ```

3. **Return Calculation** (line 501-505):
   ```python
   def _position_return_pct(entry: float, current: float, side: str) -> float:
       r = (current - entry) / entry
       return r if side == "buy" else -r
   ```

### Potential Issues

1. **Targets Not Persisted to Metadata**
   - `_persist_position_metadata()` (line 3417) doesn't save `targets`
   - When positions reloaded after restart, `targets` might be missing
   - Check: Does `reload_positions_from_metadata()` restore targets?

2. **Targets Lost on Reload**
   - If `info.get("targets", [])` returns empty list, profit targets won't trigger
   - Need to verify targets are restored from metadata

3. **Early Exits**
   - Time exits (4 hours) or stops might trigger before profit targets
   - Most exits show "time_or_trail" - positions closing before hitting 2% profit

4. **Return Calculation Issue**
   - For "buy" side: `(current - entry) / entry` should give positive % for profit
   - For "sell" side: `-(current - entry) / entry` should give positive % for profit
   - Need to verify this is correct

## Fix Required

1. **Persist targets to metadata**:
   ```python
   metadata[symbol] = {
       ...
       "targets": targets_state,  # ADD THIS
   }
   ```

2. **Restore targets on reload**:
   ```python
   if "targets" in metadata[symbol]:
       info["targets"] = metadata[symbol]["targets"]
   else:
       # Re-initialize targets if missing
       info["targets"] = [
           {"pct": t, "hit": False, "fraction": Config.SCALE_OUT_FRACTIONS[i]}
           for i, t in enumerate(Config.PROFIT_TARGETS)
       ]
   ```

3. **Add logging** to verify targets are being checked:
   ```python
   if not info.get("targets"):
       log_event("exit", "profit_targets_missing", symbol=symbol)
   ```

## Next Steps

1. Check if targets are in metadata
2. Verify targets are restored on reload
3. Add targets to metadata persistence
4. Add logging to track profit target checks
