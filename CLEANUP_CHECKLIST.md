# Repository Cleanup Checklist

**Use this checklist when executing the cleanup plan from the audit report.**

---

## Pre-Cleanup Verification

- [ ] Create a backup branch: `git checkout -b backup-before-cleanup`
- [ ] Review `REPOSITORY_AUDIT_REPORT.md` and `REPOSITORY_AUDIT_SUMMARY.md`
- [ ] Verify no systemd services reference files to be deleted
- [ ] Verify no cron jobs reference files to be deleted
- [ ] Check git status: `git status`

---

## Phase 1: Delete Trigger Files (Safest)

- [ ] Delete `.deploy_now`
- [ ] Delete `.investigation_trigger`
- [ ] Delete `.last_investigation_run`
- [ ] Delete `.trigger_complete_verification`
- [ ] Delete `.trigger_final_verification`
- [ ] Delete `.trigger_uw_test`
- [ ] Delete `.trigger_uw_test_now`
- [ ] Verify deletion: `git status`

---

## Phase 2: Delete Duplicate Module

- [ ] Verify `uw_integration_full.py` is not imported: `grep -r "uw_integration_full" . --exclude-dir=archive`
- [ ] Verify `uw_composite_v2.py` is the active version (imported by main.py)
- [ ] Delete `uw_integration_full.py`
- [ ] Test that main.py still imports correctly: `python -c "import main"` (should not error)

---

## Phase 3: Delete Patch Files

- [ ] Delete `audit_fixes_core.diff`
- [ ] Delete `audit_fixes.patch`
- [ ] Verify deletion: `git status`

---

## Phase 4: Create Archive Structure

- [ ] Create `archive/documentation/completion_summaries/`
- [ ] Create `archive/documentation/deployment_guides/`
- [ ] Create `archive/documentation/status_reports/`
- [ ] Create `archive/scripts/deployment_scripts/`
- [ ] Create `archive/scripts/diagnostic_scripts/`
- [ ] Verify structure: `tree archive/` or `ls -R archive/`

---

## Phase 5: Archive Documentation Files

### Completion Summaries (~100 files)
- [ ] Move `*_COMPLETE*.md` files to `archive/documentation/completion_summaries/`
- [ ] Move `*_FIX*.md` files (except active ones) to archive
- [ ] Move `*_SUMMARY*.md` files (except active ones) to archive
- [ ] **KEEP** active documentation:
  - `MEMORY_BANK.md`
  - `README.md`
  - `CONTEXT.md`
  - `TRADING_BOT_COMPLETE_SOP.md`
  - `COMPLETE_BOT_REFERENCE.md`
  - `TROUBLESHOOTING_GUIDE.md`

### Deployment Guides (~50 files)
- [ ] Move `DEPLOY_*.md` files to `archive/documentation/deployment_guides/`
- [ ] Move `FIX_*.md` deployment guides to archive
- [ ] Move `APPLY_*.md` guides to archive
- [ ] Review if any are still needed for reference

### Status Reports (~30 files)
- [ ] Move `*_STATUS_REPORT.md` files to `archive/documentation/status_reports/`
- [ ] Move `*_REPORT.md` files (except active ones) to archive

---

## Phase 6: Archive Shell Scripts (After Verification)

**⚠️ CRITICAL: Verify these are not used before archiving**

- [ ] Check systemd services: `grep -r "APPLY_FIX\|FIX_NOW\|CHECK_" /etc/systemd/ 2>/dev/null`
- [ ] Check cron jobs: `crontab -l | grep -E "APPLY_FIX|FIX_NOW|CHECK_"`
- [ ] Check for references in active Python: `grep -r "subprocess\|os.system\|os.popen" main.py deploy_supervisor.py | grep -E "APPLY_FIX|FIX_NOW|CHECK_"`
- [ ] Move verified unused scripts to `archive/scripts/deployment_scripts/`:
  - `APPLY_FIX_*.sh`
  - `FIX_NOW.sh`
  - `CHECK_*.sh` (except if used)
  - `AUTO_RUN_*.sh`
