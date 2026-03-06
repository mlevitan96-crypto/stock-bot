# Automation Test Run — 20260305-165820

**Branch used:** `automation-test/20260305-165820`  
**PR:** #3 (opened then closed)  
**Events triggered:** PR opened, PR updated (follow-up commit), push to main.

---

## Cursor Automations run history (verify in dashboard)

Run history and logs for Cursor Cloud Automations are **not queryable from the repo**. Verify at [cursor.com/automations](https://cursor.com/automations):

| Automation | Expected trigger | Expected runs | Verify in dashboard |
|------------|------------------|---------------|---------------------|
| PR Risk Classifier | PR opened, PR pushed | 2 | Check run history for PR #3 |
| PR Bug Review | PR opened, PR pushed | 2 | Check run history for PR #3 |
| Security Review | Push to main | 1 | Check run history for commit 64d10cd |
| Governance Integrity | Cron */10 * * * * | 1+ (or use local script) | Check run history or see GOVERNANCE_AUTOMATION_STATUS.json |
| Weekly Governance Summary | Cron 0 0 * * 0 | Scheduled only | Confirm next run Sunday 00:00 UTC |

---

## Local verification performed

- **Governance Integrity (local):** `python scripts/automations/run_governance_integrity_once.py` was run.  
  - `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json` exists, timestamp recent, `anomalies_detected: false`, `status: ok`.
- **PR and push events:** Created PR #3, pushed follow-up commit to same branch, pushed trivial commit to main (64d10cd). These events trigger the Cursor Cloud automations if they are active and connected to the repo.

---

## Run logs

Cursor Automations run logs are available only in the Cursor Automations dashboard. Capture them from [cursor.com/automations](https://cursor.com/automations) → each automation → Run history.
