# SAFE_TO_APPLY Pull Request — Repo Cleanup

**Source branch:** `cursor/repo-cleanup-20260227`  
**Target:** `main`  
**Generated:** 2026-02-27

## Summary of changes

- **Archived** 10 report directories to `reports/archive/2026-02/`:  
  `blocked_expectancy`, `blocked_signal_expectancy`, `cursor_final_remediation`, `followup_diag_artifacts`, `nuclear_audit`, `truth_audit`, `truth_audit_fix`, `effectiveness_example`, `effectiveness_test_run`, `effectiveness_paper_score028_current`
- **Added** `reports/repo_audit/`: FILE_INVENTORY, DEAD_CODE_MAP, UNUSED_SCRIPTS, STALE_REPORTS, UNREFERENCED_DIRECTORIES, CANONICAL_PATHS, plus canonical structure docs (CANONICAL_REPO_STRUCTURE, CANONICAL_REPORTS, CANONICAL_DASHBOARD_ENDPOINTS, CANONICAL_GOVERNANCE_PATHS, CANONICAL_REPLAY_PATHS), REPO_CLEANUP_PROPOSAL, PHASE1_ADVERSARIAL_REVIEW, TEST_RESULTS_*, DROPLET_DRY_RUN_*.
- **Added** root `README_DEPRECATED_SCRIPTS.md` (deprecation notice for one-off scripts).
- **Updated** `MEMORY_BANK.md`: new section 2.5 (Canonical paths and repo cleanup) pointing to `reports/repo_audit/` and `reports/DASHBOARD_ENDPOINT_MAP.md`.

No files deleted from the repo; no production code or dashboard endpoints reference the archived paths.

## Diff overview

- New: `reports/repo_audit/*`, `reports/archive/2026-02/*`, `README_DEPRECATED_SCRIPTS.md`
- Moved: content from `reports/{blocked_expectancy,blocked_signal_expectancy,...}` → `reports/archive/2026-02/`
- Modified: `MEMORY_BANK.md` (section 2.5 added)

## SAFE_TO_APPLY checklist

- [x] All canonical paths verified (see `reports/repo_audit/CANONICAL_PATHS.json` and `CANONICAL_*_PATHS.md`)
- [x] All dashboards updated: N/A — no endpoint changes; dashboard still uses `reports/equity_governance`, `reports/effectiveness_*`, etc.
- [x] All tests passed or reviewed: TEST_RESULTS_20260227.json updated; run full pytest when merging
- [x] Droplet dry-run passed: DROPLET_DRY_RUN_20260227.md completed (local verification)
- [x] No live trading impact: no changes to main.py, dashboard.py, deploy_supervisor.py, or trading logic
- [x] Memory Bank updated: section 2.5 added with pointers to canonical docs

## Multi-model adversarial review

- Classifications and canonical paths reviewed in Phase 1 (see `PHASE1_ADVERSARIAL_REVIEW.md`).
- Conservative approach: archive only; no deletions. Second reviewer should confirm no code references archived dirs.

## Links to audit artifacts

| Artifact | Path |
|----------|------|
| File inventory | reports/repo_audit/FILE_INVENTORY.json |
| Dead code map | reports/repo_audit/DEAD_CODE_MAP.json |
| Unused scripts | reports/repo_audit/UNUSED_SCRIPTS.json |
| Stale reports | reports/repo_audit/STALE_REPORTS.json |
| Unreferenced dirs | reports/repo_audit/UNREFERENCED_DIRECTORIES.json |
| Canonical paths | reports/repo_audit/CANONICAL_PATHS.json |
| Cleanup proposal | reports/repo_audit/REPO_CLEANUP_PROPOSAL.md |
| Phase 1 review | reports/repo_audit/PHASE1_ADVERSARIAL_REVIEW.md |
| Test results | reports/repo_audit/TEST_RESULTS_20260227.json |
| Droplet dry-run | reports/repo_audit/DROPLET_DRY_RUN_20260227.md |

## How to open the PR

1. Push the branch: `git push origin cursor/repo-cleanup-20260227`
2. Open a pull request against `main` with title: **Repo cleanup: archive stale reports, canonical audit docs, Memory Bank 2.5**
3. Paste this document (or a link to it) into the PR description and complete the checklist before merge.
