# Alpaca Daily Run Integrity Contract

**Authority:** `docs/ALPACA_GOVERNANCE_CONTEXT.md` (governance rules; execution integrity).  
**Scope:** Execution integrity and daily board resiliency only. No strategy or analytical contract changes.

This contract defines **required phases**, **required artifacts**, **expected locations**, and **FAIL conditions** for a valid daily governance run. Failures are explicit and fail-closed; analytical issues remain WARN-only.

---

## 1. Required phases (in order)

| Phase | Description | Validator check |
|-------|-------------|-----------------|
| Molt orchestration executed | `run_learning_orchestrator` ran and produced learning status | `reports/LEARNING_STATUS_<DATE>.md` exists, non-empty, timestamp in window |
| Engineering sentinel executed | `run_engineering_sentinel` ran | `reports/ENGINEERING_HEALTH_<DATE>.md` exists, non-empty, timestamp in window |
| Governance chair executed | `run_learning_board` ran (signal_advocate, risk_auditor, counterfactual_analyst, governance_chair) | One of `reports/PROMOTION_PROPOSAL_<DATE>.md` or `reports/REJECTION_WITH_REASON_<DATE>.md` exists, non-empty, timestamp in window |
| Promotion discipline executed | `run_promotion_discipline` ran | `reports/PROMOTION_DISCIPLINE_<DATE>.md` exists, non-empty, timestamp in window |
| Memory evolution executed | `run_memory_evolution_proposal` ran | `reports/MEMORY_BANK_CHANGE_PROPOSAL_<DATE>.md` exists, non-empty, timestamp in window |
| Discovery index present | Governance discovery index available for audits | `reports/GOVERNANCE_DISCOVERY_INDEX.md` exists, non-empty |
| Daily board output produced | Same as governance chair; one of PROPOSE/REJECT artifact | See governance chair row |
| Attribution summary present | Learning status summarizes attribution inputs | `reports/LEARNING_STATUS_<DATE>.md` (orchestrator output) satisfies this |
| Diagnostics summaries present | At least one exit-join or blocked-trade diagnostic for the date | At least one of `reports/EXIT_JOIN_HEALTH_<DATE>.md`, `reports/BLOCKED_TRADE_INTEL_<DATE>.md` exists, non-empty |

---

## 2. Required artifacts and locations

All paths relative to repo root (or `REPO_DIR` on droplet).

| Artifact | Location | Required |
|----------|----------|----------|
| Molt last run state | `state/molt_last_run.json` | Yes (proves Molt script ran; must contain `date`, `exit_code`, `timestamp_utc`) |
| Learning status | `reports/LEARNING_STATUS_<DATE>.md` | Yes |
| Engineering health | `reports/ENGINEERING_HEALTH_<DATE>.md` | Yes |
| Board output (proposal or rejection) | `reports/PROMOTION_PROPOSAL_<DATE>.md` or `reports/REJECTION_WITH_REASON_<DATE>.md` | Yes (exactly one) |
| Promotion discipline | `reports/PROMOTION_DISCIPLINE_<DATE>.md` | Yes |
| Memory bank change proposal | `reports/MEMORY_BANK_CHANGE_PROPOSAL_<DATE>.md` | Yes |
| Discovery index | `reports/GOVERNANCE_DISCOVERY_INDEX.md` | Yes |
| Attribution/diagnostics (at least one) | `reports/EXIT_JOIN_HEALTH_<DATE>.md` or `reports/BLOCKED_TRADE_INTEL_<DATE>.md` | Yes |

---

## 3. Run window (timestamp alignment)

- **Run window start:** 00:00:00 UTC on the run date (`DATE`).
- **Run window end:** 23:59:59 UTC on the run date plus 12 hours (to allow post-market run at 21:35 UTC and same-day validation).

A required artifact **fails** timestamp alignment if:
- Its last modification time (mtime) is **before** run window start, or
- Its last modification time is **after** run window end (optional strict check; can be relaxed to "mtime within last 36h" for simplicity).

