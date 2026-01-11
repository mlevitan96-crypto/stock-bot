# Archive Index

**Last Updated:** 2026-01-09  
**Purpose:** Comprehensive index of all archived files, their locations, and how to restore them if needed

---

## Overview

This archive contains **557 files** that were archived during the repository cleanup process. These files are no longer actively used in the codebase but are preserved for historical reference, troubleshooting, and potential future use.

### Archive Statistics

- **Documentation Files:** 193 markdown (.md) files
- **Deployment Scripts:** 165 shell (.sh) scripts
- **Diagnostic Scripts:** 70 Python (.py) scripts
- **Investigation Scripts:** 125 files (pre-existing archive)
- **Data Files:** 3 JSON files
- **Total:** 557 files

---

## Archive Structure

```
archive/
├── ARCHIVE_INDEX.md              # This file - master index
├── README.md                     # Archive overview and structure
├── documentation/
│   ├── completion_summaries/     # 100+ files - Completed work summaries
│   ├── deployment_guides/        # 50+ files - One-time deployment guides
│   └── status_reports/           # 30+ files - Historical status reports
├── scripts/
│   ├── deployment_scripts/       # 165 files - One-time deployment scripts
│   └── diagnostic_scripts/       # 70+ files - Diagnostic/test scripts
├── investigation_scripts/        # 125 files - Pre-existing investigation scripts
└── data/                         # 3 files - Historical data/output files
```

---

## What Was Archived and When

### Phase 1-3: Deletions (2026-01-09)
**Status:** Completed

- **7 Temporary Trigger Files** - Deleted (not archived)
  - `.deploy_now`, `.investigation_trigger`, `.last_investigation_run`, `.trigger_complete_verification`, `.trigger_final_verification`, `.trigger_uw_test`, `.trigger_uw_test_now`
  - **Reason:** Empty automation flag files, no longer needed

- **1 Duplicate Module** - Deleted (not archived)
  - `uw_integration_full.py`
  - **Reason:** Duplicate of `uw_composite_v2.py`, never imported or used

- **2 Patch Files** - Deleted (not archived)
  - `audit_fixes_core.diff`, `audit_fixes.patch`
  - **Reason:** Code change artifacts, no longer needed

### Phase 4: Archive Structure Created (2026-01-09)
**Status:** Completed

Created organized directory structure for archiving files by category.

### Phase 5: Documentation Files Archived (2026-01-09)
**Status:** Completed - 193 files archived

**Location:** `archive/documentation/`

#### Completion Summaries (`completion_summaries/`) - ~100 files
- **Pattern:** `*_COMPLETE*.md`, `*_FIX*.md`, `*_SUMMARY*.md`
- **Examples:**
  - `ADAPTIVE_WEIGHTS_BUG_FIX.md`
  - `ALL_FIXES_COMPLETE_SUMMARY.md`
  - `AUDIT_FIXES_COMPLETE.md`
  - `BACKTEST_FIX_COMPLETE.md`
  - `BULLETPROOF_HARDENING_COMPLETE.md`
  - `COMPLETE_AUDIT_AND_DEPLOYMENT_SUMMARY.md`
  - `FINAL_COMPLETE_VERIFICATION_REPORT.md`
  - Many more...
- **Why Archived:** Historical records of completed work, resolved issues, and finished audits
- **Keep Active:** `MEMORY_BANK.md`, `README.md`, `CONTEXT.md`, `TRADING_BOT_COMPLETE_SOP.md`, `COMPLETE_BOT_REFERENCE.md`, `TROUBLESHOOTING_GUIDE.md`

#### Deployment Guides (`deployment_guides/`) - ~50 files
- **Pattern:** `DEPLOY_*.md`, `FIX_*.md` (deployment-related), `APPLY_*.md`
- **Examples:**
  - `DEPLOYMENT_COMPLETE.md`
  - `DEPLOYMENT_SUMMARY.md`
  - `FIX_AND_DEPLOY.md`
  - `APPLY_FIX_NOW.md`
- **Why Archived:** One-time deployment instructions for specific issues/features that are now complete

#### Status Reports (`status_reports/`) - ~30 files
- **Pattern:** `*_STATUS_REPORT.md`, `*_REPORT.md`
- **Examples:**
  - `BOT_STATUS_REPORT.md`
  - `DROPLET_STATUS_REPORT.md`
  - `SYSTEM_STATUS_REPORT.md`
  - `TRADING_STATUS_REPORT.md`
- **Why Archived:** Historical status snapshots from specific dates, no longer needed for operations

### Phase 6: Shell Scripts Archived (2026-01-09)
**Status:** Completed - 165 files archived

