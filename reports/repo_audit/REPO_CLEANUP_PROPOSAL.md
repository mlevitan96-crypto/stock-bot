# Repo Cleanup Proposal

**Generated:** 2026-02-27 | **Branch:** cursor/repo-cleanup-* (to create)  
**Rule:** No modifications on main. All changes via cleanup branch and SAFE_TO_APPLY PR.

---

## 1. Objectives

- Remove or archive stale, unused, legacy, or misleading files.
- Canonicalize repo so governance, replay, dashboards, and attribution use only documented paths.
- Update Memory Bank to reflect cleaned repo.
- Ensure no cleanup breaks droplet, governance loop, or replay engine.

---

## 2. Files / Directories to DELETE (high confidence, no code references)

| Target | Rationale | Risk |
|--------|-----------|------|
| *(None in first pass)* | Prefer archive over delete. Deletions only after adversarial review and PR. | — |

**Adversarial note:** Do not delete any file in Phase 4 until a second reviewer confirms. If in doubt, move to `archive/` or `reports/archive/` instead.

---

## 3. Directories to ARCHIVE (move, not delete)

| Source | Destination | Rationale |
|--------|-------------|-----------|
| `archive/` | *(keep in place)* | Already isolated; no production imports. Optional: rename to `archive_legacy/` for clarity. |
| `reports/effectiveness_example` | `reports/archive/effectiveness_example` | Example run; not read by dashboard or governance. |
| `reports/effectiveness_test_run` | `reports/archive/effectiveness_test_run` | Test run artifact. |
| `reports/effectiveness_paper_score028_current` | `reports/archive/effectiveness_paper_score028_current` | Superseded by effectiveness_baseline_blame. |

**Impact:** No code path references these by name (dashboard uses `effectiveness_*` glob and effectiveness_baseline_blame). Moving them avoids clutter; scripts do not hardcode these dirs.

---

## 4. Files to MOVE (canonicalize locations)

| Source | Destination | Rationale |
|--------|-------------|-----------|
| *(None required for Phase 4)* | — | Canonical paths already defined in config.registry and dashboard. No file moves needed for correctness. |

---

## 5. Files to RENAME

| Current | Proposed | Rationale |
|---------|----------|-----------|
| *(None)* | — | Renames add churn; skip unless necessary. |

---

## 6. Reports to ARCHIVE (batch)

Move the following under `reports/archive/2026-02/` (or similar) so that `reports/` root and key subdirs stay canonical:

- `reports/blocked_expectancy/` → `reports/archive/2026-02/blocked_expectancy/`
- `reports/blocked_signal_expectancy/` → `reports/archive/2026-02/blocked_signal_expectancy/`
- `reports/cursor_final_remediation/` → `reports/archive/2026-02/cursor_final_remediation/`
- `reports/followup_diag_artifacts/` → `reports/archive/2026-02/followup_diag_artifacts/`
- `reports/nuclear_audit/` → `reports/archive/2026-02/nuclear_audit/`
- `reports/truth_audit/` → `reports/archive/2026-02/truth_audit/`
- `reports/truth_audit_fix/` → `reports/archive/2026-02/truth_audit_fix/`

**Impact:** No dashboard or governance script references these paths. Safe to move.

---

## 7. Scripts to DEPRECATE (do not remove; add comment or README)

- Root-level one-off scripts: `RUN_DROPLET_VERIFICATION_NOW.py`, `EXECUTE_DROPLET_DEPLOYMENT_NOW.py`, `FIX_*.py`, `COMPLETE_*.py`, etc.  
  **Action:** Add a single `README_DEPRECATED_SCRIPTS.md` in root listing them and stating: "Legacy one-off scripts. Prefer scripts/governance and board/eod for production."
- **Do not delete** — may still be run manually for diagnostics.

---

## 8. Dashboard endpoints to UPDATE

- **None.** Dashboard already uses canonical paths from config.registry and reports/equity_governance, reports/effectiveness_*.  
- After archiving report dirs above, confirm no endpoint points to moved paths (it does not; they are unreferenced).

---

## 9. Memory Bank docs to UPDATE

- **MEMORY_BANK.md:** Add a short "Canonical paths and cleanup" note:  
  - "Repo canonical layout and report paths: see reports/repo_audit/CANONICAL_REPO_STRUCTURE.md and reports/repo_audit/CANONICAL_PATHS.json. Dashboard endpoint map: reports/DASHBOARD_ENDPOINT_MAP.md."
- **reports/DASHBOARD_ENDPOINT_MAP.md:** No change; already canonical.
- Optionally reference `reports/repo_audit/` in MEMORY_BANK as the audit truth root.

---

## 10. Deploy scripts

- **No change** to deploy_supervisor.py, droplet_client.py, or board/eod/deploy_on_droplet.sh.  
- Governance deploy script (deploy_and_start_governance_loop_on_droplet.py) already uses canonical paths; no update needed.

---

## 11. Risk assessment

| Risk | Mitigation |
|------|------------|
| Dashboard breaks | No endpoint reads archived report dirs; only equity_governance, effectiveness_*, strategy comparison, wheel. |
| Governance loop breaks | Scripts use reports/equity_governance, reports/effectiveness_baseline_blame, state/equity_governance_loop_state.json — unchanged. |
| Replay breaks | historical_replay_engine.py and scripts/replay/* unchanged; no moved paths used as input. |
| Droplet cron fails | EOD and cron scripts (board/eod/*, scripts/run_equity_governance_loop_on_droplet.sh) unchanged. |
| Import errors | No production code imports from archive/ or from archived report dirs. |

---

## 12. Multi-model adversarial review notes

- **Conservative stance:** No file deletions in this proposal; only archive moves and deprecation doc.
- **Second reviewer:** Confirm that `reports/effectiveness_*` glob in dashboard does not break when we move effectiveness_example, effectiveness_test_run, effectiveness_paper_score028_current into reports/archive/ (dashboard prefers effectiveness_baseline_blame when present; glob still finds any remaining effectiveness_*).
- **Rollback:** Revert branch; move dirs back from reports/archive/ if ever needed.

---

## 13. Summary of Phase 4 actions (on cleanup branch)

1. Create `reports/archive/2026-02/` if not present.
2. Move listed report dirs (blocked_expectancy, blocked_signal_expectancy, cursor_final_remediation, followup_diag_artifacts, nuclear_audit, truth_audit, truth_audit_fix) into `reports/archive/2026-02/`.
3. Move effectiveness_example, effectiveness_test_run, effectiveness_paper_score028_current into `reports/archive/` (or `reports/archive/2026-02/`).
4. Add `README_DEPRECATED_SCRIPTS.md` at root (deprecation notice for one-off scripts).
5. Update MEMORY_BANK.md with one short paragraph pointing to reports/repo_audit canonical docs and DASHBOARD_ENDPOINT_MAP.
6. Run validation tests (Phase 5) and droplet dry-run; record results.
7. Open PR with SAFE_TO_APPLY checklist and links to all audit artifacts.
