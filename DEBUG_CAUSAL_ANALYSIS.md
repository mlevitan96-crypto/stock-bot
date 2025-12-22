# Debug Causal Analysis - Why 0 Trades Processed

## Issue
The causal analysis engine is processing 0 trades even though attribution.jsonl exists.

## Potential Causes

1. **File Structure Mismatch**: Attribution records might not have `type="attribution"` field
2. **Trade ID Format**: All trade_ids might start with "open_" (incomplete trades)
3. **Missing Context**: Records might not have the expected structure
4. **Silent Errors**: Exceptions being caught without logging

## Fixes Applied (V4.2)

### 1. More Flexible Record Detection
- Accept records with `type="attribution"` OR records with `context` and `pnl` fields
- Don't require explicit type field

### 2. Enhanced Debugging
- Added detailed debug output showing:
  - Total lines read
  - Why records were skipped (no_id, open_, no_type, errors)
  - Sample record structure

### 3. Better Context Extraction
- Try context at top level if not in nested "context" field
- Try multiple timestamp fields (ts, timestamp, entry_ts)
- Handle missing components gracefully

### 4. Improved P&L Handling
- Handle both pnl_usd and pnl_pct formats
- Better fallback when pnl_pct missing

## Next Steps

After deploying, the debug output will show:
- How many lines are in the file
- Why records are being skipped
- Sample record structure

This will help identify the exact issue.
