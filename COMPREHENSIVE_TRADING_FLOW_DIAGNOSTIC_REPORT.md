# Comprehensive Trading Flow Diagnostic Report

**Date:** 2026-01-26  
**Audit Type:** Direct droplet inspection + telemetry artifact analysis  
**Status:** ⚠️ **TRADING OPERATIONAL, ANALYSIS DATA STALE**

---

## Executive Summary

A comprehensive audit was performed directly on the droplet. **Core trading functionality is fully operational**, but **telemetry/computed artifacts are stale or missing** because the telemetry extraction process is not running.

**Key Findings:**
- ✅ **Core Trading:** All processes running, active trading (50 trades in last 2h)
- ✅ **Signal Capture:** Working (53 symbols, cache updated 0.01 min ago)
- ✅ **Exit Criteria:** Working (621 recent exits)
- ✅ **Logging:** All systems active
- ❌ **Telemetry Artifacts:** 10 artifacts stale (65.3 hours), 4 artifacts missing
- ❌ **Telemetry Extraction:** Not scheduled, hasn't run in 65.7 hours

---

## Complete Trading Flow Checklist

### ✅ 1. SIGNAL CAPTURE - WORKING

| Component | Status | Details |
|-----------|--------|---------|
| UW Flow Daemon Running | ✅ PASS | Running (PID: 1793750) |
| Cache File Exists | ✅ PASS | Exists, 6.7 MB |
| Cache Has Data | ✅ PASS | 53 symbols in cache |
| Cache Recent | ✅ PASS | Updated 0.01 min ago |
| Enrichment Module | ✅ PASS | Available |

**Verification:** Signal capture is working correctly.

---

### ✅ 2. SIGNAL PROCESSING - WORKING

| Component | Status | Details |
|-----------|--------|---------|
| Composite Scoring Module | ✅ PASS | Available |
| Composite Scoring Working | ✅ PASS | 937 recent orders indicates scoring active |
| Gate Event Logging | ✅ PASS | 1,047 recent gate events |
| Signal History Logging | ✅ PASS | Active |

**Verification:** Signal processing is working correctly.

---

### ✅ 3. EXIT CRITERIA - WORKING

| Component | Status | Details |
|-----------|--------|---------|
| evaluate_exits() Function | ✅ PASS | Exists |
| Exit Event Logging | ✅ PASS | 621 recent exits in last 60 min |
| Exit Signals Captured | ✅ PASS | Exit log shows active evaluation |
| Structural Exit Module | ✅ PASS | Available |
| Exit Attribution Logging | ✅ PASS | 283 recent attribution entries |

**Verification:** Exit criteria are working correctly.

**Exit Criteria Confirmed:**
- Stop-loss: -1.0% ✅
- Signal decay: <60% of entry score ✅
- Profit target: 0.75% ✅
- Trailing stop: 1.5% / 1.0% in MIXED regime ✅

---

### ✅ 4. LOGGING SYSTEMS - WORKING

| Component | Status | Details |
|-----------|--------|---------|
| Logging Functions Available | ✅ PASS | All functions present |
| Log Directories Exist | ✅ PASS | All directories exist |
| Attribution Logging | ✅ PASS | 2,127 total, 283 recent |
| Order Logging | ✅ PASS | 19,745 total, 937 recent |
| Run Cycle Logging | ✅ PASS | 7,091 total, 66 recent |
| Exit Logging | ✅ PASS | 10,902 total, 621 recent |
| Gate Logging | ✅ PASS | 5,057 total, 1,047 recent |
| System Event Logging | ✅ PASS | Active |

**Verification:** All logging systems are operational.

---

### ✅ 5. TRADE EXECUTION - WORKING

| Component | Status | Details |
|-----------|--------|---------|
| AlpacaExecutor Available | ✅ PASS | Class present |
| decide_and_execute() Function | ✅ PASS | Function exists |
| Position Metadata Tracking | ✅ PASS | File exists, updated 0.22 min ago |
| Order Submission Logging | ✅ PASS | 937 recent orders |

**Verification:** Trade execution is working correctly.

**Recent Trading Activity:**
- 50 trades in last 2 hours
- Active order execution
- Positions being opened and closed

---

### ❌ 6. TELEMETRY & COMPUTED ARTIFACTS - NOT RUNNING

| Component | Status | Details |
|-----------|--------|---------|
| Telemetry Extraction Script | ⚠️ EXISTS | `scripts/run_full_telemetry_extract.py` exists |
| Telemetry Extraction Scheduled | ❌ FAIL | Not in crontab |
| Last Telemetry Run | ❌ STALE | 65.7 hours ago (2026-01-24) |
| Computed Artifacts Status | ❌ STALE/MISSING | See details below |

**Computed Artifacts Status:**

**STALE (65.3 hours old):**
1. `exit_intel_completeness.json` - 3,217 bytes
2. `feature_equalizer_builder.json` - 774 bytes
3. `feature_value_curves.json` - 3,732 bytes
4. `long_short_analysis.json` - 777 bytes
5. `regime_sector_feature_matrix.json` - 138 bytes
6. `regime_timeline.json` - 12,211 bytes
7. `replacement_telemetry_expanded.json` - 721 bytes
8. `score_distribution_curves.json` - 161,782 bytes
9. `signal_performance.json` - 554 bytes
10. `signal_weight_recommendations.json` - 301 bytes

**MISSING:**
1. `entry_parity_details.json`
2. `feature_family_summary.json`
3. `live_vs_shadow_pnl.json`
4. `shadow_vs_live_parity.json`

**Root Cause:**
- `scripts/run_full_telemetry_extract.py` exists but is not scheduled
- No cron job or scheduled task to run telemetry extraction
- Last run was 65.7 hours ago (2026-01-24)
- Dashboard correctly shows stale/missing status

