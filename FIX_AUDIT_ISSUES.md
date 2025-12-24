# How to Fix Audit Issues - Step by Step Guide

## Overview

This guide provides step-by-step instructions to fix all 12 issues found in the comprehensive audit.

---

## 🔴 CRITICAL (1) - VERIFIED WORKING ✅

**Status:** ✅ FALSE POSITIVE - Adaptive weights ARE being used correctly in `uw_composite_v2.py`

No action needed.

---

## 🔴 HIGH PRIORITY FIXES (5)

### Fix 1: Synchronize Signal Component Lists

**Files:** `config/uw_signal_contracts.py` and `config/registry.py`

**Problem:** Lists are out of sync
- Missing in registry: `flow`, `freshness_factor`
- Missing in contracts: `options_flow`

**Solution:**

1. **Update `config/registry.py`:**
   ```python
   class SignalComponents:
       ALL_COMPONENTS = [
           "flow",  # Add this
           "options_flow",
           "dark_pool",
           "insider",
           "iv_term_skew",
           "smile_slope",
           "whale_persistence",
           "event_alignment",
           "temporal_motif",
           "toxicity_penalty",
           "regime_modifier",
           "congress",
           "shorts_squeeze",
           "institutional",
           "market_tide",
           "calendar_catalyst",
           "etf_flow",
           "greeks_gamma",
           "ftd_pressure",
           "iv_rank",
           "oi_change",
           "squeeze_score",
           "freshness_factor",  # Add this
       ]
   ```

2. **Verify `config/uw_signal_contracts.py` includes all components**

3. **Run verification:**
   ```python
   from config.uw_signal_contracts import SIGNAL_COMPONENTS
   from config.registry import SignalComponents
   
   assert set(SIGNAL_COMPONENTS) == set(SignalComponents.ALL_COMPONENTS)
   ```

---

### Fix 2: Replace Hardcoded Paths

**Files:** `deploy_supervisor.py`, `signals/uw_adaptive.py`

**Solution:**

1. **Add registry import:**
   ```python
   from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles
   ```

2. **Replace hardcoded paths:**

   **In `deploy_supervisor.py`:**
   ```python
   # Before:
   Path("logs/supervisor.log")
   Path("state/bot_heartbeat.json")
   Path("data/uw_flow_cache.json")
   
   # After:
   LogFiles.DEPLOYMENT_SUPERVISOR  # (may need to add to registry)
   StateFiles.BOT_HEARTBEAT
   CacheFiles.UW_FLOW_CACHE
   ```

   **In `signals/uw_adaptive.py`:**
   ```python
   # Before:
   Path("data/adaptive_gate_state.json")
   
   # After:
   StateFiles.ADAPTIVE_GATE_STATE
   ```

3. **Add missing paths to registry if needed:**
   ```python
   # In config/registry.py
   class LogFiles:
       DEPLOYMENT_SUPERVISOR = Directories.LOGS / "supervisor.log"
       # ... other logs
   ```

---

### Fix 3: Add Missing Endpoint Polling

**File:** `uw_flow_daemon.py`

**Missing:** `insider`, `calendar`, `congress`, `institutional`

**Solution:**

1. **Add polling methods to `UWFlowDaemon` class:**

   ```python
   def _poll_insider(self, ticker: str):
       """Poll insider trading data"""
       if not self.poller.should_poll("insider"):
           return
       
       try:
           data = self.client.get_insider(ticker)
           if data:
               self._update_cache(ticker, "insider", data)
               safe_print(f"[UW-DAEMON] Updated insider data for {ticker}")
       except Exception as e:
           safe_print(f"[UW-DAEMON] Error polling insider for {ticker}: {e}")
   
   def _poll_calendar(self, ticker: str):
       """Poll calendar/events data"""
       if not self.poller.should_poll("calendar"):
           return
       
       try:
           data = self.client.get_calendar(ticker)
           if data:
               self._update_cache(ticker, "calendar", data)
               safe_print(f"[UW-DAEMON] Updated calendar data for {ticker}")
       except Exception as e:
           safe_print(f"[UW-DAEMON] Error polling calendar for {ticker}: {e}")
   
   def _poll_congress(self, ticker: str):
       """Poll congress trading data"""
       if not self.poller.should_poll("congress"):
           return
       
       try:
           data = self.client.get_congress(ticker)
           if data:
               self._update_cache(ticker, "congress", data)
               safe_print(f"[UW-DAEMON] Updated congress data for {ticker}")
       except Exception as e:
           safe_print(f"[UW-DAEMON] Error polling congress for {ticker}: {e}")
   
   def _poll_institutional(self, ticker: str):
       """Poll institutional data"""
       if not self.poller.should_poll("institutional"):
           return
       
       try:
           data = self.client.get_institutional(ticker)
           if data:
               self._update_cache(ticker, "institutional", data)
               safe_print(f"[UW-DAEMON] Updated institutional data for {ticker}")
       except Exception as e:
           safe_print(f"[UW-DAEMON] Error polling institutional for {ticker}: {e}")
   ```

