# Position State Discrepancy - Critical Issue Found

**Date:** 2026-01-05  
**Status:** 🔴 **CRITICAL - STATE DESYNC DETECTED**

---

## Problem Statement

**User Report:** "There are no positions open"

**Bot's Internal State:** Shows 6 positions in `state/position_metadata.json`:
- TSLA
- IWM  
- WBD
- SPY
- SNDK
- RDDT

**Discrepancy:** Bot's metadata is STALE and out of sync with Alpaca API (authoritative source).

---

## Root Cause Analysis

### 1. Reconciliation is Throttled

From `main.py` lines 7453-7456:
```python
# Throttle to every 5 minutes
now = time.time()
if (now - _last_reconcile_check_ts) < RECONCILE_CHECK_INTERVAL_SEC:
    return {"skipped": True, "reason": "throttled"}
```

**Issue:** Reconciliation only runs every 5 minutes (throttled).

### 2. Auto-Fix Requires Multiple Confirmations

From `main.py` lines 7514-7518:
```python
# AUTO-FIX: Only after N consecutive confirmations to prevent false positives
if _consecutive_divergence_count >= DIVERGENCE_CONFIRMATION_THRESHOLD:
    # Auto-fix divergence
```

**Issue:** Requires 2 consecutive confirmations before auto-fixing, which means:
- Divergence must be detected in cycle 1
- Must still exist in cycle 2 (5+ minutes later)
- Only then will it auto-fix

**Result:** Stale state can persist for 10+ minutes before being corrected.

### 3. Reconciliation Status

From logs:
```json
"position_reconcile": {"skipped": true, "reason": "throttled"}
```

Reconciliation is being skipped due to throttling.

---

## Impact

1. **Bot thinks it has 6 positions but actually has 0**
2. **Dashboard shows incorrect position count**
3. **Trading logic may be affected** (bot thinks positions are open when they're closed)
4. **New trades may be blocked incorrectly** (thinking max positions reached)

---

## Required Fixes

### Fix 1: Immediate - Force Reconciliation

Need to trigger reconciliation immediately to sync state with Alpaca API.

### Fix 2: Enhanced Monitoring

Add monitoring to detect position state discrepancies:
1. Compare `position_metadata.json` with Alpaca API positions
2. Alert when discrepancy detected
3. Auto-trigger reconciliation when discrepancy found

### Fix 3: Reduce Reconciliation Throttle

Consider reducing throttle interval or removing throttle for critical state checks.

### Fix 4: Force Reconciliation on Startup

Ensure reconciliation runs immediately on bot startup to sync state.

---

## Next Steps

1. ✅ **Diagnosis Complete** - Identified stale state issue
2. ⏳ **Immediate Fix** - Trigger reconciliation to sync state
3. ⏳ **Enhanced Monitoring** - Add position state validation
4. ⏳ **Prevent Future Issues** - Improve reconciliation logic

---

**Priority:** 🔴 **CRITICAL** - State desync can cause trading issues
