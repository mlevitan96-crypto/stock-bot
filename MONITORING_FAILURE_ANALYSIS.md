# Monitoring Failure Analysis - Score 0.00 Issue

## Date: 2026-01-05

## CRITICAL FINDINGS

### 1. Fix Status: ❌ NOT WORKING YET
- Signals STILL show score=0.00 and source=unknown
- Fix was deployed but service may need to restart or new signals need to be generated

### 2. Monitoring Guard FAILURE - CRITICAL BUG

**Location:** `monitoring_guards.py` line 74

**The Bug:**
```python
composite_clusters = [c for c in clusters if c.get("source") == "composite"]

if len(composite_clusters) == 0:
    return True  # No composite clusters to check  ← THIS IS THE BUG!
```

**Why It Failed:**
1. The guard ONLY checks clusters with `source == "composite"`
2. When the bug occurred, clusters had `source == "unknown"` or no source
3. The guard filtered out ALL problematic clusters, so it never checked them
4. The guard returned `True` (healthy) because it found "no composite clusters to check"
5. This is a FALSE NEGATIVE - the system was broken but monitoring said it was healthy

### 3. What Should Have Been Detected

The monitoring should have detected:
- ✅ ALL clusters have `source == "unknown"` 
- ✅ ALL clusters have `composite_score == 0.00`
- ✅ No clusters have `source == "composite_v3"` when composite scoring is active

### 4. Dashboard Health Checks - Gaps

The dashboard health endpoints do NOT check:
- ❌ Signal score distribution (do all signals have score=0.00?)
- ❌ Source field validity (are all sources "unknown"?)
- ❌ Composite scoring activation status vs. actual cluster sources

They only check:
- ✅ Signal data presence (does data exist in cache?)
- ✅ Signal computation (are signals computed?)
- ❌ Signal QUALITY (are scores valid? are sources correct?)

---

## REQUIRED FIXES

### Fix 1: Monitoring Guard - Detect ALL Score Issues

**File:** `monitoring_guards.py`

**Change `check_composite_score_floor` to:**
1. Check ALL clusters (not just composite ones)
2. Detect when ALL clusters have score=0.00
3. Detect when ALL clusters have source="unknown"
4. Alert if composite scoring is active but no clusters have source="composite_v3"

### Fix 2: Dashboard Health - Add Score Quality Checks

**File:** `sre_monitoring.py` or `dashboard.py`

**Add checks for:**
1. Signal score distribution (min, max, avg, count of 0.00 scores)
2. Source field validity (% of signals with source="unknown")
3. Composite scoring status vs. actual cluster sources

### Fix 3: Verify Fix Actually Works

**Current Status:**
- Code fix deployed
- Service restarted
- BUT signals still show score=0.00

**Next Steps:**
1. Wait for new signals to be generated (may take a few minutes)
2. Verify new signals have scores > 0.0
3. If still broken, investigate why composite scoring isn't creating clusters

---

## ROOT CAUSE SUMMARY

1. **Code Bug:** Merged unscored clusters with scored ones
2. **Monitoring Bug:** Guard only checked composite clusters, missed unknown-source clusters
3. **Dashboard Gap:** No quality checks for signal scores/sources
4. **No Alerting:** System was broken but no alerts triggered

---

**Status:** ⚠️ MULTIPLE CRITICAL GAPS IDENTIFIED - FIXES REQUIRED
