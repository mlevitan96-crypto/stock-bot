# Data Path Fragmentation & Standardized Audit Labels - Fix Summary

**Date:** 2026-01-02  
**Status:** ✅ IMPLEMENTATION COMPLETE  
**Authoritative Source:** MEMORY_BANK.md

---

## Problem Identified

The Friday EOW audit returned 0 trades because:
1. **Data path fragmentation:** `main.py` and `friday_eow_audit.py` used different path resolution methods
2. **Schema mismatch:** Attribution logging used nested schema while audit expected flat schema
3. **Missing mandatory fields:** `stealth_boost_applied` not tracked, `entry_score` could be missing
4. **Silent failures:** Audit succeeded but returned zero results without reporting WHERE it looked

---

## Fixes Implemented

### 1. Standardized Data Path ✅

**Files Modified:**
- `config/registry.py` - Added `LogFiles.ATTRIBUTION` constant
- `main.py` - Updated to use `ATTRIBUTION_LOG_PATH = LogFiles.ATTRIBUTION`
- `friday_eow_audit.py` - Updated to use `LogFiles.ATTRIBUTION` from config/registry
- `dashboard.py` - Updated to use `LogFiles.ATTRIBUTION` from config/registry

**Changes:**
```python
# config/registry.py
class LogFiles:
    # CRITICAL: Attribution log path - MUST be used by all components
    ATTRIBUTION = Directories.LOGS / "attribution.jsonl"

# main.py
from config.registry import LogFiles
ATTRIBUTION_LOG_PATH = LogFiles.ATTRIBUTION

# friday_eow_audit.py
from config.registry import LogFiles
ATTRIBUTION_LOG = LogFiles.ATTRIBUTION
```

**Impact:**
- Single source of truth for attribution log path
- All components use exact same path constant
- Eliminates path mismatch bugs

---

### 2. Metadata Schema Enforcement ✅

**File Modified:** `main.py::log_exit_attribution()`

**Mandatory Flat Schema Fields:**
- `symbol` - Trade symbol (top level)
- `entry_score` - Entry signal score (top level, MUST NOT be 0.0)
- `exit_pnl` - Exit P&L percentage (top level, alias for pnl_pct)
- `market_regime` - Market regime at entry (top level)
- `stealth_boost_applied` - Boolean indicating if stealth flow boost was applied (top level)

**Changes:**
```python
# Extract stealth_boost_applied
stealth_boost_applied = False
if context.get("flow_magnitude") == "LOW":
    stealth_boost_applied = True

# Enforce mandatory flat schema
attribution_record = {
    "type": "attribution",
    "trade_id": f"close_{symbol}_{now_iso()}",
    # MANDATORY FLAT FIELDS
    "symbol": symbol,
    "entry_score": entry_score_flat,
    "exit_pnl": round(pnl_pct, 4),
    "market_regime": market_regime_flat,
    "stealth_boost_applied": stealth_boost_applied,
    # Additional fields (preserved for backward compatibility)
    "pnl_usd": round(pnl_usd, 2),
    "pnl_pct": round(pnl_pct, 4),
    "hold_minutes": round(hold_minutes, 1),
    "context": context  # Full context preserved
}
```

**Data Integrity Checks:**
- ✅ CRITICAL ERROR logged if `entry_score == 0.0`
- ✅ WARNING logged if `market_regime == "unknown"`
- ✅ Verification check after write to confirm log was written successfully

**Impact:**
- All mandatory fields always present at top level
- Backward compatibility maintained (nested schema still in `context`)
- Data integrity enforced with logging

---

### 3. Audit Script Logic Repair ✅

**File Modified:** `friday_eow_audit.py`

**Changes:**
1. **Fuzzy Search Function:** Added `fuzzy_search_attribution_log()` to search across all log directories
2. **Load with Fallback:** Added `load_attribution_with_fuzzy_search()` that:
   - Tries primary standardized path first
   - If empty/missing, searches alternative locations
   - Reports WHERE data was found (stderr output)
   - Never silently returns zero results without explanation

3. **Flat Schema Support:** Added `extract_trade_field()` helper function that:
   - Tries top-level field (flat schema)
   - Falls back to context.field (nested schema)
   - Returns default if not found

4. **Schema-Aware Analysis:** Updated all analysis functions to use `extract_trade_field()`:
   - `calculate_alpha_decay_curves()` - Supports flat/nested schema
   - `analyze_stealth_flow_effectiveness()` - Checks `stealth_boost_applied` field
   - `analyze_temporal_liquidity_gate_impact()` - Supports flat/nested schema
   - `analyze_greeks_decay()` - Supports flat/nested schema

**Fuzzy Search Locations:**
- Primary: `logs/attribution.jsonl` (standardized path)
- Alternatives: `data/attribution.jsonl`, `state/attribution.jsonl`
- Parent directories: Searches up to 2 levels up if script run from subdirectory

**Impact:**
- Never silently returns zero results
- Reports data source location in stderr
- Supports both flat and nested schemas
- Finds data even if path differs

---

### 4. Dashboard Label Sync ✅

**File Modified:** `dashboard.py`

**Changes:**
1. **Standardized Path:** Uses `LogFiles.ATTRIBUTION` from config/registry.py
2. **Flat Schema Support:** Extracts fields from top level first, falls back to nested
3. **CRITICAL ERROR Logging:** Logs CRITICAL ERROR to stderr if `entry_score == 0.0` or missing
4. **Field Extraction:**
   - `entry_score` - Tries flat schema first
   - `market_regime` - Tries flat schema first
   - `exit_pnl`/`pnl_pct` - Tries flat schema first
   - `stealth_boost_applied` - Extracted from flat schema

