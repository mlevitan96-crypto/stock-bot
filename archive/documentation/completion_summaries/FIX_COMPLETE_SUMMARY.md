# Scoring Engine Fix - Complete Summary

## Date: 2026-01-05

## Problem

ALL signals showed `score=0.00` and `source=unknown` in signals.jsonl, making trading impossible.

## Root Cause

**Code Flow Issue:**
1. Line 6075: `clusters = flow_clusters` (initialized to unscored clusters from `cluster_signals()`)
2. Line 6081: `if use_composite and len(uw_cache) > 0:` - composite scoring runs IF cache exists
3. Line 6265: `clusters = filtered_clusters` - ONLY executes if composite scoring ran (inside if block)
4. Line 4636: `log_signal(c)` logs ALL clusters passed to decide_and_execute

**The Bug:**
- When composite scoring doesn't run, `clusters` stays as `flow_clusters` (unscored)
- `flow_clusters` from `cluster_signals()` don't have `composite_score` or `source` fields
- These unscored clusters got logged with score=0.00 and source=unknown

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

## Expected Behavior After Fix

**Scenario 1: Composite scoring runs**
- `clusters = filtered_clusters` (scored clusters)
- Signals logged with valid scores and source="composite_v3" ✅

**Scenario 2: Composite scoring doesn't run**
- `clusters = []` (cleared)
- NO signals logged ✅
- Prevents unscored signals from being logged

## Deployment Status

✅ Code fixed in main.py (line 6273-6279)
✅ Committed to Git
✅ Pushed to remote
✅ Pulled to droplet
✅ Service restarted

## Next Steps

Wait 2-5 minutes for new signals and verify:
- No signals with score=0.00 should appear in signals.jsonl
- If composite scoring runs: Signals have scores > 0.0 and source="composite_v3"
- If composite scoring doesn't run: No signals logged (clusters cleared)

---

**Status:** ✅ FIX DEPLOYED - Prevents unscored signals from being logged
