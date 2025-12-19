# UW API Usage Optimization Analysis

**Date**: 2025-12-17  
**Issue**: 75% daily limit reached early in trading day  
**Limit**: 15,000 requests/day, 120 requests/minute

---

## 🔴 **CRITICAL ISSUE IDENTIFIED**

### **Problem: Duplicate API Calls**

The system is making **direct UW API calls** even when cache exists, causing massive over-consumption:

1. **main.py Fallback Loop (Lines 4364-4376)**:
   - Makes `uw.get_option_flow(ticker)` for **EVERY ticker** in `Config.TICKERS`
   - If 50 tickers × 1 request per cycle = **50 requests per cycle**
   - SmartPoller allows polling every 60 seconds
   - **50 requests/minute × 390 minutes (6.5 hours) = 19,500 requests/day** ❌ **EXCEEDS LIMIT**

2. **SRE Monitoring Health Checks**:
   - `sre_monitoring.py` makes actual API calls to test endpoint health
   - Called periodically for multiple endpoints
   - Adds additional requests

3. **Cache Should Be Primary Source**:
   - `uw_integration_full.py` daemon should populate cache
   - All components should read from cache, NOT make direct API calls
   - Current code has "fallback" that bypasses cache

---

## ✅ **Current Architecture (Intended)**

1. **UW Daemon** (`uw_integration_full.py`):
   - Runs as separate process
   - Polls UW API at optimized intervals
   - Writes to `data/uw_flow_cache.json`
   - **ONLY component that should make UW API calls**

2. **Main Bot** (`main.py`):
   - Reads from `uw_flow_cache.json`
   - Uses cache data for all decisions
   - Should **NEVER** make direct UW API calls when cache exists

3. **SmartPoller**:
   - Should only be used by UW daemon
   - NOT by main bot

---

## 🔧 **Required Fixes**

### **Fix 1: Remove Fallback API Calls in main.py**

**Current Code (WRONG):**
```python
# Lines 4364-4376
for ticker in Config.TICKERS:
    if poll_flow:
        flow = uw.get_option_flow(ticker, limit=100)  # ❌ API CALL PER TICKER
```

**Should Be:**
```python
# If cache exists, use it - NO API CALLS
if use_composite and len(uw_cache) > 0:
    # Use cache data only
    # NO direct API calls
else:
    # Only if cache is completely empty (daemon not running)
    # Log warning and skip trading
```

### **Fix 2: Make SRE Monitoring Cache-Based**

**Current:** Makes actual API calls to test health  
**Should:** Check cache freshness and file timestamps instead

### **Fix 3: Verify UW Daemon Polling Frequency**

Check `uw_integration_full.py` to ensure it's not polling too frequently.

---

## 📊 **Request Calculation**

### **Current (BROKEN) Pattern:**
- Main bot cycle: Every 60 seconds
- Per cycle: 50 tickers × 1 request = 50 requests
- Per hour: 50 × 60 = 3,000 requests
- Per day (6.5 hours): 3,000 × 6.5 = **19,500 requests** ❌

### **Correct Pattern (After Fix):**
- UW daemon: Polls at optimized intervals (SmartPoller)
  - option_flow: Every 60 seconds (1 request, not per-ticker)
  - top_net_impact: Every 5 minutes (1 request)
  - dark_pool: Every 2 minutes (1 request per symbol, but batched)
  - greek_exposure: Every 15 minutes (1 request per symbol)
- Main bot: **0 requests** (reads cache only)
- SRE monitoring: **0 requests** (checks cache freshness)

**Estimated after fix: ~500-1,000 requests/day** ✅

---

## 🎯 **Implementation Plan**

1. Remove fallback API calls in `main.py`
2. Make SRE monitoring cache-based
3. Add logging to track actual UW API usage
4. Verify UW daemon is running and populating cache
5. Add rate limit monitoring and alerts



