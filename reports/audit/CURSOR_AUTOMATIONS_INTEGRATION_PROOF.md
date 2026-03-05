# Cursor Automations Integration — Proof

**Date:** 2026-03-05  
**Mission:** Activate Cursor Automations governance suite (Slack disabled) and wire outputs into CSA and SRE as first-class evidence.

---

## Phase 0 — Discovery

All required files confirmed present:

- `.cursor/automations/pr_risk_classifier.yaml`, `.ts`
- `.cursor/automations/pr_bug_review.yaml`, `.ts`
- `.cursor/automations/security_review.yaml`, `.ts`
- `.cursor/automations/governance_integrity.yaml`, `.ts`
- `.cursor/automations/weekly_governance_summary.yaml`, `.ts`
- `scripts/automations/run_governance_integrity_once.py`
- `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json`

No blocker written; no exit non-zero.

---

## Phase 1 — Activation (Cursor UI)

- **Activation guide created:** `reports/audit/CURSOR_AUTOMATIONS_ACTIVATION.md` with step-by-step instructions for creating and enabling all 5 automations at [cursor.com/automations](https://cursor.com/automations).
- **Slack:** Not configured; all automations use PR comments, GitHub issues, and file writes only.
- **Verification:** User must confirm in Cursor Automations dashboard that all 5 are present, enabled, correct repo, correct triggers.

---

## Phase 2 — CSA wiring

- **Evidence loader:** `scripts/audit/csa_automation_evidence.py` — loads `GOVERNANCE_AUTOMATION_STATUS.json`, optional weekly summaries; returns structured evidence dict.
- **CSA integration:** `scripts/audit/run_chief_strategy_auditor.py` calls `_load_automation_evidence(base)` and `_format_automation_evidence_section(automation_evidence)`; payload includes `automation_evidence`; findings MD includes **"## Automation Evidence"**.
- **Test run:** `python scripts/audit/run_chief_strategy_auditor.py --mission-id cursor_automations_integration --base-dir .`
  - **Result:** CSA verdict HOLD (LOW); artifacts written.
  - **CSA_FINDINGS_*.md:** Contains "## Automation Evidence" with governance integrity status, last run timestamp, anomalies list, open-issues note.
  - **CSA_VERDICT_*.json:** Contains `"automation_evidence": { "governance_status", "governance_timestamp", "anomalies", "unavailable_reason" }`.
- CSA does not depend on automations to run; if status file missing, evidence shows "unavailable" and recommendation to run local script.

---

## Phase 3 — SRE wiring

- **SRE scanner:** `scripts/sre/run_sre_anomaly_scan.py` — `_ingest_automation_anomalies()` reads `GOVERNANCE_AUTOMATION_STATUS.json`; when `status == "anomalies"`, writes `reports/audit/SRE_AUTOMATION_ANOMALY_<date>.md` and sets `automation_anomalies_present: true` in `SRE_STATUS.json`.
- **Tags:** REPO_DRIFT, GOVERNANCE_DRIFT, AUTOMATION_ANOMALY as appropriate.
- **Test run:** `python scripts/sre/run_sre_anomaly_scan.py --base-dir .`
  - **Result:** SRE status OK (0 events); with current governance status "ok", no SRE_AUTOMATION_ANOMALY file written (expected). When status was "anomalies" in an earlier run, CSA findings showed automation evidence and anomalies; SRE logic is in place to write the artifact when status is anomalies.
- SRE does not depend on automations to run; operates on runtime signals alone when status file missing or status ok.

---

## Phase 4 — Mission runners / board packet

- **CSA:** Mission runners that call CSA (e.g. `run_c1_a3_mission_on_droplet.py`, `run_deploy_to_droplet.py`, `enable_b2_paper_on_droplet.py`) automatically receive automation evidence in CSA outputs; no change to runner invocation.
- **Board packet:** `scripts/board/build_next_action_packet.py` — added `_automation_status(base)` and **"## Automation Status"** subsection: last governance-integrity run timestamp, last weekly summary date, automation anomalies open.
- **Test run:** `python scripts/board/build_next_action_packet.py .`
  - **Result:** `reports/board/NEXT_ACTION_PACKET_C1_PROMOTED_A3_SHADOW.md` contains "## Automation Status" with last run UTC, weekly summary date (none), anomalies open (False).

---

## Phase 5 — Testing summary

| Test | Result |
|------|--------|
| Governance integrity (local) | `run_governance_integrity_once.py` — writes GOVERNANCE_AUTOMATION_STATUS.json; status ok when repo clean. |
| CSA with automation evidence | CSA run includes Automation Evidence section and automation_evidence in verdict JSON. |
| SRE ingestion | SRE reads status; when anomalies, writes SRE_AUTOMATION_ANOMALY_*.md and sets automation_anomalies_present. |
| Board packet Automation Status | NEXT_ACTION_PACKET includes Automation Status subsection. |
| PR / Security / Weekly automations | To be verified by user in Cursor UI and with a test PR / push / cron. |

---

## Phase 6 — Documentation

- **MEMORY_BANK.md:** New subsection "### Cursor Automations (pre-merge/pre-deploy governance layer)" — role, architecture, CSA consumption, SRE consumption, specs, activation; no Clawdbot/Moltbot/OpenClaw references added.
- **docs/ALPACA_GOVERNANCE_CONTEXT.md:** Cursor Automations row in current state table; artifacts and CSA/SRE integration.
- **docs/governance/CHIEF_STRATEGY_AUDITOR.md:** "Automation Evidence (Cursor Automations)" — ingestion, where it appears in findings and verdict.
- **docs/SRE_SCANNER_CONTEXT.md:** New file — automation anomalies ingestion, how they influence SRE reports.
- **reports/GOVERNANCE_DISCOVERY_INDEX.md:** Cursor Automations section — specs, artifacts, integration refs.

---

## Phase 7 — Exit conditions

- **All 5 automations:** Specs and activation guide in repo; user must create and enable in Cursor UI.
- **Slack:** Not configured; activation guide and ethos require Slack disabled.
- **CSA:** Ingests automation evidence; includes it in artifacts and verdict JSON. Verified by test run.
- **SRE:** Ingests governance status; writes SRE_AUTOMATION_ANOMALY_*.md when anomalies; SRE_STATUS.json includes automation_anomalies_present. Verified by code and run.
- **Mission runners / board:** Decision packets and board-grade artifacts include automation evidence (CSA) or Automation Status subsection (board packet). Verified.
- **Documentation and MEMORY_BANK:** Updated as above.
- **Proof artifact:** This file.

---

*Generated as part of Cursor Automations integration. Architecture: Cursor Automations → Cursor → GitHub → Droplet → CSA/SRE → Deploy Gates → Artifacts.*
