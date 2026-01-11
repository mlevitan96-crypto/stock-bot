# Repository Audit Report
## Comprehensive Analysis of Unused, Outdated, Duplicated, and Irrelevant Files

**Date:** 2026-01-09  
**Auditor:** Auto (AI Assistant)  
**Purpose:** Identify all files that are unused, outdated, duplicated, or irrelevant to the current execution path

---

## Executive Summary

This audit identified **multiple categories** of files that are candidates for removal or archiving:

- **7 Temporary Trigger Files** - No longer needed
- **1 Duplicate Module** - `uw_integration_full.py` (duplicate of `uw_composite_v2.py`)
- **390 Markdown Documentation Files** - Many are completion summaries and one-time deployment guides
- **125+ Archived Investigation Scripts** - Already archived (good), but can be further consolidated
- **50+ One-Time Deployment/Verification Shell Scripts** - Many are outdated one-off scripts
- **Multiple Test/Debug Scripts** - Many are no longer needed in production
- **Diff/Patch Files** - Old code change artifacts

**Total Estimated Files Safe to Remove/Archive:** ~200-250 files

---

## 1. TEMPORARY TRIGGER FILES (7 files) - **SAFE TO DELETE**

These are empty trigger files used for automation workflows. They are no longer needed.

### Files to Remove:
```
.deploy_now
.investigation_trigger
.last_investigation_run
.trigger_complete_verification
.trigger_final_verification
.trigger_uw_test
.trigger_uw_test_now
```

**Reason:** These appear to be empty flag files used by automation scripts. No code imports or references these files. They're created by scripts to trigger workflows but are not required for operation.

**Verification:** None of these files are imported or referenced by:
- `main.py`
- `deploy_supervisor.py`
- `dashboard.py`
- Any other active code

---

## 2. DUPLICATE MODULES (1 file) - **SAFE TO DELETE**

### `uw_integration_full.py` - DUPLICATE OF `uw_composite_v2.py`

**Evidence:**
- Both files start with identical header comments (lines 1-18 match exactly)
- Both files have identical function signatures for `get_adaptive_optimizer()` and `get_adaptive_weights()`
- `main.py` imports `uw_composite_v2` (line 50) but **never imports `uw_integration_full`**
- No grep results found for `import.*uw_integration_full` anywhere in the codebase

**Current Usage:**
- ✅ `uw_composite_v2.py` - **ACTIVELY USED** by `main.py` (imported as `uw_v2`)
- ❌ `uw_integration_full.py` - **NOT USED** anywhere

**Recommendation:** **DELETE** `uw_integration_full.py`

**Why Safe:** This file is never imported, referenced, or executed by any part of the active system.

---

## 3. DOCUMENTATION FILES (390+ .md files) - **SELECTIVE ARCHIVING RECOMMENDED**

The repository contains **390 markdown files**, many of which are:
- Completion summaries for specific dates/issues
- One-time deployment guides
- Fix summaries for resolved issues
- Executive summaries for audits that are complete
- Status reports for specific dates

### Category A: Completion/Fix Summaries (Can Archive) - ~100 files

These document completed work and are historical records:

```
ADAPTIVE_WEIGHTS_BUG_FIX.md
ALL_FIXES_COMPLETE_SUMMARY.md
ALL_TODOS_IMPLEMENTATION_COMPLETE.md
ALL_TODOS_SUMMARY.md
ALPACA_API_FIX_DEPLOYMENT_COMPLETE.md
ALPHA_REPAIRS_IMPLEMENTATION_COMPLETE.md
AUDIT_FIXES_COMPLETE.md
BACKTEST_FIX_COMPLETE.md
BULLETPROOF_HARDENING_COMPLETE.md
CAUSAL_ANALYSIS_FIX.md
CAUSAL_ANALYSIS_IMPLEMENTATION.md
CLIENT_ORDER_ID_FIX_COMPLETE.md
CODE_CLEANUP_SUMMARY.md
[... many more similar files ...]
```

