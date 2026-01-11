# Repository Audit - Quick Reference Summary

**Date:** 2026-01-09  
**Full Report:** See `REPOSITORY_AUDIT_REPORT.md` for complete analysis

---

## 🎯 Files Safe to DELETE (10 files)

### Trigger Files (7):
- `.deploy_now`
- `.investigation_trigger`
- `.last_investigation_run`
- `.trigger_complete_verification`
- `.trigger_final_verification`
- `.trigger_uw_test`
- `.trigger_uw_test_now`

### Duplicate Module (1):
- `uw_integration_full.py` (duplicate of `uw_composite_v2.py` - never imported)

### Patch Files (2):
- `audit_fixes_core.diff`
- `audit_fixes.patch`

---

## 📦 Files Safe to ARCHIVE (~200-250 files)

### Documentation Files (~180 .md files):
- Completion summaries (`*_COMPLETE.md`, `*_FIX.md`)
- One-time deployment guides (`DEPLOY_*.md`, `FIX_*.md`)
- Status reports for specific dates (`*_STATUS_REPORT.md`)

### Shell Scripts (~50 .sh files):
- One-time deployment scripts (`APPLY_*.sh`, `FIX_*.sh`)
- Verification scripts (`CHECK_*.sh`, `VERIFY_*.sh`)
- Auto-run scripts (`AUTO_RUN_*.sh`)

### Diagnostic Python Scripts (~100 .py files):
- Check scripts (`check_*.py`)
- Test scripts (`test_*.py`)
- Diagnose scripts (`diagnose_*.py`, `investigate_*.py`)

---

## ✅ Files to KEEP (Active Code)

### Core System Files:
- `main.py` - Main trading bot
- `dashboard.py` - Web dashboard  
- `deploy_supervisor.py` - Service supervisor
- `uw_flow_daemon.py` - UW data daemon
- `heartbeat_keeper.py` - Health monitoring

### Active Modules:
- `uw_composite_v2.py` - ✅ USED
- `uw_enrichment_v2.py` - ✅ USED
- `uw_execution_v2.py` - ✅ USED
- `comprehensive_learning_orchestrator_v2.py` - ✅ USED
- `v4_orchestrator.py` - ✅ USED (one-shot service)
- `v2_nightly_orchestration_with_auto_promotion.py` - ✅ USED

### Active Directories:
- `signals/` - Signal processing modules
- `config/` - Configuration files
- `learning/` - Learning system
- `structural_intelligence/` - SI modules
- `self_healing/` - Self-healing system
- `telemetry/` - Telemetry logging
- `xai/` - Explainable AI
- `api_management/` - API management

### Active Documentation:
- `MEMORY_BANK.md` - Primary knowledge base
- `README.md` - Project overview
- `CONTEXT.md` - Project context
- `TRADING_BOT_COMPLETE_SOP.md` - SOP
- `COMPLETE_BOT_REFERENCE.md` - Reference doc

---

## 📊 Statistics

- **Total .md files:** 390
- **Total .py files:** ~400+ (397 with shebang)
- **Total .sh files:** ~50+
- **Files in archive/:** 125+ (already archived ✅)
- **Safe to delete:** 10 files
- **Safe to archive:** ~200-250 files

---

## ⚠️ Before Executing Deletions

**VERIFY:**
1. No systemd services reference deleted scripts
2. No cron jobs reference deleted scripts  
3. No active Python code imports deleted modules
4. No CI/CD pipelines reference deleted scripts
5. Documentation doesn't reference removed files

---

## 🎬 Recommended Execution Order

1. **Phase 1:** Delete trigger files (safest)
2. **Phase 2:** Delete duplicate module (`uw_integration_full.py`)
3. **Phase 3:** Delete patch files
4. **Phase 4:** Create archive structure
5. **Phase 5:** Move documentation to archive
6. **Phase 6:** Move shell scripts to archive (after verification)
7. **Phase 7:** Move diagnostic scripts to archive
8. **Phase 8:** Update .gitignore if needed
9. **Phase 9:** Create ARCHIVE_INDEX.md

---

**For detailed analysis, see `REPOSITORY_AUDIT_REPORT.md`**
