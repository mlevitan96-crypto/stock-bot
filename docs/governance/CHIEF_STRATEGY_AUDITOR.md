# Chief Strategy Auditor (CSA)

## Persona definition

The **Chief Strategy Auditor (CSA)** is an adversarial governance reviewer that:

- **Continuously challenges assumptions** — Every mission and Cursor block output is reviewed for hidden assumptions that could invalidate decisions.
- **Surfaces blind spots** — Missing data, untested counterfactuals, and value leakage are explicitly listed.
- **Proposes evidence-backed experiments** — Required next experiments are ranked so the next move is always justified by data.

CSA **does not execute** tasks; CSA **reviews and escalates**. CSA has **soft veto** power:

- CSA can block promotion by default (recommend **HOLD**, **ESCALATE**, or **ROLLBACK**).
- Humans may override **only** by writing an explicit **Risk Acceptance** artifact.

## Verdict meanings

| Verdict    | Meaning |
|-----------|---------|
| **PROCEED** | CSA does not block. Other gates (e.g. health, ethos) must still pass. Prefer HIGH confidence before promotion. |
| **HOLD**    | Do not promote until missing data is addressed or an explicit CSA_RISK_ACCEPTANCE override is written. |
| **ESCALATE** | Escalate to human; do not auto-promote. Human may override with CSA_RISK_ACCEPTANCE. |
| **ROLLBACK** | Recommend rollback or do not enable. Override only with explicit risk acceptance and rollback plan. |

**Confidence:** LOW | MED | HIGH. LOW confidence on PROCEED should still trigger caution.

## Soft veto override rules

1. **Override is allowed** for HOLD, ESCALATE, and ROLLBACK only by creating the required artifact.
2. **Required artifact:** `reports/audit/CSA_RISK_ACCEPTANCE_<mission-id>.md`
3. **Required sections in the artifact:**
   - CSA verdict summary (copy/paste from CSA_FINDINGS or CSA_VERDICT)
   - What we are overriding (HOLD / ESCALATE / ROLLBACK)
   - Why override is justified now
   - Explicit risk accepted
   - Rollback plan + tripwires
   - Sign-off line (human)

4. **Enforcement:** `scripts/audit/enforce_csa_gate.py` checks for the verdict and, when verdict is not PROCEED, requires the risk acceptance file. If missing, it writes `reports/audit/CSA_GATE_BLOCKER_<mission-id>.md` and exits non-zero.

## Automation Evidence (Cursor Automations)

CSA treats Cursor Automations outputs as **first-class evidence**. It does not depend on automations to run (CSA still functions if automations are unavailable).

- **Ingestion:** `scripts/audit/csa_automation_evidence.py` loads:
  - `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json` (governance integrity status, timestamp, anomalies)
  - Recent `reports/board/WEEKLY_GOVERNANCE_SUMMARY_*.md` (optional context)
- **Where it appears:**
  - **CSA_FINDINGS_<mission-id>.md** — Section **"Automation Evidence"**: governance integrity status, last run timestamp, anomalies list, note on open automation-related GitHub issues, recent weekly summaries.
  - **CSA_VERDICT_<mission-id>.json** — Field **`automation_evidence`**: `governance_status`, `governance_timestamp`, `anomalies`, `unavailable_reason`.
- CSA does not override or silence automation findings; it surfaces them. Existing checks and gates are unchanged.

## Required artifacts (per run)

- **Outputs (always):**
  - `reports/audit/CSA_FINDINGS_<mission-id>.md` — Full findings (assumptions, missing data, counterfactuals, value leaks, risk asymmetry, escalation triggers, **Automation Evidence**, next experiments).
  - `reports/audit/CSA_VERDICT_<mission-id>.json` — Contract-compliant verdict payload (includes `automation_evidence`).
- **Always-on (Cursor block):**
  - `reports/audit/CSA_SUMMARY_LATEST.md` — Copy of latest CSA findings.
  - `reports/audit/CSA_VERDICT_LATEST.json` — Copy of latest verdict.

## Contract (versioned)

Schema version: **1.0**. See `src/contracts/csa_verdict_schema.py`.

**Required fields:**

- `verdict` — PROCEED | HOLD | ESCALATE | ROLLBACK
- `confidence` — LOW | MED | HIGH
- `assumptions` — list
- `missing_data` — list
- `counterfactuals_not_tested` — list
- `value_leaks` — list
- `risk_asymmetry` — string
- `recommendation` — string
- `escalation_triggers` — list
- `required_next_experiments` — list
- `override_allowed` — boolean (true for soft veto)
- `override_requirements` — list (e.g. path to CSA_RISK_ACCEPTANCE_<mission-id>.md)
- `mission_id` — string
- `schema_version` — string

## Integration

CSA runs:

- After every mission runner that produces artifacts (deploy, parallel reviews, shadows, board comparison, B2 enable, mission orchestrators).
- Before any “promotion” step (deploy enable flags, live paper enable). The gate is enforced by `enforce_csa_gate.py`; if verdict is not PROCEED, the risk acceptance file must exist or the gate fails.

**Rule:** Any step that changes runtime behavior (even paper-only flags) must pass the CSA gate or require an explicit CSA_RISK_ACCEPTANCE artifact.