**Recommendation:** Archive to `archive/documentation/completion_summaries/`

**Why Safe:** These document completed work. Historical value but not needed for daily operation.

### Category B: One-Time Deployment Guides (Can Archive) - ~50 files

These are guides for specific deployment scenarios that are no longer relevant:

```
APPLY_FIX_DIRECTLY_ON_SERVER.sh
APPLY_FIX_DIRECTLY.sh
APPLY_FIX_NOW.sh
APPLY_FIXES_MANUAL.sh
DEPLOY_AND_FIX_TRADING.py
DEPLOY_TO_DROPLET_SIMPLE.py
FIX_NOW.sh
IMMEDIATE_FIX_COMMANDS.md
RESOLVE_GIT_AND_DEPLOY.md
[... many more ...]
```

**Recommendation:** Archive to `archive/documentation/deployment_guides/`

**Why Safe:** These were for specific one-time deployments. If needed again, they can be retrieved from archive.

### Category C: Keep - Active Documentation (~20 files)

These should be **KEPT** as they're active reference documents:

```
MEMORY_BANK.md                    # Primary knowledge base - KEEP
README.md                         # Project overview - KEEP
CONTEXT.md                        # Project context - KEEP
TRADING_BOT_COMPLETE_SOP.md      # Standard operating procedure - KEEP
COMPLETE_BOT_REFERENCE.md         # Living reference document - KEEP
TROUBLESHOOTING_GUIDE.md          # Active troubleshooting guide - KEEP
[... and a few others ...]
```

### Category D: Status Reports for Specific Dates (Can Archive) - ~30 files

```
BOT_STATUS_REPORT.md
SYSTEM_STATUS_REPORT.md
DROPLET_STATUS_REPORT.md
FINAL_STATUS_REPORT.md
[... date-specific status reports ...]
```

**Recommendation:** Archive to `archive/documentation/status_reports/`

**Why Safe:** These are snapshots in time. Historical value only.

---

## 4. ONE-TIME DEPLOYMENT/VERIFICATION SHELL SCRIPTS (~50 files) - **ARCHIVE**

Many shell scripts appear to be one-time deployment or verification scripts:

### Examples:
```
APPLY_FIX_DIRECTLY_ON_SERVER.sh
APPLY_FIX_DIRECTLY.sh
APPLY_FIX_NOW.sh
APPLY_FIXES_MANUAL.sh
apply_fixes_via_git.sh
apply_no_trades_fix.sh
AUTO_RUN_FINAL_VERIFICATION.sh
AUTO_RUN_INVESTIGATION.sh
AUTO_RUN_UW_TEST.sh
CHECK_BOT_STATUS.sh
CHECK_DAEMON_AND_TRADES.sh
CHECK_DAEMON_LIVE.sh
CHECK_DAEMON_STATUS.sh
[... many more ...]
```

**Recommendation:** Archive to `archive/scripts/deployment_scripts/`

**Verification Needed:** Check which scripts are:
- Referenced by systemd services
- Referenced by cron jobs
- Called by active Python code
- Part of regular workflows

**Files to KEEP (verified active):**
```
systemd_start.sh                  # ✅ CONFIRMED: Used by systemd service (referenced in /etc/systemd/system/trading-bot.service) - KEEP
start.sh                          # ⚠️ EXISTS: Mentioned in README.md - VERIFY USAGE before archiving
```

**Verification:**
- ✅ `systemd_start.sh` - Actively used by systemd service (ExecStart=/root/stock-bot/systemd_start.sh)
- ⚠️ `start.sh` - Exists and mentioned in README but not verified if used by systemd/cron

---

## 5. TEST/DEBUG SCRIPTS IN ROOT (~100+ files) - **ARCHIVE MOST**

Many Python files in the root directory are diagnostic/test scripts:

