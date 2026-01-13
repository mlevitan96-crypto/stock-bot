# Scoring Flow Verification Report
**Date:** 2026-01-13  
**Status:** ⚠️ **SIGNALS NOT BEING SCORED**

---

## Executive Summary

The scoring system components are working correctly:
- ✅ **Weights are loaded:** `options_flow=2.4`, `dark_pool=1.3`, etc.
- ✅ **Composite scoring function works:** Test shows scores of 3.627 for AAPL/MSFT
- ✅ **UW cache has 53 symbols** with signal data
- ✅ **Worker loop is running** and calling `run_once()`
- ❌ **BUT:** No composite scores are being calculated in production
- ❌ **No clusters are being created** from signals
- ❌ **No run.jsonl entries** showing completed cycles

---

## Root Cause Analysis

### The Problem
`run_once()` is being called by the worker loop, but:
1. **No composite scores are being calculated** for signals
2. **No clusters are reaching `decide_and_execute()`**
3. **No logs show composite scoring happening** in production

### Why This Happens
Looking at the code flow in `main.py`:
1. `run_once()` is called (line 8452)
2. It should process signals and call composite scoring (line 7548)
3. But we see no logs of composite scoring being called
4. This suggests `run_once()` might be:
   - Crashing before reaching composite scoring
   - Returning early due to a condition
   - Not processing symbols correctly

---

## Verification Results

### ✅ Weights Status
```
WEIGHTS_V3:
  options_flow: 2.4 ✅
  dark_pool: 1.3 ✅
  insider: 0.5 ✅
  ... (all weights present)
```

### ✅ Composite Scoring Test
```
AAPL: composite_score: 3.627 ✅
MSFT: composite_score: 3.627 ✅
```

### ✅ UW Cache
```
Symbols in cache: 53 ✅
Sample: SPY, AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA, AMD, NFLX
```

### ❌ Production Scoring
- No composite scoring logs in journalctl
- No clusters in run.jsonl
- No signals.jsonl entries with scores

---

## Required Fixes

### 1. Add Debug Logging to Composite Scoring
Add explicit logging when composite scoring is called:

```python
# In main.py around line 7548
print(f"DEBUG: Calling compute_composite_score_v3 for {ticker}", flush=True)
composite = uw_v2.compute_composite_score_v3(ticker, enriched, "mixed")
print(f"DEBUG: Composite score for {ticker}: {composite.get('score', 0):.3f}", flush=True)
```

### 2. Verify use_composite is True
Check if `use_composite` condition is being met:

```python
# In main.py around line 7410
print(f"DEBUG: use_composite={use_composite}, cache_symbol_count={cache_symbol_count}", flush=True)
```

### 3. Check for Early Returns
Verify `run_once()` isn't returning early before composite scoring:

```python
# Add logging at start of run_once()
print(f"DEBUG: run_once() STARTED", flush=True)
```

### 4. Verify Symbol Processing Loop
Ensure the symbol processing loop is actually executing:

```python
# In main.py around line 7428
print(f"DEBUG: Processing {len(all_symbols_to_process)} symbols", flush=True)
for ticker in all_symbols_to_process:
    print(f"DEBUG: Processing ticker: {ticker}", flush=True)
```

---

## Next Steps

1. **Add comprehensive debug logging** to trace the entire scoring flow
2. **Check if run_once() is completing** or crashing silently
3. **Verify signals are reaching composite scoring** function
4. **Ensure clusters are being created** after scoring
5. **Check for any conditions blocking** composite scoring execution

---

## Files to Modify

1. `main.py` - Add debug logging to:
   - `run_once()` start/end
   - Composite scoring calls
   - Symbol processing loop
   - Cluster creation

---

**Status:** Scoring system works in isolation but not in production flow. Need to trace execution path.
