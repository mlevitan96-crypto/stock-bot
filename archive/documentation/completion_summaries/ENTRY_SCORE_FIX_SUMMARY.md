# Entry Score Display Fix - CRITICAL

**Date:** 2026-01-05  
**Status:** ✅ **FIXED AND DEPLOYED**

---

## Problem Identified

**User Concern:** Entry scores showing as 0.00 on dashboard - are positions being entered "blindly" (without entry scores)?

**Root Cause Analysis:**

1. **Dashboard API Endpoint Issue:** 
   - `/api/positions` endpoint only read from Alpaca API
   - Did NOT read `entry_score` from `state/position_metadata.json`
   - Dashboard always showed 0.00 even when entry scores existed in metadata

2. **Trading Bot Validation:**
   - ✅ NEW entries are BLOCKED if `entry_score <= 0.0` (line 5227-5236)
   - ⚠️ Reconciliation CAN restore positions with `entry_score = 0.0` if metadata is missing/corrupted
   - ⚠️ No self-healing check for missing entry scores

---

## Fixes Applied

### 1. Dashboard API Endpoint Fix

**File:** `dashboard.py` line 1620-1646

**Change:** Added metadata loading to include `entry_score` in API response

```python
# Load entry scores from position metadata
metadata = {}
try:
    from config.registry import StateFiles, read_json
    metadata_path = StateFiles.POSITION_METADATA
    if metadata_path.exists():
        metadata = read_json(metadata_path, default={})
except Exception as e:
    print(f"[Dashboard] Warning: Failed to load position metadata: {e}", flush=True)

# Add entry_score to each position
entry_score = metadata.get(symbol, {}).get("entry_score", 0.0) if metadata else 0.0
pos_list.append({
    ...
    "entry_score": float(entry_score)  # CRITICAL: Include entry_score from metadata
})
```

**Result:** Dashboard now displays actual entry scores from metadata

---

### 2. Reconciliation Validation

**File:** `main.py` line 2945-2958

**Change:** Added warning when positions are reconciled with 0.0 entry_score

```python
# CRITICAL VALIDATION: Log warning if entry_score is 0.0 (should never happen)
if entry_score <= 0.0:
    log_event("reconcile", "WARNING_zero_entry_score_reconciled", 
             symbol=symbol, entry_score=entry_score,
             has_metadata=bool(metadata.get(symbol)),
             note="Position restored with 0.0 entry_score - metadata may be corrupted or missing")
    print(f"WARNING {symbol}: Position reconciled with entry_score={entry_score:.2f} - this should never happen", flush=True)
```

**Result:** System now logs warnings when positions are restored with 0.0 entry_score for investigation

---

## Trading Bot Entry Score Protection

**Existing Protection (Already Active):**
- ✅ Line 5227-5236: NEW entries with `entry_score <= 0.0` are **BLOCKED** with `continue`
- ✅ Line 3734-3737: `mark_open` warns if `entry_score <= 0.0` (defensive check)

**What This Means:**
- **New positions CANNOT be opened with 0.0 entry_score** - validation blocks them
- **Reconciled positions CAN have 0.0 entry_score** if metadata is corrupted/missing
- Dashboard will now show 0.00 for positions with missing/corrupted metadata (highlighted in red)

---

## Self-Healing Status

**Current State:**
- Self-healing exists for architecture issues, UW daemon, etc.
- **No self-healing check for missing entry scores in metadata** (not yet implemented)

**Recommendation:**
- Monitor logs for `WARNING_zero_entry_score_reconciled` events
- If positions consistently have 0.0 entry_score, investigate metadata corruption
- Consider adding self-healing check to repair metadata if entry_score is 0.0 and position exists

---

## Verification Steps

1. **Check Dashboard:**
   - Open positions should now show actual entry scores (not 0.00)
   - Positions with 0.0 entry_score will be highlighted in red

2. **Check Logs for Warnings:**
   ```bash
   grep "WARNING_zero_entry_score_reconciled" logs/*.jsonl
   ```

3. **Check Metadata:**
   ```bash
   cat state/position_metadata.json | python3 -m json.tool | grep entry_score
   ```

---

## Next Steps

1. ✅ Dashboard fix deployed
2. ✅ Validation warning added
3. ⚠️ Monitor for `WARNING_zero_entry_score_reconciled` events
4. 🔄 Consider adding self-healing check for metadata corruption (future enhancement)

---

## Impact

- **Dashboard:** Now correctly displays entry scores from metadata
- **Trading Bot:** New positions still protected (cannot open with 0.0 score)
- **Reconciliation:** Warning logged if positions restored with 0.0 score (for investigation)
- **User Visibility:** Can now see which positions have missing/corrupted metadata (shown as 0.00 in red)