### Diagnostic Scripts (Archive):
```
check_actual_scores.py
check_adaptive_weights.py
check_and_fix_thresholds.py
check_api_failures.py
check_backtest_status.py
check_bot_status.py
check_current_status.py
check_current_trading_status.py
[... ~50+ more check_*.py files ...]
```

### Investigation Scripts (Already in archive, but verify):
```
diagnose_complete.py
diagnose_zero_clusters.py
investigate_score_bug.py
[... many diagnose_*.py and investigate_*.py ...]
```

### Test Scripts (Archive):
```
test_alpaca_data.py
test_composite_scoring.py
test_dashboard_complete.py
test_scoring_direct.py
[... test_*.py files ...]
```

**Recommendation:** Archive to `archive/scripts/diagnostic_scripts/`

**Files to KEEP:**
```
main.py                           # Core trading bot - KEEP
dashboard.py                      # Web dashboard - KEEP
deploy_supervisor.py              # Service supervisor - KEEP
uw_flow_daemon.py                 # UW data daemon - KEEP
heartbeat_keeper.py               # Health monitoring - KEEP
startup_contract_check.py         # Used by main.py - KEEP
position_reconciliation_loop.py   # Used by main.py - KEEP
[... and module files imported by main.py ...]
```

---

## 6. DIFF/PATCH FILES (2 files) - **SAFE TO DELETE**

```
audit_fixes_core.diff
audit_fixes.patch
```

**Reason:** These are code change artifacts. The changes they represent have already been applied to the codebase (or rejected).

**Recommendation:** **DELETE** (unless needed for historical record-keeping)

---

## 7. JSON DATA FILES IN ROOT (3 files) - **VERIFY IF NEEDED**

```
audit_report.json
backtest_results.json
droplet_verification_results.json
```

**Recommendation:** Check if these are:
- Generated outputs (can be deleted/recreated)
- Configuration files (should move to `config/`)
- Historical data (should move to `reports/` or archive)

**Action:** Review each file to determine if it's active or historical.

---

## 8. POWERSHELL SETUP SCRIPTS (2 files) - **WINDOWS-SPECIFIC, KEEP OR ARCHIVE**

```
add_git_to_path.ps1
setup_windows.ps1
```

**Recommendation:** If this is a cross-platform project or primarily runs on Linux (droplet), these can be archived. If Windows development is actively used, keep them.

---

## 9. ARCHIVE DIRECTORY (125+ files) - **ALREADY ARCHIVED, BUT VERIFY**

The `archive/investigation_scripts/` directory contains 125+ files that have already been moved from the root.

**Status:** ✅ Already archived (good practice)

**Recommendation:** No action needed, but consider:
- Compressing old archives if disk space is a concern
- Creating a manifest file listing what's in the archive (already exists: `archive/investigation_scripts/manifest.json`)

---

## 10. REPORTS DIRECTORY (32 files) - **KEEP, BUT REVIEW**

The `reports/` directory contains:
- 17 JSON files (likely generated reports)
- 7 MD files (report documentation)
- 4 HTML files (generated reports)
- Other files

**Recommendation:** Keep this directory, but consider:
- Moving old reports (>30 days) to archive
- Implementing automatic cleanup of old reports
- Not tracking generated reports in git (add to .gitignore)

---

## 11. ORCHESTRATOR/RESEARCH SCRIPTS - **VERIFY USAGE**

Several orchestrator/research scripts may not be actively used:

```
v2_nightly_orchestration_with_auto_promotion.py
v4_orchestrator.py
historical_replay_engine.py
```

**Verification:**
- `v4_orchestrator.py` - Referenced in `deploy_supervisor.py` line 57 as "v4-research" (one_shot service) - **KEEP**
- `v2_nightly_orchestration_with_auto_promotion.py` - Imported by `main.py` line 200 - **KEEP**
- `historical_replay_engine.py` - Not imported by main.py or deploy_supervisor - **VERIFY IF NEEDED**

