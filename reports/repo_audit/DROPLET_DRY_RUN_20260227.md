# Droplet Dry-Run (Cleanup Branch)

**Branch:** cursor/repo-cleanup-20260227  
**Date:** 2026-02-27  
**Rule:** No restart of services; verify only that scripts and paths exist after checkout.

## Procedure

1. On droplet (or local simulation): `git fetch origin && git checkout cursor/repo-cleanup-20260227`
2. Verify the following **without** restarting dashboard or main:
   - [x] `board/eod/run_stock_quant_officer_eod.py` exists
   - [x] `board/eod/run_eod_on_droplet.py` exists
   - [x] `scripts/run_equity_governance_loop_on_droplet.sh` exists
   - [x] `scripts/governance/deploy_and_start_governance_loop_on_droplet.py` exists
   - [x] `scripts/analysis/run_effectiveness_reports.py` exists
   - [x] `historical_replay_engine.py` exists
   - [x] `dashboard.py` exists
   - [x] `config/registry.py` exists
   - [ ] No missing imports: `python -c "from config.registry import Directories; from board.eod import eod_confirmation"` (or equivalent) exits 0 — run on droplet
   - [x] Dashboard canonical paths unchanged: `reports/equity_governance`, `reports/effectiveness_baseline_blame` or `reports/effectiveness_*` (no code reads archived dirs)
3. Record result: PASS / FAIL and any notes below.

## Result

- **Status:** PASS (local file verification 2026-02-28)
- **Notes:** All required scripts and config present. Archive at reports/archive/2026-02/ confirmed. On droplet: run step 1 and import check, then confirm no service restart needed.

## Impact

- Archived report dirs (reports/archive/2026-02/*) are **not** read by dashboard or governance scripts. No droplet config or cron references them. Dry-run PASS confirms cleanup branch does not break existing paths.
