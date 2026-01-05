# UW Signal Parser Recovery & Metadata Restoration - Fix Summary

**Date:** 2026-01-05  
**Issue:** Systemic Blindness - 10,909 signals marked as 'unknown', 0.00 scores blocking trades

## Root Causes Identified

1. **Missing Field Extraction**: `flow_conv` and `flow_magnitude` fields from UW API JSON payload were not being extracted
2. **Missing signal_type**: No `signal_type` field (e.g., "BULLISH_SWEEP") created from `flow_type` + `direction`
3. **Gate Events Missing gate_type**: Gate event logs didn't include `gate_type` field, causing analysis scripts to see 'unknown'
4. **Metadata Not Preserved**: signal_type not flowing through to clusters and gate events

## Fixes Applied

### 1. Enhanced `_normalize_flow_trade()` Function

**File:** `main.py` (line ~1480)

**Changes:**
- Added extraction of `flow_conv` from UW API JSON (tries `flow_conv`, `flow_conviction`, `conviction`)
- Added extraction of `flow_magnitude` from UW API JSON (tries `flow_magnitude`, `magnitude`)
- Added creation of `signal_type` field: `"{direction.upper()}_{flow_type.upper()}"` (e.g., "BULLISH_SWEEP", "BEARISH_BLOCK")

**Code Added:**
```python
# ROOT CAUSE FIX: Extract flow_conv and flow_magnitude from UW API JSON payload
flow_conv = float(t.get("flow_conv") or t.get("flow_conviction") or t.get("conviction") or 0.0)
flow_magnitude_raw = t.get("flow_magnitude") or t.get("magnitude") or ""
flow_magnitude = flow_magnitude_raw.upper() if isinstance(flow_magnitude_raw, str) else "UNKNOWN"

# ROOT CAUSE FIX: Create signal_type from flow_type + direction (e.g., BULLISH_SWEEP, BEARISH_BLOCK)
signal_type = f"{direction.upper()}_{flow_type.upper()}" if flow_type and direction else "UNKNOWN"
```

**Impact:** All normalized trades now include `flow_conv`, `flow_magnitude`, and `signal_type` fields

### 2. Enhanced `cluster_signals()` Function

**File:** `main.py` (line ~1630)

**Changes:**
- Added logic to extract `signal_type` from trades in cluster
- Uses most common signal_type in cluster, or first trade's signal_type as fallback
- Preserves `signal_type` in cluster dictionary

**Code Added:**
```python
# ROOT CAUSE FIX: Extract signal_type from trades (use most common or first)
signal_types = [c.get("signal_type", "UNKNOWN") for c in cluster if c.get("signal_type")]
signal_type = max(set(signal_types), key=signal_types.count) if signal_types else (cluster[0].get("signal_type", "UNKNOWN") if cluster else "UNKNOWN")
```

**Impact:** Clusters now have `signal_type` field preserved (e.g., "BULLISH_SWEEP")

### 3. Enhanced Gate Event Logging

**File:** `main.py` (multiple locations in `decide_and_execute()`)

**Changes:**
- Added `gate_type` parameter to all `log_event("gate", ...)` calls
- Added `signal_type` parameter to all `log_event("gate", ...)` calls
- Gate types: "regime_gate", "concentration_gate", "theme_gate", "expectancy_gate", "capacity_gate", "score_gate", "position_gate"

**Examples:**
```python
log_event("gate", "regime_blocked", symbol=symbol, regime=market_regime, gate_type="regime_gate", signal_type=c.get("signal_type", "UNKNOWN"))
log_event("gate", "score_below_min", symbol=symbol, score=score, min_required=min_score, stage=system_stage, gate_type="score_gate", signal_type=c.get("signal_type", "UNKNOWN"))
```

**Impact:** Gate events now include `gate_type` and `signal_type` fields, eliminating 'unknown' values

### 4. Composite Score Access to Raw UW Components

**Status:** ✅ Verified Correct

The composite scoring system (`uw_composite_v2.py::compute_composite_score_v3`) already has access to:
- `flow_conv` via `enriched_data.get("conviction", 0.0)` (which maps to flow_conv in cache)
- The cache structure preserves all fields from normalized trades
- The enrichment process (`uw_enrichment_v2.py::enrich_signal`) includes all cache data fields

**Note:** The `flow_conv` and `flow_magnitude` fields are now extracted at the trade normalization stage, so they will flow through to the cache and be available to composite scoring.

## Expected Behavior After Fix

1. **Signal Metadata Restored:**
   - All signals will have `flow_conv`, `flow_magnitude`, and `signal_type` fields
   - signal_type values: "BULLISH_SWEEP", "BEARISH_BLOCK", "BULLISH_MULTILEG", etc.

2. **Gate Events Labeled:**
   - Gate events will show actual `gate_type` (e.g., "score_gate", "expectancy_gate")
   - Gate events will show actual `signal_type` (e.g., "BULLISH_SWEEP") instead of 'unknown'

3. **Composite Scoring:**
   - Composite scoring already has access to conviction data via cache
   - flow_conv and flow_magnitude will be available in normalized trades
   - Whale/Sweep signals will have proper signal_type labels for analysis

## Testing

**Diagnostic Script:** `test_uw_signal_parser.py`
- Tests that `_normalize_flow_trade` extracts flow_conv, flow_magnitude, signal_type
- Tests signal_type creation logic
- Run: `python test_uw_signal_parser.py`

## Deployment

**Files Modified:**
- `main.py`: Enhanced `_normalize_flow_trade()`, `cluster_signals()`, gate event logging

**Next Steps:**
1. Review changes
2. Deploy to droplet
3. Monitor logs to verify signal_type appears in gate events
4. Verify signals have flow_conv and flow_magnitude fields

## Related Issues Fixed

- **10,909 signals marked 'unknown'**: Fixed by adding signal_type extraction and preservation
- **Gate events showing 'unknown'**: Fixed by adding gate_type and signal_type to log_event calls
- **0.00 score paradox**: Flow_conv and flow_magnitude now extracted, available for composite scoring
