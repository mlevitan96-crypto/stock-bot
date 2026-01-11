# Archive Directory

This directory contains archived files that are no longer actively used but are kept for historical reference.

## Directory Structure

```
archive/
├── documentation/
│   ├── completion_summaries/    # Completed work summaries (*_COMPLETE*.md, *_FIX*.md)
│   ├── deployment_guides/        # One-time deployment guides (DEPLOY_*.md, FIX_*.md)
│   └── status_reports/           # Historical status reports (*_STATUS_REPORT.md)
├── scripts/
│   ├── deployment_scripts/       # One-time deployment shell scripts
│   └── diagnostic_scripts/       # Diagnostic and test Python scripts
└── investigation_scripts/        # Investigation and debugging scripts (pre-existing)
```

## Purpose

Files are archived here when they:
- Are no longer actively used in the codebase
- Document completed work or resolved issues
- Are one-time deployment or diagnostic scripts
- Have historical value but aren't needed for daily operations

## Active Files

The following files are **NOT archived** and remain in the root directory:
- Core system files: `main.py`, `dashboard.py`, `deploy_supervisor.py`, `uw_flow_daemon.py`
- Active documentation: `MEMORY_BANK.md`, `README.md`, `CONTEXT.md`, `TRADING_BOT_COMPLETE_SOP.md`
- Active scripts: `systemd_start.sh`, `start.sh` (if used)

## Archive Date

Archive structure created: 2026-01-09

## Notes

- Files in this directory are not actively maintained
- If you need to find a specific archived file, check the subdirectories
- Archived files can be restored if needed (they're still in git history)
- See `REPOSITORY_AUDIT_REPORT.md` for details on what was archived and why