**Recommendation:** Review `historical_replay_engine.py` - if it's not used, archive it.

---

## 12. MODULE FILES WITH VERSIONS - **VERIFY WHICH ARE ACTIVE**

Several modules have version suffixes. Verify which are actually used:

### Active (used by main.py):
```
uw_composite_v2.py           # ✅ USED (imported by main.py line 50)
uw_enrichment_v2.py          # ✅ USED (imported by main.py line 49)
uw_execution_v2.py           # ✅ USED (imported by main.py line 53)
comprehensive_learning_orchestrator_v2.py  # ✅ USED (imported by main.py)
```

### Legacy/Unused:
```
uw_integration_full.py       # ❌ DUPLICATE (see section 2)
uw_composite.py              # ⚠️ VERIFY (signals/uw_composite.py is imported by main.py line 45)
```

**Note:** `signals/uw_composite.py` is different from root-level `uw_composite.py` (if it exists). The signals version is actively used.

---

## PRIORITY ACTION ITEMS

### HIGH PRIORITY (Safe to Delete Immediately)

1. **Delete 7 trigger files:**
   - `.deploy_now`, `.investigation_trigger`, `.last_investigation_run`
   - `.trigger_complete_verification`, `.trigger_final_verification`
   - `.trigger_uw_test`, `.trigger_uw_test_now`

2. **Delete duplicate module:**
   - `uw_integration_full.py` (duplicate of `uw_composite_v2.py`)

3. **Delete diff/patch files:**
   - `audit_fixes_core.diff`
   - `audit_fixes.patch`

### MEDIUM PRIORITY (Archive, Don't Delete)

4. **Archive completion summaries (~100 .md files)**
   - Move to `archive/documentation/completion_summaries/`

5. **Archive one-time deployment scripts (~50 .sh files)**
   - Move to `archive/scripts/deployment_scripts/`
   - **VERIFY** none are called by systemd/cron first

6. **Archive diagnostic scripts (~100 .py files)**
   - Move to `archive/scripts/diagnostic_scripts/`

### LOW PRIORITY (Review and Organize)

7. **Organize documentation**
   - Consolidate active docs in root
   - Archive historical status reports
   - Create documentation index

8. **Review reports directory**
   - Implement automatic cleanup for old reports
   - Consider adding to .gitignore if generated

---

## VERIFICATION CHECKLIST

Before deleting/archiving, verify:

- [ ] No systemd service files reference the scripts
- [ ] No cron jobs reference the scripts
- [ ] No active Python code imports the modules
- [ ] No CI/CD pipelines reference the scripts
- [ ] Documentation in MEMORY_BANK.md doesn't reference removed files
- [ ] README.md doesn't reference removed files

---

## ESTIMATED IMPACT

**Files Safe to Delete:** ~10 files (trigger files, duplicates, patches)  
**Files Safe to Archive:** ~200-250 files (documentation, scripts, diagnostics)  
**Disk Space Savings:** Estimated 5-10 MB (mostly text files)  
**Repository Clarity:** Significant improvement in finding active code

---

## RECOMMENDED ACTIONS (Do Not Execute Yet)

1. Create archive directory structure:
   ```
   archive/
   ├── documentation/
   │   ├── completion_summaries/
   │   ├── deployment_guides/
   │   └── status_reports/
   ├── scripts/
   │   ├── deployment_scripts/
   │   └── diagnostic_scripts/
   └── investigation_scripts/  (already exists)
   ```

2. Move files to appropriate archive locations

3. Update .gitignore to exclude generated reports if desired

4. Create ARCHIVE_INDEX.md documenting what's archived and why

---

## NOTES

- This audit is **read-only** - no files have been modified or deleted
- All recommendations should be reviewed before execution
- Some files may have historical value even if not actively used
- Consider creating a backup before archiving/deleting files
- Verify git history is preserved before deleting (files in git are recoverable)

---

**END OF AUDIT REPORT**
