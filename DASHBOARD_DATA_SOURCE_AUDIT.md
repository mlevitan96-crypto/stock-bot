# Dashboard Data Source Audit

**Date:** 2026-01-05  
**Status:** 🔍 **IN PROGRESS - CRITICAL ISSUES FOUND**

---

## Problem Statement

User reported:
- "Last Order" is showing incorrect data
- Concerned that health areas are tied to incorrect trade time data
- Need to verify all dashboard tabs use real, accurate data sources
- Ensure everything works and is accurate

---

## Current Implementation Analysis

### 1. Last Order Display (CRITICAL ISSUE)

**Location:** `dashboard.py` lines 1158-1242

**Current Implementation:**
- Tries multiple endpoints: `/api/health_status`, `http://localhost:8081/api/cockpit`, `http://localhost:8081/health`
- Falls back through multiple sources
- Uses `last_order.age_sec` from API response

**Problem:** 
- Multiple fallback sources create confusion
- Not using Alpaca API directly (most reliable source)
- May be reading from stale or incorrect cached files

**Recommendation:**
- Query Alpaca API directly for most recent order
- Use `api.list_orders(status='all', limit=1, nested=False)` sorted by `created_at`
- Calculate age from current time vs. order timestamp

### 2. Doctor/Heartbeat Display

**Location:** `dashboard.py` lines 1187-1204

**Current Implementation:**
- Uses `data.doctor.age_sec` from health_status endpoint
- Falls back to `healthData.last_heartbeat_age_sec`

**Problem:**
- Depends on bot's internal health tracking (may be stale if bot crashed)
- Should verify bot process is actually running

**Recommendation:**
- Keep current implementation (reasonable for heartbeat)
- Add verification that bot process is running

---

## Data Source Verification Needed

### Critical Checks Required:

1. ✅ **Last Order:**
   - [ ] Verify current data source(s) are correct
   - [ ] Test with Alpaca API direct query
   - [ ] Compare with cached file data
   - [ ] Fix if incorrect

2. ✅ **Doctor/Heartbeat:**
   - [ ] Verify heartbeat mechanism is working
   - [ ] Check if bot process is actually running
   - [ ] Verify data source is accurate

3. ✅ **All Dashboard Tabs:**
   - [ ] Positions Tab - Verify entry_score from metadata (already fixed)
   - [ ] Executive Summary - Verify data from attribution.jsonl
   - [ ] SRE Monitoring - Verify data sources
   - [ ] XAI Auditor - Verify data sources
   - [ ] Trading Readiness - Verify data sources

---

## Action Plan

1. **Immediate:** Fix Last Order to query Alpaca API directly
2. **Verify:** Test all dashboard endpoints with real data
3. **Document:** Update data source documentation
4. **Test:** Confirm accuracy with real trading data
