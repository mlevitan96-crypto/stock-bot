# Comprehensive Monitoring Failure Report

## Date: 2026-01-05

## Executive Summary

**Critical Issue:** ALL signals showed `score=0.00` and `source=unknown` for an extended period, and monitoring completely failed to detect it.

**Root Causes Identified:**
1. **Code Bug:** Unscored clusters merged with scored clusters
2. **Monitoring Bug:** Guard only checked composite clusters, missed unknown-source clusters
3. **Dashboard Gap:** No signal quality checks (score distribution, source validity)
4. **No Alerting:** System was broken but appeared healthy

---

## Issue #1: Code Bug (FIXED)

**Problem:** Line 6264 merged `flow_clusters` (no scores) with `filtered_clusters` (has scores)

**Fix Applied:**
- Changed to use ONLY `filtered_clusters` when composite scoring is active
- All clusters now have `composite_score > 0.0` and `source="composite_v3"`

**Status:** ✅ Code fixed, but NOT YET VERIFIED WORKING (signals still show 0.00 in test)

---

## Issue #2: Monitoring Guard FAILURE (FIXED)

**Location:** `monitoring_guards.py` line 74

**The Critical Bug:**
```python
composite_clusters = [c for c in clusters if c.get("source") == "composite"]

if len(composite_clusters) == 0:
    return True  # No composite clusters to check  ← FALSE NEGATIVE!
```

**Why It Failed:**
1. Guard ONLY checked clusters with `source == "composite"`
2. When bug occurred, ALL clusters had `source == "unknown"`
3. Guard filtered out ALL problematic clusters
4. Guard returned `True` (healthy) because it found "no composite clusters to check"
5. **This is a FALSE NEGATIVE - system was broken but monitoring said it was healthy**

**Fix Applied:**
- Now checks ALL clusters (not just composite ones)
- Detects when ALL scores are 0.00
- Detects when ALL sources are "unknown"
- Detects when composite scoring is active but no clusters have source="composite_v3"

**Status:** ✅ Monitoring guard fixed and deployed

---

## Issue #3: Dashboard Health Checks - GAPS IDENTIFIED

**What Dashboard DOES Check:**
- ✅ Signal data presence (does data exist in cache?)
- ✅ Signal computation (are signals computed?)
- ✅ UW API endpoint health
- ✅ Order execution pipeline

**What Dashboard DOES NOT Check:**
- ❌ Signal score distribution (do all signals have score=0.00?)
- ❌ Source field validity (are all sources "unknown"?)
- ❌ Composite scoring activation vs. actual cluster sources
- ❌ Signal quality metrics (min/max/avg scores)

**Impact:**
- Dashboard showed "healthy" even when ALL signals had score=0.00
- No visibility into signal quality issues

**Status:** ⚠️ TODO - Add dashboard health checks for signal quality

---

## Issue #4: Verification Status

**Current Test Results:**
- 861 signals in last 30 minutes
- ALL have score=0.00
- ALL have source=unknown

**Possible Reasons:**
1. **Service hasn't restarted properly** - Need to verify
2. **New signals haven't been generated yet** - Fix only affects NEW clusters
3. **Composite scoring may not be running** - Need to check logs
4. **Fix logic may have an issue** - Need to investigate

**Next Steps:**
1. Wait 2-5 minutes for new signals to be generated
2. Re-test with signals from LAST 5 MINUTES only
3. Check service logs to verify composite scoring is running
4. If still broken, investigate why composite scoring isn't creating clusters

---

## Required Actions

### Immediate (CRITICAL)
1. ✅ Fix code bug (DONE)
2. ✅ Fix monitoring guard (DONE)
3. ⏳ Verify fix is actually working (IN PROGRESS)
4. ⏳ Add dashboard health checks for signal quality (TODO)

### Short-Term (HIGH PRIORITY)
1. Add signal quality metrics to SRE monitoring
2. Add alerts for score=0.00 issues
3. Add alerts for source="unknown" issues
4. Create dashboard widget showing score distribution

### Long-Term (MEDIUM PRIORITY)
1. Add automated tests for signal quality
2. Add regression tests for scoring pipeline
3. Create runbook for signal quality issues

---

## Lessons Learned

1. **Monitoring must check ALL data, not just subset**
   - Filtering out problematic data before checking = false negatives
   
2. **Dashboard needs quality checks, not just presence checks**
   - Data can exist but be invalid (score=0.00, source=unknown)
   
3. **Test fixes immediately after deployment**
   - Don't assume fixes work without verification
   
4. **Multiple layers of monitoring needed**
   - Code-level guards + Dashboard health + Alerting

---

**Status:** ⚠️ MULTIPLE CRITICAL GAPS IDENTIFIED AND BEING ADDRESSED
