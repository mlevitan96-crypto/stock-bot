# How to Fix Audit Issues - Complete Guide

## Summary

The comprehensive audit found **12 issues**. Here's how to fix them:

---

## ✅ Already Fixed (by script)

1. **Signal Component Lists Synchronized** ✅
   - Script synchronized `config/registry.py` with `config/uw_signal_contracts.py`

2. **Registry Imports Added** ✅
   - Added to `deploy_supervisor.py`
   - Added to `signals/uw_adaptive.py`

---

## 🔴 High Priority - Manual Fixes Needed

### Fix 1: Replace Hardcoded Paths

**Files:** `deploy_supervisor.py`, `signals/uw_adaptive.py`

**Steps:**
1. Find all `Path("logs/...")`, `Path("state/...")`, `Path("data/...")`
2. Replace with `LogFiles.XXX`, `StateFiles.XXX`, `CacheFiles.XXX`
3. Add missing paths to `config/registry.py` if needed

**Example:**
```python
# Before:
Path("logs/supervisor.log")

# After:
LogFiles.DEPLOYMENT_SUPERVISOR  # (add to registry if missing)
```

---

### Fix 2: Replace Hardcoded API Endpoints

**Files:** `main.py`, `uw_flow_daemon.py`

**Steps:**
1. Find `"https://paper-api.alpaca.markets"` → Replace with `APIConfig.ALPACA_BASE_URL`
2. Find `"https://api.unusualwhales.com"` → Replace with `APIConfig.UW_BASE_URL`
3. Ensure `from config.registry import APIConfig` is imported

**Example:**
```python
# Before:
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

# After:
from config.registry import APIConfig
ALPACA_BASE_URL = APIConfig.ALPACA_BASE_URL
```

---

### Fix 3: Add Missing Endpoint Polling

**File:** `uw_flow_daemon.py`

**Missing:** `insider`, `calendar`, `congress`, `institutional`

**Steps:**
1. Add polling methods to `UWFlowDaemon` class
2. Add to SmartPoller intervals
3. Call from `_poll_ticker()` method
4. Add client methods if needed

**See `FIX_AUDIT_ISSUES.md` for complete implementation code**

---

## ⚠️ Medium Priority

### Fix 4: Standardize Timezone

**Files:** Multiple files using `UTC`, `ET`, `EST`, `EDT`

**Steps:**
1. Replace all with `pytz.timezone('US/Eastern')`
2. This automatically handles DST

**Example:**
```python
# Before:
datetime.now(timezone.utc)

# After:
import pytz
et = pytz.timezone('US/Eastern')
datetime.now(et)
```

---

## 📝 Low Priority

### Fix 5: Add Signal Components Documentation

**File:** `MEMORY_BANK.md`

**Steps:**
1. Add "Signal Components" section
2. List all 21+ components
3. Document their sources

**See `FIX_AUDIT_ISSUES.md` for complete section**

---

## 🚀 Quick Start

1. **Review:** Read `FIX_AUDIT_ISSUES.md` for detailed instructions
2. **Fix High Priority:** Do fixes 1-3 first
3. **Verify:** Run `python COMPREHENSIVE_CODE_AUDIT.py` to check progress
4. **Test:** Ensure system still works after fixes
5. **Commit:** Commit changes

---

## 📋 Checklist

- [x] Signal component lists synchronized (automated)
- [x] Registry imports added (automated)
- [ ] Hardcoded paths replaced
- [ ] Hardcoded API endpoints replaced
- [ ] Missing endpoint polling added
- [ ] Timezone standardized
- [ ] Documentation updated
- [ ] Re-run audit
- [ ] Test system

---

**Estimated Time:** 1-2 hours for remaining manual fixes
