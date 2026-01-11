# Scoring Engine Fix - Final Solution

## Date: 2026-01-05

## Problem

ALL signals showed `score=0.00` and `source=unknown` because unscored `flow_clusters` were being logged when composite scoring didn't run.

## Root Cause

**Code Flow:**
1. Line 6075: `clusters = flow_clusters` (initialized to unscored clusters)
2. Line 6081: `if use_composite and len(uw_cache) > 0:` - composite scoring runs IF cache exists
3. Line 6265: `clusters = filtered_clusters` - ONLY if composite scoring ran (inside if block)
4. Line 4636: `log_signal(c)` logs ALL clusters passed to decide_and_execute

**The Issue:**
- When composite scoring doesn't run, `clusters` stays as `flow_clusters` (from line 6075)
- `flow_clusters` from `cluster_signals()` don't have `composite_score` or `source` fields
- These unscored clusters got logged to `signals.jsonl` with score=0.00 and source=unknown

## Fix Applied

Added `else` clause after composite scoring block to clear `clusters` when composite scoring doesn't run:

```python
else:
    # CRITICAL FIX: Composite scoring didn't run - clear clusters to prevent logging unscored signals
    # When composite scoring doesn't run, clusters stays as flow_clusters (which have no composite_score)
    # These would appear as score=0.00 in signals.jsonl - prevent this by clearing clusters
    print(f"⚠️  WARNING: Composite scoring did not run (use_composite={use_composite}, cache_symbols={len(uw_cache)}) - clearing {len(flow_clusters)} unscored flow_clusters to prevent signals with score=0.00", flush=True)
    log_event("composite_scoring", "not_run_clearing_clusters", use_composite=use_composite, cache_symbols=len(uw_cache), flow_clusters=len(flow_clusters))
    clusters = []  # Clear unscored clusters - prevent logging signals with score=0.00
```

## Expected Behavior

**Before Fix:**
- Composite scoring doesn't run → clusters = flow_clusters → signals logged with score=0.00 ❌

**After Fix:**
- Composite scoring runs → clusters = filtered_clusters → signals logged with valid scores ✅
- Composite scoring doesn't run → clusters = [] → NO signals logged ✅

## Deployment Status

✅ Code fixed
✅ Committed and pushed to Git
✅ Pulled to droplet
✅ Service restarted

## Next Steps

Wait 2-5 minutes for new signals and verify:
- If composite scoring runs: Signals have scores > 0.0 and source="composite_v3"
- If composite scoring doesn't run: No signals logged (empty clusters list)

---

**Status:** ✅ FIX DEPLOYED - Prevents unscored signals from being logged