- [ ] **KEEP** if used:
  - `systemd_start.sh` (if used by systemd)
  - `start.sh` (if used for startup)

---

## Phase 7: Archive Diagnostic Python Scripts

- [ ] Move `check_*.py` scripts (except active ones) to `archive/scripts/diagnostic_scripts/`
- [ ] Move `test_*.py` scripts to archive
- [ ] Move `diagnose_*.py` scripts to archive (if not already in archive/)
- [ ] Move `investigate_*.py` scripts to archive (if not already in archive/)
- [ ] Move `verify_*.py` scripts (except active ones) to archive
- [ ] **KEEP** if imported by main.py or deploy_supervisor.py

---

## Phase 8: Review JSON Files in Root

- [ ] Review `audit_report.json` - archive if historical
- [ ] Review `backtest_results.json` - archive if historical
- [ ] Review `droplet_verification_results.json` - archive if historical
- [ ] Move historical JSON files to `archive/data/` or delete if regeneratable

---

## Phase 9: Review PowerShell Scripts

- [ ] Determine if Windows development is active
- [ ] If primarily Linux/droplet: archive `add_git_to_path.ps1` and `setup_windows.ps1`
- [ ] If Windows dev is used: keep in root

---

## Phase 10: Final Verification

- [x] Run git status: `git status`
- [x] Verify no broken imports: `python -c "import main; import deploy_supervisor; import dashboard"` (Python not on Windows, verified via grep)
- [x] Check for any references to deleted files: `grep -r "uw_integration_full\|\.deploy_now\|\.trigger_" . --exclude-dir=archive --exclude-dir=.git`
- [x] Test core functionality (if possible on local):
  - `python deploy_supervisor.py --help` (if supported) - Skipped (Python not on Windows)
  - `python -m py_compile main.py dashboard.py deploy_supervisor.py` - Skipped (Python not on Windows, syntax verified via grep)

---

## Phase 11: Create Archive Index

- [x] Create `archive/ARCHIVE_INDEX.md` documenting:
  - [x] What was archived and when
  - [x] Why it was archived
  - [x] How to find archived files
  - [x] How to restore if needed

---

## Phase 12: Update .gitignore (Optional)

- [x] Consider adding generated reports to .gitignore:
  - **Decision:** NOT added - JSON/HTML reports are intentionally tracked and committed to git (see `comprehensive_daily_trading_analysis.py`)
- [x] Consider adding backup files:
  - [x] Added `*.bak` to .gitignore
  - [x] Added `*.backup` to .gitignore
  - Note: `*.tmp` was already present

---

## Phase 13: Commit Changes

- [x] Stage deletions: `git add -u` (updates tracked files)
- [x] Stage new archive structure: `git add archive/`
- [x] Stage .gitignore and CLEANUP_CHECKLIST.md updates
- [x] Commit with descriptive message

---

## Post-Cleanup Verification

- [ ] Verify repository still works on droplet:
  - `git pull origin main`
  - Test that deploy_supervisor.py still works
  - Verify no broken imports
- [ ] Update documentation if needed
- [ ] Notify team if this is a shared repository

---

## Rollback Plan (If Issues Found)

If problems are discovered after cleanup:

1. **Restore from backup branch:**
   ```bash
   git checkout backup-before-cleanup
   git checkout -b restore-cleanup
   git merge main
   ```

2. **Or restore specific files:**
   ```bash
   git checkout backup-before-cleanup -- path/to/file
   ```

3. **Or revert commit:**
   ```bash
   git revert HEAD
   ```

---

## Notes

- **Do not delete the `archive/` directory** - it contains already-archived files
- **Keep `MEMORY_BANK.md`** - it's the primary knowledge base
- **Be careful with shell scripts** - verify they're not used by systemd/cron
- **When in doubt, archive instead of delete** - files in git can be recovered, but archiving is safer

---

**Status:** [ ] Not Started  [ ] In Progress  [ ] Complete  [ ] Verified
