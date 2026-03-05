# Cursor Automations — UI Activation Proof

**Date:** 2026-03-05  
**Mission:** Create and activate all five Cursor Automations for stock-bot with Slack disabled; verify in dashboard and via test PR and Governance Integrity run.

---

## Agent limitation (UI-automation mode)

**The agent cannot access cursor.com/automations or perform any UI actions.** There is no browser automation, no Cursor account login, and no API available to create or enable automations from this environment. Creation and activation of the five automations **must be done by a human** in the Cursor Automations dashboard.

The agent has:

1. **Prepared a UI runbook** with copy-paste instruction blocks for each automation:  
   **`reports/audit/CURSOR_AUTOMATIONS_UI_RUNBOOK.md`**
2. **Used the existing YAML/TS files** in `.cursor/automations/` as the source of truth and derived the runbook and instructions from them, with **Slack explicitly disabled** in every instruction block.
3. **Written this proof artifact** so that once you complete the UI steps and verification, you can record the outcome here.

---

## What you must do

1. Open **[cursor.com/automations](https://cursor.com/automations)** and sign in.
2. Follow **`reports/audit/CURSOR_AUTOMATIONS_UI_RUNBOOK.md`** from Phase 1 through Phase 6 to create all five automations (PR Risk Classifier, PR Bug Review, Security Review, Governance Integrity, Weekly Governance Summary).
3. For each automation: set **Repository = stock-bot**, correct **Trigger**, enable only the **Tools** listed (no Slack), and paste the **Instructions** from the runbook.
4. **Save and Activate** each automation.
5. Complete the **Phase 7 verification checklist** in the runbook:
   - Confirm all five appear and are active.
   - Confirm triggers match (PR opened/pushed; Push to main; `*/10 * * * *`; `0 0 * * 0`).
   - Confirm Slack is not configured for any.
   - Open a **test PR** (e.g. a small doc or comment-only change) and confirm both PR Risk Classifier and PR Bug Review run and post comments.
   - Confirm **Governance Integrity** has run at least once (check automation run history or `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json` timestamp after a run).

---

## Verification record (fill in after you complete the steps)

| # | Automation              | Created | Active | Trigger correct | Slack disabled | Notes |
|---|-------------------------|---------|--------|------------------|----------------|-------|
| 1 | PR Risk Classifier      | ☐       | ☐      | ☐                | ☐              |       |
| 2 | PR Bug Review           | ☐       | ☐      | ☐                | ☐              |       |
| 3 | Security Review         | ☐       | ☐      | ☐                | ☐              |       |
| 4 | Governance Integrity    | ☐       | ☐      | ☐                | ☐              |       |
| 5 | Weekly Governance Summary | ☐     | ☐      | ☐                | ☐              |       |

- **Test PR:** Opened on (date) ________. PR Risk Classifier commented: ☐ Yes ☐ No. PR Bug Review commented: ☐ Yes ☐ No.  
- **Governance Integrity:** First run observed (date/time or run ID): ________.  
- **Completed by:** ________  **Date:** ________  

---

## Exit conditions (mission)

Return control only when:

- [ ] All five automations are created and active in the dashboard.
- [ ] All triggers match the YAML definitions (see runbook).
- [ ] Slack is disabled for all automations.
- [ ] A test PR has been processed by both PR automations (comments posted).
- [ ] Governance Integrity has run at least once.
- [ ] This proof artifact is updated with the verification record above.

**Once you have completed the runbook and verification, update the checkboxes and table in this file and commit it.** The runbook (`CURSOR_AUTOMATIONS_UI_RUNBOOK.md`) is the executable guide; this file is the proof of completion.

---

*Architecture: Cursor Automations → Cursor → GitHub → Droplet → CSA/SRE → Deploy Gates → Artifacts. Slack remains disabled.*