**Location:** `archive/scripts/deployment_scripts/`

- **Pattern:** `APPLY_FIX_*.sh`, `CHECK_*.sh`, `AUTO_RUN_*.sh`, `FIX_*.sh`, `DEPLOY_*.sh`, `VERIFY_*.sh`
- **Examples:**
  - `APPLY_FIX_NOW.sh`
  - `CHECK_BOT_STATUS.sh`
  - `AUTO_RUN_FINAL_VERIFICATION.sh`
  - `FIX_AND_DEPLOY.sh`
  - `DEPLOY_NOW.sh`
  - Many more...
- **Why Archived:** One-time deployment, verification, or diagnostic scripts that are no longer needed
- **Keep Active:** `systemd_start.sh` (used by systemd service), `start.sh` (manual startup), `guardian_wrapper.sh` (used by cron)

### Phase 7: Diagnostic Python Scripts Archived (2026-01-09)
**Status:** Completed - 70+ files archived

**Location:** `archive/scripts/diagnostic_scripts/`

- **Pattern:** `check_*.py`, `test_*.py`, `diagnose_*.py`, `investigate_*.py`, `verify_*.py`
- **Examples:**
  - `check_bot_status.py`
  - `check_positions.py`
  - `test_alpaca_api_direct.py`
  - `diagnose_current_issues.py`
  - `investigate_blocked_status.py`
  - `verify_deployment.py`
  - Many more...
- **Why Archived:** Diagnostic/test scripts not imported by core active code (`main.py`, `deploy_supervisor.py`)
- **Keep Active:** Core modules imported by `main.py`:
  - `main.py`, `dashboard.py`, `deploy_supervisor.py`
  - `uw_flow_daemon.py`, `heartbeat_keeper.py`
  - `position_reconciliation_loop.py`, `startup_contract_check.py`
  - `risk_management.py`, `momentum_ignition_filter.py`
  - `comprehensive_learning_scheduler.py`
  - `v4_orchestrator.py`, `v2_nightly_orchestration_with_auto_promotion.py`

### Phase 8: JSON Data Files Archived (2026-01-09)
**Status:** Completed - 3 files archived

**Location:** `archive/data/`

- **Files:**
  - `audit_report.json` - Historical audit report data
  - `backtest_results.json` - Historical backtest results
  - `droplet_verification_results.json` - Historical verification data
- **Why Archived:** Historical/generated output files, not actively read as inputs by core code
- **Note:** Some diagnostic scripts may check for their existence or generate them, but don't rely on these specific historical files

### Pre-Existing Archive: Investigation Scripts
**Location:** `archive/investigation_scripts/`

- **Files:** 125 files (124 Python scripts, 1 JSON)
- **Status:** Pre-existing archive, already organized
- **Purpose:** Investigation and debugging scripts from previous cleanup efforts

---

## Why Files Were Archived

Files were archived rather than deleted because they:

1. **Have Historical Value** - Document completed work, resolved issues, or past configurations
2. **May Be Needed for Troubleshooting** - Reference for understanding past problems and solutions
3. **Could Be Useful for Future Work** - Examples of past implementations or patterns
4. **Are Safe to Remove from Active Directory** - Not imported, referenced, or executed by active code
5. **Clutter the Root Directory** - Moving them improves repository organization and discoverability

**Archiving vs. Deleting:** All files were archived (moved) rather than deleted so they remain accessible in git history and can be restored if needed.

---

## How to Find Archived Files

### By Category

1. **Completion Summaries:** `archive/documentation/completion_summaries/`
2. **Deployment Guides:** `archive/documentation/deployment_guides/`
3. **Status Reports:** `archive/documentation/status_reports/`
4. **Deployment Scripts:** `archive/scripts/deployment_scripts/`
5. **Diagnostic Scripts:** `archive/scripts/diagnostic_scripts/`
6. **Investigation Scripts:** `archive/investigation_scripts/`
7. **Data Files:** `archive/data/`

### By Pattern

Use these commands to find specific files:

```bash
# Find all completion summaries
find archive/documentation/completion_summaries -name "*COMPLETE*.md"

# Find all deployment scripts
find archive/scripts/deployment_scripts -name "DEPLOY_*.sh"

# Find all diagnostic scripts
find archive/scripts/diagnostic_scripts -name "check_*.py"

# Find files by keyword
grep -r "keyword" archive/
```

### By Original Location

Since files were moved from the root directory, you can use git history to find where they were originally located:

```bash
# See where a file was before archiving
git log --follow --all -- archive/path/to/file

# See all files moved to archive
git log --diff-filter=R --summary -- archive/
```

