# Code Cleanup Plan

**Date:** 2025-12-26  
**Purpose:** Remove unused code to prevent confusion and reduce maintenance burden

## Analysis Results

### 1. Investigation/Test Scripts: 131 files
**Status:** These are temporary debugging/investigation scripts that should be archived or removed.

**Categories:**
- **Investigation scripts** (diagnose_*, investigate_*)
- **Fix scripts** (fix_*)
- **Verification scripts** (verify_*, check_*)
- **Test scripts** (test_*)
- **Audit scripts** (audit_*, COMPLETE_*, FULL_*)

**Recommendation:** Archive to `archive/investigation_scripts/` or remove if no longer needed.

### 2. Potentially Unused Definitions in main.py: 52
**Status:** Need manual review - some may be used indirectly.

**Examples found:**
- `record_trade_for_learning` (line 87)
- `log_postmortem` (line 616)
- `auto_rearm_kill_switch` (line 648)
- `is_market_open_now_old` (line 834) - **Clearly old/unused**
- `update_bandit` (line 1745)
- `SmartPoller` (line 1780)
- `extract_bucket_pnls` (line 2192)
- `should_run_experiment` (line 2320)
- `try_promotion_if_ready` (line 2329)
- Various dashboard/API functions that may be unused

**Recommendation:** Review each and remove if truly unused.

### 3. Large Comment Blocks: 8
**Status:** May contain old code or documentation.

**Recommendation:** Review and either uncomment if needed or remove.

### 4. Shadow Lab Code
**Status:** `ENABLE_SHADOW_LAB` is used 8 times but may not be actively used.

**Recommendation:** Verify if shadow lab is actually being used, if not, consider removing.

## Cleanup Strategy

### Phase 1: Archive Investigation Scripts (Safe)
Move all investigation/test scripts to `archive/` directory.

### Phase 2: Review and Remove Unused Functions (Careful)
Manually review each potentially unused function in main.py.

### Phase 3: Remove Commented Code (Safe)
Remove large blocks of commented code after verification.

### Phase 4: Remove Dead Features (Careful)
Remove features that are disabled and never used (e.g., shadow lab if disabled).

## Files to Keep (Active)

**Core System:**
- `main.py` - Main trading bot
- `dashboard.py` - Dashboard
- `uw_flow_daemon.py` - UW data daemon
- `deploy_supervisor.py` - Service supervisor
- `heartbeat_keeper.py` - Health monitoring

**Trading Readiness System (NEW - KEEP):**
- `failure_point_monitor.py`
- `trading_readiness_test_harness.py`
- `inject_fake_signal_test.py`
- `automated_trading_verification.py`
- `continuous_fp_monitoring.py`
- `investigate_blocked_status.py`
- `fix_blocked_readiness.py`
- `verify_readiness_simple.py`

**Core Modules:**
- `uw_composite_v2.py`
- `uw_enrichment_v2.py`
- `adaptive_signal_optimizer.py`
- `self_healing_threshold.py`
- All modules in `signals/`, `execution/`, `learning/`, `structural_intelligence/`, etc.

## Files to Archive/Remove

**Investigation Scripts (131 files)** - Archive to `archive/investigation_scripts/`

**Potentially Unused Functions in main.py** - Review and remove:
- `is_market_open_now_old` - Clearly old version
- Functions that are never called

## Implementation

See `cleanup_unused_code.py` for automated cleanup script.