2. **Add to SmartPoller intervals:**
   ```python
   # In SmartPoller.__init__ or should_poll method
   self.intervals = {
       "option_flow": 60,
       "insider": 300,  # 5 minutes
       "calendar": 3600,  # 1 hour
       "congress": 300,  # 5 minutes
       "institutional": 300,  # 5 minutes
       # ... other intervals
   }
   ```

3. **Call from main polling loop:**
   ```python
   # In _poll_ticker method
   self._poll_insider(ticker)
   self._poll_calendar(ticker)
   self._poll_congress(ticker)
   self._poll_institutional(ticker)
   ```

4. **Add client methods if needed:**
   ```python
   # In UWClient class
   def get_insider(self, ticker: str):
       return self._get(f"/api/insider/{ticker}")
   
   def get_calendar(self, ticker: str):
       return self._get(f"/api/calendar/{ticker}")
   
   def get_congress(self, ticker: str):
       return self._get(f"/api/congress/{ticker}")
   
   def get_institutional(self, ticker: str):
       return self._get(f"/api/institutional/{ticker}")
   ```

---

### Fix 4: Add Registry Imports

**File:** `deploy_supervisor.py`

**Solution:**

1. **Add import at top of file:**
   ```python
   from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles
   ```

2. **Replace all hardcoded paths with registry paths**

---

### Fix 5: Replace Hardcoded API Endpoints

**Files:** `main.py`, `uw_flow_daemon.py`

**Solution:**

1. **Add import:**
   ```python
   from config.registry import APIConfig
   ```

2. **Replace hardcoded endpoints:**

   **In `main.py`:**
   ```python
   # Before:
   ALPACA_BASE_URL = get_env("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
   
   # After:
   from config.registry import APIConfig
   ALPACA_BASE_URL = APIConfig.ALPACA_BASE_URL
   ```

   **In `uw_flow_daemon.py`:**
   ```python
   # Before:
   self.base_url = "https://api.unusualwhales.com"
   
   # After:
   from config.registry import APIConfig
   self.base_url = APIConfig.UW_BASE_URL
   ```

---

## ⚠️ MEDIUM PRIORITY FIXES (5)

### Fix 6: Standardize Timezone Usage

**Files:** Multiple files

**Solution:**

1. **Use consistent timezone:**
   ```python
   import pytz
   et = pytz.timezone('US/Eastern')  # Handles DST automatically
   now_et = datetime.now(et)
   ```

2. **Replace all `UTC`, `ET`, `EST`, `EDT` references with `US/Eastern`**

3. **Document in MEMORY_BANK.md:**
   - Always use `pytz.timezone('US/Eastern')` for market hours
   - This automatically handles DST transitions

---

## 📝 LOW PRIORITY FIXES (1)

### Fix 7: Add Signal Components Documentation

**File:** `MEMORY_BANK.md`

**Solution:**

Add section:
```markdown
## Signal Components

All 21+ signal components used in trading:

1. **flow** / **options_flow**: Options flow sentiment
2. **dark_pool**: Dark pool activity
3. **insider**: Insider trading
4. **iv_term_skew**: IV term structure skew
5. **smile_slope**: Volatility smile slope
6. **whale_persistence**: Large player patterns
7. **event_alignment**: Event/earnings alignment
8. **temporal_motif**: Temporal patterns
9. **toxicity_penalty**: Signal staleness penalty
10. **regime_modifier**: Market regime adjustment
11. **congress**: Congress/politician trading
12. **shorts_squeeze**: Short interest/squeeze signals
13. **institutional**: Institutional activity
14. **market_tide**: Market-wide options sentiment
15. **calendar_catalyst**: Earnings/events calendar
16. **greeks_gamma**: Gamma exposure
17. **ftd_pressure**: Fails-to-deliver pressure
18. **iv_rank**: IV rank percentile
19. **oi_change**: Open interest changes
20. **etf_flow**: ETF money flow
21. **squeeze_score**: Combined squeeze indicators
22. **freshness_factor**: Data recency factor

**Source:** `config/uw_signal_contracts.py` and `config/registry.py`
```

---

## 🚀 Quick Fix Script

Run the automated fix script:

```bash
python APPLY_AUDIT_FIXES.py
```

This will:
- ✅ Synchronize signal component lists
- ✅ Add registry imports
- ✅ Create TODO for missing endpoints
- ⚠️  Some fixes require manual implementation

---

## ✅ Verification

After applying fixes, verify:

```bash
# Re-run audit
python COMPREHENSIVE_CODE_AUDIT.py

# Check for remaining issues
# Should show 0 critical, reduced high/medium issues
```

---

## 📋 Checklist

- [ ] Fix 1: Signal component lists synchronized
- [ ] Fix 2: Hardcoded paths replaced with registry
- [ ] Fix 3: Missing endpoint polling added
- [ ] Fix 4: Registry imports added
- [ ] Fix 5: Hardcoded API endpoints replaced
- [ ] Fix 6: Timezone usage standardized
- [ ] Fix 7: Signal components documented
- [ ] Re-run audit to verify
- [ ] Test system still works
- [ ] Commit changes

---

**Estimated Time:** 2-4 hours for all fixes
