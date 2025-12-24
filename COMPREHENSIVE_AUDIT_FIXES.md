# Comprehensive Code Audit - Findings and Fixes

**Date:** 2025-12-24  
**Audit Tool:** `COMPREHENSIVE_CODE_AUDIT.py`  
**Total Findings:** 12 issues (1 Critical, 5 High, 5 Medium, 1 Low)

---

## 🔴 CRITICAL ISSUES (1)

### 1. Signal Computation Doesn't Use Adaptive Weights
**File:** `signals/uw_composite.py` or `uw_composite_v2.py`  
**Issue:** Signal computation doesn't call `get_adaptive_weights()`  
**Impact:** Learning system updates weights but they're not applied to trading decisions  
**Fix:** 
- Verify `uw_composite_v2.py` has `get_adaptive_weights()` call
- Ensure adaptive weights are merged with base weights
- Verify cache invalidation after learning updates

**Status:** ⚠️ NEEDS VERIFICATION

---

## 🔴 HIGH PRIORITY ISSUES (5)

### 2. Signal Component Lists Don't Match
**Files:** `config/uw_signal_contracts.py` vs `config/registry.py`  
**Issue:** `SIGNAL_COMPONENTS` and `SignalComponents.ALL_COMPONENTS` are out of sync  
**Impact:** Mismatched component names can cause learning system to miss signals  
**Fix:**
```python
# Synchronize both lists to include all 21+ components
# Ensure exact match between:
# - config/uw_signal_contracts.py::SIGNAL_COMPONENTS
# - config/registry.py::SignalComponents.ALL_COMPONENTS
```

**Status:** ❌ NEEDS FIX

### 3. Hardcoded Paths in Multiple Files
**Files:** `main.py`, `uw_flow_daemon.py`, others  
**Issue:** Hardcoded paths like `"logs/attribution.jsonl"` instead of using registry  
**Impact:** Path changes require updates in multiple files, error-prone  
**Fix:**
- Replace all hardcoded paths with `config/registry.py` imports
- Use `StateFiles`, `CacheFiles`, `LogFiles`, `ConfigFiles`
- Example: `Path("logs/attribution.jsonl")` → `LogFiles.ATTRIBUTION` (if exists) or add to registry

**Status:** ⚠️ PARTIAL (some files already use registry)

### 4. Missing Endpoint Polling
**File:** `uw_flow_daemon.py`  
**Issue:** Missing polling for: `insider`, `calendar`, `congress`, `institutional`  
**Impact:** These signals are not being captured, reducing signal quality  
**Fix:**
- Add polling methods for missing endpoints
- Ensure all 11+ UW endpoints are polled
- Verify data flows to cache

**Status:** ❌ NEEDS FIX

### 5. Hardcoded Paths Without Registry Import
**File:** Multiple files  
**Issue:** Files use hardcoded paths but don't import registry  
**Impact:** Inconsistent path management  
**Fix:**
- Add `from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles`
- Replace hardcoded paths

**Status:** ❌ NEEDS FIX

---

## ⚠️ MEDIUM PRIORITY ISSUES (5)

### 6. Hardcoded API Endpoints
**Files:** Multiple files  
**Issue:** Hardcoded `"https://paper-api.alpaca.markets"` and `"https://api.unusualwhales.com"`  
**Impact:** API endpoint changes require code changes  
**Fix:**
- Use `config/registry.py::APIConfig.ALPACA_BASE_URL`
- Use `config/registry.py::APIConfig.UW_BASE_URL`

**Status:** ⚠️ PARTIAL (registry has these, but not all files use them)

### 7. Timezone Inconsistency
**Files:** Multiple files  
**Issue:** Mixed timezone references (`UTC`, `ET`) instead of consistent `US/Eastern`  
**Impact:** Potential timezone bugs, especially around DST transitions  
**Fix:**
- Use `pytz.timezone('US/Eastern')` consistently (handles DST automatically)
- Document timezone usage in MEMORY_BANK.md

**Status:** ⚠️ MOSTLY FIXED (daemon uses US/Eastern, verify others)

---

## 📝 LOW PRIORITY ISSUES (1)

### 8. Missing Documentation Sections
**File:** `MEMORY_BANK.md`  
**Issue:** Missing "Signal Components" section  
**Impact:** Documentation incomplete  
**Fix:** Add section documenting all signal components and their sources

**Status:** ❌ NEEDS FIX

---

## ✅ VERIFICATION CHECKLIST

After fixes, verify:

- [ ] All signal components are synchronized
- [ ] All file paths use registry
- [ ] All 11+ UW endpoints are polled
- [ ] Adaptive weights are applied in signal computation
- [ ] Learning updates flow back to trading
- [ ] All trades flow to learning system
- [ ] Documentation is complete
- [ ] Memory bank is up to date

---

## 📊 SUMMARY

**Total Issues:** 12  
**Critical:** 1 (must fix immediately)  
**High:** 5 (fix before next deployment)  
**Medium:** 5 (fix in next iteration)  
**Low:** 1 (documentation improvement)

**Estimated Fix Time:** 2-4 hours for all critical and high priority issues

---

## 🚀 NEXT STEPS

1. **Immediate (Critical):**
   - Verify adaptive weights are used in signal computation
   - Fix if not working

2. **Before Next Deployment (High):**
   - Synchronize signal component lists
   - Fix hardcoded paths
   - Add missing endpoint polling
   - Add registry imports where missing

3. **Next Iteration (Medium):**
   - Replace hardcoded API endpoints
   - Standardize timezone usage

4. **Documentation (Low):**
   - Update MEMORY_BANK.md with signal components section
