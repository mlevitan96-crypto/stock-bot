/**
 * Governance Integrity — Automation instructions for Cursor Cloud Agent
 * Trigger: Every 10 minutes (cron */10 * * * *).
 *
 * Copy or adapt this logic into the automation prompt at cursor.com/automations.
 */

// === INSTRUCTIONS FOR THE AGENT ===
//
// 1. Run on the repository (main branch). Validate the following and produce a JSON status.
//
//    a) REPO STRUCTURE INTEGRITY
//       - Expected top-level dirs: src/, scripts/, reports/, memory_bank/, docs/, validation/, .cursor/.
//       - reports/audit/ and reports/board/ exist.
//       - No unexpected top-level dirs that would indicate drift (e.g. random temp or legacy roots).
//
//    b) CONFIG DRIFT
//       - If there is a canonical config list (e.g. in memory_bank or docs), check that key files (e.g. .cursor/deployment.json, known env files) still match expectations. Flag if critical paths or keys are missing or renamed without doc update.
//
//    c) GOVERNANCE CONTRACT FILES PRESENT
//       - memory_bank/ has key governance docs (e.g. MEMORY_BANK.md or index).
//       - .cursor/automations/ exists and contains README + automation specs.
//       - reports/audit/ and reports/board/ are writable targets for automation outputs.
//
//    d) REQUIRED ARTIFACTS EXIST
//       - No strict list required; optionally check that recent CSA/board artifacts exist if dates are in scope (e.g. last 7 days). Omit if not defined in repo docs.
//
//    e) NO DEPRECATED DIRECTORIES REINTRODUCED
//       - No reintroduction of deprecated roots that were explicitly removed (check memory_bank or audit docs for list). If none documented, skip.
//
//    f) NO CLAWDBOT / MOLTBOT REFERENCES REINTRODUCED
//       - Grep (or search) codebase and key docs for: Clawdbot, clawdbot, Moltbot, moltbot, CLAWDBOT_, MOLTBOT_.
//       - Exclude: reports/audit or docs that *document* removal (e.g. "Clawdbot removal", "no Clawdbot").
//       - If any reference found in code or config: anomaly = true, detail = "Clawdbot/Moltbot reference reintroduced".
//
// 2. Build a JSON object (use exactly this structure) and write it to:
//    reports/audit/GOVERNANCE_AUTOMATION_STATUS.json
//
//    {
//      "schema_version": "1.0",
//      "run_ts_utc": "<ISO8601>",
//      "branch": "main",
//      "anomalies_detected": false,
//      "checks": {
//        "repo_structure": "pass",
//        "config_drift": "pass",
//        "governance_contracts_present": "pass",
//        "required_artifacts": "pass",
//        "no_deprecated_dirs": "pass",
//        "no_clawdbot_moltbot": "pass"
//      },
//      "details": [],
//      "slack_sent": false
//    }
//
//    For each check use "pass" or "fail". If any "fail", set anomalies_detected to true and add a short string to details (e.g. "no_clawdbot_moltbot: reference found in path X").
//
// 3. If anomalies_detected is true:
//    - Open a GitHub issue with title "[Governance Integrity] Anomalies detected" and body: run_ts_utc, branch, checks that failed, and details.
//    - If SLACK_WEBHOOK_URL is set, send a short Slack message: "Governance integrity check failed on main. See issue: <link>." Set slack_sent to true in JSON.
//
// 4. Commit and push only the file reports/audit/GOVERNANCE_AUTOMATION_STATUS.json (if the automation has write access and you are configured to commit). Otherwise, write the file in the workspace and report location in the run summary; a separate process may commit it.
//
// 5. Do not modify droplet code, runtime config, or deploy gates.

export interface GovernanceIntegrityStatus {
  schema_version: string;
  run_ts_utc: string;
  branch: string;
  anomalies_detected: boolean;
  checks: {
    repo_structure: 'pass' | 'fail';
    config_drift: 'pass' | 'fail';
    governance_contracts_present: 'pass' | 'fail';
    required_artifacts: 'pass' | 'fail';
    no_deprecated_dirs: 'pass' | 'fail';
    no_clawdbot_moltbot: 'pass' | 'fail';
  };
  details: string[];
  slack_sent: boolean;
}