---

## Issues Found

### 🔴 CRITICAL (Affects Analysis/Monitoring):

1. **Telemetry Extraction Not Scheduled**
   - **Impact:** Computed artifacts not being generated
   - **Details:** `run_full_telemetry_extract.py` not in crontab
   - **Last Run:** 65.7 hours ago
   - **Fix Required:** Schedule daily telemetry extraction

2. **Computed Artifacts Stale (10 artifacts)**
   - **Impact:** Dashboard shows stale data (65+ hours old)
   - **Details:** All artifacts from 2026-01-24, not updated since
   - **Fix Required:** Run telemetry extraction to generate fresh artifacts

3. **Computed Artifacts Missing (4 artifacts)**
   - **Impact:** Dashboard shows missing data
   - **Details:** `entry_parity_details`, `feature_family_summary`, `live_vs_shadow_pnl`, `shadow_vs_live_parity`
   - **Fix Required:** Run telemetry extraction to generate missing artifacts

### ✅ WORKING (No Issues):

- All core trading processes
- Signal capture and processing
- Exit criteria evaluation
- Trade execution
- All logging systems

---

## Proposed Fixes

### Issue 1: Telemetry Extraction Not Scheduled

**Problem:** `scripts/run_full_telemetry_extract.py` is not scheduled to run automatically.

**Proposed Fix:**
1. **Schedule Daily Telemetry Extraction:**
   ```bash
   # Add to crontab (runs daily at 4:30 PM ET / 20:30 UTC after market close)
   30 20 * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py >> logs/telemetry_extract.log 2>&1
   ```

2. **Or Run Immediately to Generate Fresh Artifacts:**
   ```bash
   cd /root/stock-bot
   /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py
   ```

3. **Verify Script Works:**
   - Check if script runs without errors
   - Verify artifacts are generated in `telemetry/YYYY-MM-DD/computed/`
   - Check dashboard updates after generation

**Expected Result:**
- Fresh artifacts generated daily
- Dashboard shows "healthy" status (< 6 hours old)
- All 14 artifacts present and recent

---

### Issue 2: Stale Computed Artifacts

**Problem:** 10 artifacts are 65.3 hours old (from 2026-01-24).

**Proposed Fix:**
1. **Run Telemetry Extraction Now:**
   ```bash
   cd /root/stock-bot
   /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py
   ```

2. **Verify Artifacts Updated:**
   - Check `telemetry/2026-01-26/computed/` directory
   - Verify all artifacts have recent timestamps
   - Check dashboard shows "healthy" status

**Expected Result:**
- All artifacts updated to today's date
- Dashboard shows recent data (< 6 hours old)
- Signal performance and recommendations updated

---

### Issue 3: Missing Computed Artifacts

**Problem:** 4 artifacts are completely missing:
- `entry_parity_details.json`
- `feature_family_summary.json`
- `live_vs_shadow_pnl.json`
- `shadow_vs_live_parity.json`

**Proposed Fix:**
1. **Check if Script Generates These:**
   - Review `scripts/run_full_telemetry_extract.py` to see if it generates these artifacts
   - Check if they require additional scripts or data

2. **Run Full Telemetry Extraction:**
   ```bash
   cd /root/stock-bot
   /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py
   ```

3. **If Still Missing:**
   - Check if these artifacts require shadow trading data
   - Verify if shadow trading is enabled
   - Check if additional scripts are needed

**Expected Result:**
- Missing artifacts generated (if supported)
- Or artifacts marked as "not applicable" if shadow trading disabled

---

## Verification Against Memory Bank

### Reference Documentation Checked:
1. ✅ `COMPLETE_BOT_REFERENCE.md` - All 22 signal components
2. ✅ `TRADING_BOT_COMPLETE_SOP.md` - Complete workflow
3. ✅ `TRADE_WORKFLOW_ANALYSIS.md` - Trade flow steps
4. ✅ `ALPACA_TRADING_BOT_WORKFLOW.md` - Exit criteria

### Actual vs Expected:

#### Core Trading Flow
- **Expected:** Signal capture → Processing → Execution → Exit → Logging
- **Actual:** ✅ All working correctly
- **Status:** OPERATIONAL

#### Telemetry/Analysis
- **Expected:** Daily telemetry extraction generates computed artifacts
- **Actual:** ❌ Not scheduled, last run 65.7 hours ago
- **Status:** NOT RUNNING

---

## Conclusion

**Core Trading System:** ✅ **FULLY OPERATIONAL**
- All processes running
- Signal capture working
- Exit criteria working
- Logging systems active
- Active trading (50 trades in last 2h)

**Analysis/Telemetry System:** ❌ **NOT RUNNING**
- Telemetry extraction not scheduled
- Computed artifacts stale (65+ hours)
- 4 artifacts missing
- Dashboard correctly showing stale/missing status

**The dashboard is correct** - the data IS stale/missing because the telemetry extraction process hasn't run in 65.7 hours and is not scheduled.

---

## Immediate Action Required

1. **Run Telemetry Extraction Now:**
   ```bash
   cd /root/stock-bot
   /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py
   ```

2. **Schedule Daily Telemetry Extraction:**
   ```bash
   # Add to crontab
   crontab -e
   # Add line:
   30 20 * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python3 scripts/run_full_telemetry_extract.py >> logs/telemetry_extract.log 2>&1
   ```

3. **Verify After Running:**
   - Check `telemetry/2026-01-26/computed/` directory
   - Verify artifacts are fresh (< 6 hours old)
   - Check dashboard updates

---

**Report Generated:** 2026-01-26T20:04:07+00:00  
**Audit Method:** Direct droplet inspection  
**Full Results:** `reports/droplet_audit_results.json`, `reports/telemetry_artifacts_status.json`
