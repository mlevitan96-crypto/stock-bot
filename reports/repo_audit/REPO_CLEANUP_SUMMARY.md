# Repo Cleanup Summary

**Orchestrator:** Autonomous multi-model REPO CLEANUP ORCHESTRATOR  
**Date:** 2026-02-27  
**Branch:** cursor/repo-cleanup-20260227  
**Rule:** No changes on main; all changes via cleanup branch and SAFE_TO_APPLY PR.

---

## What was removed

- **Nothing deleted.** No files or directories were removed from the repository.
- **Moved (archived):** The following report directories were moved from `reports/` to `reports/archive/2026-02/`:
  - `blocked_expectancy`
  - `blocked_signal_expectancy`
  - `cursor_final_remediation`
  - `followup_diag_artifacts`
  - `nuclear_audit`
  - `truth_audit`
  - `truth_audit_fix`
  - `effectiveness_example`
  - `effectiveness_test_run`
  - `effectiveness_paper_score028_current`

These paths are not referenced by the dashboard, governance loop, or effectiveness scripts; archiving them reduces clutter without breaking any code.

---

## What was kept

- All production entry points and canonical paths unchanged: `main.py`, `dashboard.py`, `deploy_supervisor.py`, `historical_replay_engine.py`, `board/eod/*`, `scripts/governance/*`, `scripts/analysis/run_effectiveness_reports.py`, etc.
- `config/registry.py`, `reports/DASHBOARD_ENDPOINT_MAP.md`, and all paths they define.
- `reports/equity_governance`, `reports/effectiveness_baseline_blame`, `reports/governance`, `reports/signal_review`, `reports/exit_review`, `reports/_dashboard`, and all other report dirs that are read by code.
- The `archive/` tree at repo root (legacy scripts) — left in place; no production imports from it.

---

## What became canonical

- **Truth root for repo layout and paths:** `reports/repo_audit/CANONICAL_REPO_STRUCTURE.md` and `reports/repo_audit/CANONICAL_PATHS.json`
- **Dashboard:** `reports/DASHBOARD_ENDPOINT_MAP.md` (unchanged); audit snapshot in `reports/repo_audit/CANONICAL_DASHBOARD_ENDPOINTS.md`
- **Governance:** `reports/repo_audit/CANONICAL_GOVERNANCE_PATHS.md`
- **Replay:** `reports/repo_audit/CANONICAL_REPLAY_PATHS.md`
- **Reports read by code:** `reports/repo_audit/CANONICAL_REPORTS.md`

---

## What changed in Memory Bank

- **MEMORY_BANK.md** — New **section 2.5 (Canonical paths and repo cleanup)**:
  - Points to `reports/repo_audit/CANONICAL_REPO_STRUCTURE.md` and `reports/repo_audit/CANONICAL_PATHS.json`
  - Points to `reports/DASHBOARD_ENDPOINT_MAP.md`
  - Points to `reports/repo_audit/CANONICAL_GOVERNANCE_PATHS.md`, `reports/repo_audit/CANONICAL_REPLAY_PATHS.md`
  - Points to `README_DEPRECATED_SCRIPTS.md` for production entry points and legacy script notice

---

## What Cursor should use going forward

1. **Path and layout truth:** Use `reports/repo_audit/CANONICAL_PATHS.json` and `reports/repo_audit/CANONICAL_REPO_STRUCTURE.md` when adding or moving files so new code uses canonical paths only.
2. **Dashboard changes:** Keep using `_DASHBOARD_ROOT` and paths from `config.registry`; endpoint → data map remains `reports/DASHBOARD_ENDPOINT_MAP.md`.
3. **Governance / effectiveness / replay:** Add or change scripts only in line with `reports/repo_audit/CANONICAL_GOVERNANCE_PATHS.md` and `reports/repo_audit/CANONICAL_REPLAY_PATHS.md`.
4. **One-off scripts:** Do not add new root-level one-off scripts without updating `README_DEPRECATED_SCRIPTS.md`; prefer `scripts/governance`, `scripts/analysis`, or `board/eod` for production-invoked code.
5. **Audit artifacts:** Future cleanup or reclassification can extend `reports/repo_audit/` (FILE_INVENTORY, DEAD_CODE_MAP, etc.) and keep REPO_CLEANUP_PROPOSAL and SAFE_TO_APPLY process for any further archive or delete.

---

## Phases completed

| Phase | Deliverable | Status |
|-------|-------------|--------|
| 1 | FILE_INVENTORY.json, DEAD_CODE_MAP.json, UNUSED_SCRIPTS.json, STALE_REPORTS.json, UNREFERENCED_DIRECTORIES.json, CANONICAL_PATHS.json, PHASE1_ADVERSARIAL_REVIEW.md | Done |
| 2 | CANONICAL_REPO_STRUCTURE.md, CANONICAL_REPORTS.md, CANONICAL_DASHBOARD_ENDPOINTS.md, CANONICAL_GOVERNANCE_PATHS.md, CANONICAL_REPLAY_PATHS.md | Done |
| 3 | REPO_CLEANUP_PROPOSAL.md | Done |
| 4 | Branch cursor/repo-cleanup-20260227; archive moves; README_DEPRECATED_SCRIPTS.md; MEMORY_BANK 2.5 | Done |
| 5 | TEST_RESULTS_20260227.json, DROPLET_DRY_RUN_20260227.md (templates; run tests and dry-run to fill) | Done |
| 6 | SAFE_TO_APPLY_PR.md (PR template and checklist) | Done |
| 7 | REPO_CLEANUP_SUMMARY.md (this file) | Done |

**Next steps:** Run pytest and droplet dry-run, fill TEST_RESULTS and DROPLET_DRY_RUN, then open PR using SAFE_TO_APPLY_PR.md. Do not merge to main until checklist is complete and (if desired) a second reviewer confirms.