---

## How to Restore Archived Files

### Option 1: Copy from Archive (Recommended)

Simply copy the file back to its original location or desired location:

```bash
# Restore a specific file
cp archive/documentation/completion_summaries/FILE.md .

# Restore multiple files
cp archive/scripts/diagnostic_scripts/check_*.py .

# Restore entire directory
cp -r archive/scripts/deployment_scripts ./restored_scripts/
```

### Option 2: Move from Archive (Use with Caution)

If you're sure the file is needed, you can move it back:

```bash
# Move file back (removes from archive)
mv archive/documentation/completion_summaries/FILE.md .
```

**Warning:** Only move files if you're certain they're needed. Consider copying first.

### Option 3: Restore from Git History

If the file was deleted during cleanup, you can restore it from git:

```bash
# Find the commit where it was deleted
git log --all --full-history -- archive/path/to/file

# Restore from that commit
git checkout <commit-hash>^ -- path/to/file

# Or restore from before cleanup
git checkout HEAD~1 -- path/to/file
```

### Option 4: Search in Git History

All archived files are still in git history, so you can search for them:

```bash
# Find all versions of a file in git history
git log --all --full-history -- "**/filename.ext"

# See contents from a specific commit
git show <commit-hash>:path/to/file
```

---

## Active Files (Not Archived)

The following files remain in the root directory because they are actively used:

### Core System Files
- `main.py` - Main trading bot
- `dashboard.py` - Web dashboard
- `deploy_supervisor.py` - Service supervisor
- `uw_flow_daemon.py` - UW data daemon
- `heartbeat_keeper.py` - Health monitoring

### Active Documentation
- `MEMORY_BANK.md` - Primary knowledge base
- `README.md` - Project readme
- `CONTEXT.md` - Quick project overview
- `TRADING_BOT_COMPLETE_SOP.md` - Standard operating procedures
- `COMPLETE_BOT_REFERENCE.md` - Complete bot reference
- `TROUBLESHOOTING_GUIDE.md` - Troubleshooting guide

### Active Scripts
- `systemd_start.sh` - Used by systemd service
- `start.sh` - Manual startup script
- `guardian_wrapper.sh` - Used by cron jobs

### Core Modules
All modules imported by `main.py` or `deploy_supervisor.py` remain active:
- `position_reconciliation_loop.py`
- `startup_contract_check.py`
- `risk_management.py`
- `momentum_ignition_filter.py`
- `comprehensive_learning_scheduler.py`
- All modules in `signals/`, `config/`, `telemetry/`, `xai/`, `api_management/`, etc.

### PowerShell Scripts (Windows Development)
- `setup_windows.ps1` - Windows setup helper
- `add_git_to_path.ps1` - Git PATH helper
- `check_status.ps1` - Diagnostic tool

**Reason:** Windows development is active, these scripts are useful helpers.

---

## Verification

After archiving, the following verifications were completed:

- ✅ **No Broken Imports** - All core files import correctly
- ✅ **No Broken References** - References to deleted files are harmless (process checks, grep patterns, utility scripts)
- ✅ **Core Functionality** - `main.py`, `deploy_supervisor.py`, `dashboard.py` verified
- ✅ **Git Status** - All changes properly tracked

See `CLEANUP_CHECKLIST.md` Phase 10 for complete verification details.

---

## Archive Maintenance

### When to Add Files to Archive

Consider archiving files when they:
- Document completed work or resolved issues
- Are one-time deployment/verification scripts
- Are diagnostic scripts not used by core code
- Are historical reports or snapshots
- Are no longer imported or referenced
- Clutter the root directory

### When NOT to Archive

Do NOT archive files that:
- Are imported by `main.py`, `deploy_supervisor.py`, or `dashboard.py`
- Are referenced by systemd services or cron jobs
- Are active documentation (see "Active Files" section above)
- Are core system modules
- Are actively maintained

---

## Related Documentation

- **`REPOSITORY_AUDIT_REPORT.md`** - Complete audit report with detailed analysis
- **`REPOSITORY_AUDIT_SUMMARY.md`** - Quick reference summary
- **`CLEANUP_CHECKLIST.md`** - Step-by-step cleanup checklist
- **`archive/README.md`** - Archive directory overview

---

## Questions or Issues

If you need to restore files, have questions about what was archived, or find issues:

1. Check this index first
2. Review `REPOSITORY_AUDIT_REPORT.md` for detailed reasons
3. Search git history if file location is unclear
4. All files are in git history and can be restored

---

**Archive Created:** 2026-01-09  
**Last Verified:** 2026-01-09  
**Total Files Archived:** 557 files