Validator implementation: **mtime >= run_window_start** and **mtime <= run_window_end**. Use run_window_end = run date 23:59:59 UTC + 12 hours.

---

## 4. FAIL conditions (daily run INVALID)

The daily run is **INVALID** (fail-closed) when **any** of the following is true:

1. **Molt exited early:** `state/molt_last_run.json` has `exit_code` != 0 or is missing.
2. **Governance chair did not emit output:** Neither `reports/PROMOTION_PROPOSAL_<DATE>.md` nor `reports/REJECTION_WITH_REASON_<DATE>.md` exists, or both exist but are empty.
3. **Any required artifact is missing:** A file from §2 is absent.
4. **Any required artifact is empty:** A required file has size 0.
5. **Timestamp misalignment:** A required artifact's mtime is outside the run window (see §3).
6. **Discovery index missing or empty:** `reports/GOVERNANCE_DISCOVERY_INDEX.md` missing or zero-length.
7. **No diagnostics summary:** Neither `reports/EXIT_JOIN_HEALTH_<DATE>.md` nor `reports/BLOCKED_TRADE_INTEL_<DATE>.md` exists or both are empty.

Analytical issues (e.g. learning verdict FAILED, promotion rejected) remain **WARN-only** and do not by themselves make the run INVALID; execution integrity (all phases ran and emitted artifacts) is what triggers FAIL.

---

## 5. Canonical daily entry point

- **Script:** `scripts/run_daily_governance.sh` (or equivalent). Single command that:
  1. Runs Molt workflow (`scripts/run_molt_on_droplet.sh` or `scripts/run_molt_workflow.py` with --date and --base-dir).
  2. Ensures discovery index exists (no-op if already present; optional refresh if a refresh script exists).
  3. Runs artifact completeness validator (`scripts/validate_daily_governance_artifacts.py`).
  4. Emits a single **PASS** or **FAIL** verdict; exit 0 only on PASS.

- **Validator:** `scripts/validate_daily_governance_artifacts.py` — verifies required files exist, non-empty, timestamps in run window; exit non-zero on any FAIL; produces concise PASS/FAIL summary.

---

## 6. Failure modes now prevented

| Failure mode | Detection | Result |
|--------------|-----------|--------|
| Molt exits early (exception, crash) | `state/molt_last_run.json` missing or `exit_code` != 0 | FAIL; run INVALID |
| Governance chair does not emit output | Neither PROMOTION_PROPOSAL nor REJECTION_WITH_REASON present/non-empty | FAIL; run INVALID |
| Discovery index missing or empty | `reports/GOVERNANCE_DISCOVERY_INDEX.md` missing or zero-length | FAIL; run INVALID |
| Any required Molt artifact missing | Validator checks each path | FAIL; run INVALID |
| Any required artifact empty | Validator checks st_size > 0 | FAIL; run INVALID |
| Stale or misaligned artifacts | mtime outside run window (optional; use `--skip-timestamps` to relax) | FAIL when not skipped |
| No diagnostics (exit join / blocked intel) | Neither EXIT_JOIN_HEALTH nor BLOCKED_TRADE_INTEL present/non-empty | FAIL; run INVALID |
| Silent board breakage | Explicit validator output and non-zero exit from canonical entry point | No silent pass when artifacts missing |

Analytical outcomes (e.g. LEARNING_FAILED, REJECT) do **not** by themselves cause FAIL; only execution integrity does.

---

## 7. References

- Molt workflow: `scripts/run_molt_workflow.py`, `scripts/run_molt_on_droplet.sh`
- Board (governance chair): `moltbot/board.py`, `moltbot/agents/governance_chair.py`
- Discovery index: `reports/GOVERNANCE_DISCOVERY_INDEX.md`
- Governance context: `docs/ALPACA_GOVERNANCE_CONTEXT.md`
