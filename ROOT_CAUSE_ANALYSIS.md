# Root Cause Analysis - Score 0.00 Issue

## Finding

Signals are logged at line 4636 in `decide_and_execute()`:
```python
for c in clusters_sorted:
    log_signal(c)  # Line 4636 - logs ALL clusters passed to decide_and_execute
```

## The Problem

Looking at the code flow:

1. Line 6075: `clusters = flow_clusters` (initialized)
2. Line 6081: `if use_composite and len(uw_cache) > 0:` - composite scoring runs IF cache exists
3. Line 6265: `clusters = filtered_clusters` - ONLY if composite scoring ran
4. Line 4636: `log_signal(c)` logs ALL clusters

**The Issue:**
- If composite scoring runs but `filtered_clusters` is empty (all symbols rejected), `clusters = filtered_clusters` makes clusters empty
- BUT signals with score=0.00 ARE being logged, which means flow_clusters are being logged
- This means composite scoring is either NOT running, OR there's a bug where flow_clusters are logged even when composite scoring ran

## Hypothesis

Composite scoring is NOT running because:
- `use_composite` is False, OR
- `uw_cache` is empty

When composite scoring doesn't run, `clusters` stays as `flow_clusters` (line 6075), which don't have composite_score or source fields, so they appear as score=0.00 and source=unknown.

## Solution

Need to ensure composite scoring runs when cache exists, OR prevent flow_clusters from being logged when composite scoring should run but doesn't.