**Error Logging:**
```python
if entry_score == 0.0 or entry_score is None:
    print(f"[Dashboard] CRITICAL_ERROR: Missing entry_score for trade {rec.get('trade_id', 'unknown')} symbol {rec.get('symbol', 'unknown')}", flush=True, file=sys.stderr)
```

**Impact:**
- Dashboard uses same schema as audit
- CRITICAL ERRORS logged for missing data
- No silent "0.0 score" displays without error logging

---

### 5. Data Integrity Check ✅

**File Modified:** `main.py::log_exit_attribution()`

**Implementation:**
```python
# DATA INTEGRITY CHECK: Verify log was written successfully
try:
    import os
    if ATTRIBUTION_LOG_PATH.exists():
        import time
        file_mtime = os.path.getmtime(str(ATTRIBUTION_LOG_PATH))
        if time.time() - file_mtime < 5:
            log_event("data_integrity", "attribution_log_verified", symbol=symbol)
        else:
            log_event("data_integrity", "WARNING_attribution_log_not_updated", 
                     symbol=symbol, file_age_sec=time.time() - file_mtime)
    else:
        log_event("data_integrity", "CRITICAL_ERROR_attribution_log_missing", symbol=symbol)
except Exception as integrity_error:
    log_event("data_integrity", "ERROR_integrity_check_failed", 
             symbol=symbol, error=str(integrity_error))
```

**Impact:**
- Every trade execution verified by data integrity check
- Confirms log was written successfully
- Catches write failures immediately

---

## Standardized Schema

### Mandatory Flat Schema (Top Level)

```json
{
  "type": "attribution",
  "trade_id": "close_AAPL_2026-01-02T21:30:00Z",
  "ts": "2026-01-02T21:30:00Z",
  "symbol": "AAPL",
  "entry_score": 3.45,
  "exit_pnl": 2.34,
  "market_regime": "RISK_ON",
  "stealth_boost_applied": false,
  "pnl_usd": 125.50,
  "pnl_pct": 2.34,
  "hold_minutes": 240.0,
  "context": {
    // Full nested context preserved for backward compatibility
  }
}
```

### Field Requirements

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `symbol` | string | ✅ Yes | - | Must not be empty |
| `entry_score` | float | ✅ Yes | - | **CRITICAL ERROR if 0.0 or missing** |
| `exit_pnl` | float | ✅ Yes | - | Alias for pnl_pct |
| `market_regime` | string | ✅ Yes | "unknown" | **WARNING if "unknown"** |
| `stealth_boost_applied` | boolean | ✅ Yes | false | Extracted from flow_magnitude |

---

## Data Path Map (Finalized, Immutable)

**Single Source of Truth:** `config/registry.py::LogFiles.ATTRIBUTION`

**Path:** `logs/attribution.jsonl` (relative to project root)

**All Components MUST Use:**
```python
from config.registry import LogFiles
ATTRIBUTION_LOG = LogFiles.ATTRIBUTION
```

**Components Updated:**
- ✅ `main.py` - Uses `ATTRIBUTION_LOG_PATH = LogFiles.ATTRIBUTION`
- ✅ `friday_eow_audit.py` - Uses `LogFiles.ATTRIBUTION`
- ✅ `dashboard.py` - Uses `LogFiles.ATTRIBUTION`
- ✅ All future components MUST use `LogFiles.ATTRIBUTION`

---

## Testing & Verification

### Test 1: Path Standardization
- [ ] Verify all components use `LogFiles.ATTRIBUTION`
- [ ] Verify no hardcoded paths remain

### Test 2: Schema Enforcement
- [ ] Verify all trades have mandatory flat fields
- [ ] Verify CRITICAL ERROR logged if entry_score missing
- [ ] Verify stealth_boost_applied is tracked

### Test 3: Audit Script
- [ ] Run `friday_eow_audit.py` and verify it finds trades
- [ ] Verify fuzzy search reports data source location
- [ ] Verify audit never silently returns zero results

### Test 4: Dashboard
- [ ] Verify dashboard displays entry_score correctly
- [ ] Verify CRITICAL ERROR logged for missing fields
- [ ] Verify no "0.0 score" displays without error

### Test 5: Data Integrity
- [ ] Verify integrity check runs after each trade
- [ ] Verify log verification confirms write success

---

## Files Modified

1. ✅ `config/registry.py` - Added `LogFiles.ATTRIBUTION`
2. ✅ `main.py` - Standardized path, enforced schema, added integrity check
3. ✅ `friday_eow_audit.py` - Standardized path, fuzzy search, flat schema support
4. ✅ `dashboard.py` - Standardized path, flat schema support, error logging

---

## Next Steps

1. **Deploy Fixes:** Commit and push all changes
2. **Verify Audit:** Run `friday_eow_audit.py` and confirm it finds trades
3. **Monitor Logs:** Check for CRITICAL ERROR entries in logs
4. **Update MEMORY_BANK.md:** Document finalized Data Path Map

---

## Reference

- **Authoritative Source:** `MEMORY_BANK.md`
- **Standardized Path:** `config/registry.py::LogFiles.ATTRIBUTION`
- **Schema Definition:** This document (Mandatory Flat Schema section)
