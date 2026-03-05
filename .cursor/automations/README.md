# Cursor Automations — Governance Suite

This directory defines the **Cursor Automations** governance layer for stock-bot. Automations run in **Cursor Cloud** and act as a pre-merge, pre-deploy governance layer. They do **not** modify droplet code or runtime behavior.

## Purpose

- **PR risk classification** — Classify PRs by blast radius, infra/trading/governance impact; tag and route for review.
- **PR bug review** — Deep diff analysis (logic errors, regressions, edge cases, dead code, missing tests); inline comments.
- **Security review** — On push to main: secrets, credentials, unsafe patterns, dependency vulns; GitHub Security + optional Slack.
- **Governance integrity** — Every 10 minutes: repo structure, config drift, required artifacts, no deprecated/Clawdbot/Moltbot reintroduction.
- **Weekly governance summary** — Sunday 00:00 UTC: commits, PRs, CSA verdicts, SRE, deploys, shadow/paper/live; report to `reports/board/`.

## Integration with Governance

```
Cursor Automations → Cursor (Cloud Agents) → GitHub (PRs, main pushes)
                         ↓
                   Slack (optional)
                         ↓
                   reports/audit/ and reports/board/
                         ↓
                   CSA / SRE / Deploy Gates (unchanged; droplet authority unchanged)
```

- Automations **do not** run on the droplet.
- They **do not** change trading logic, config, or deploy gates.
- They **strengthen** the organism: earlier signal, better triage, integrity checks, and audit trail.

## How to Use

1. **Cursor Dashboard**: Go to [cursor.com/automations](https://cursor.com/automations) and create automations from the specs in this directory.
2. **Per automation**: Use the `.yaml` file for **trigger** and **settings**; use the `.ts` file as the **prompt/instruction** source (paste or reference in the automation prompt).
3. **Slack**: Set `SLACK_WEBHOOK_URL` (or equivalent) in Cloud Agents environment; automations will post when configured. If unset, they skip Slack silently.
4. **Repository/branch**: For scheduled and push-to-main automations, select this repo and `main` in the trigger settings.

### Setup checklist (after push to main)

- [ ] At [cursor.com/automations](https://cursor.com/automations), create 5 automations (one per YAML/TS pair above).
- [ ] For each: set trigger per the `.yaml`, paste or reference the `.ts` instructions in the prompt, enable tools (Comment on PR, Send to Slack, etc.).
- [ ] Verify in the dashboard that PR-triggered and scheduled automations appear and are enabled.
- [ ] Open a small test PR to confirm PR Risk Classifier and PR Bug Review fire and post comments.
- [ ] Confirm Governance Integrity runs (scheduled or manually): check `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json` or automation logs.

## How to Disable

- **Single automation**: Disable it in [cursor.com/automations](https://cursor.com/automations).
- **All automations**: Disable or delete each automation in the dashboard; no code change required on droplet.

## How to Extend

- Add new `.yaml` + `.ts` pairs in `.cursor/automations/`.
- Document trigger, behavior, and outputs in the YAML and in this README.
- Keep Slack and GitHub actions optional and fail-safe (no webhook → skip Slack).

## Files

| File | Trigger | Output / Action |
|------|---------|------------------|
| `pr_risk_classifier.yaml` / `.ts` | PR opened/updated | Comment: risk level, reasoning, reviewers; tag `requires-governance-review` if HIGH; optional Slack |
| `pr_bug_review.yaml` / `.ts` | PR opened/updated | Inline PR comments with findings and suggested fixes |
| `security_review.yaml` / `.ts` | Push to main | Security summary; GitHub issue + Slack if HIGH |
| `governance_integrity.yaml` / `.ts` | Every 10 min | `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json`; issue + Slack if anomalies |
| `weekly_governance_summary.yaml` / `.ts` | Sunday 00:00 UTC | `reports/board/WEEKLY_GOVERNANCE_SUMMARY_<date>.md`; optional Slack |

## Local / CI verification

- **Governance integrity (one-off):**  
  `python scripts/automations/run_governance_integrity_once.py`  
  Writes `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json` and prints whether anomalies were detected. Use to verify checks or run in CI; Slack and GitHub issues are only sent by the Cursor Cloud automation.
