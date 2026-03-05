# Cursor Automations — Activation Guide (Slack Disabled)

This document describes how to **create and activate** the 5 Cursor Automations in the Cursor UI at [cursor.com/automations](https://cursor.com/automations). **Slack is not configured;** all automations run with PR comments, GitHub issues, and file writes only.

## Prerequisites

- Repository: **stock-bot** (this repo)
- Branch: **main** where applicable
- Do **not** configure Slack or any external webhooks

## 1) PR Risk Classifier

- **Name:** PR Risk Classifier
- **Trigger:** Pull request opened **OR** Pull request pushed
- **Repository/branch:** stock-bot, main
- **Tools:** Comment on pull request; Request reviewers (if supported). **Do not enable Slack.**
- **Prompt/instructions:** Use the logic in `.cursor/automations/pr_risk_classifier.ts`:
  - Read diff and metadata
  - Classify PR as LOW / MEDIUM / HIGH from blast radius, infra impact, trading logic impact, governance impact, config changes, dependency changes
  - Post a PR comment with risk level, reasoning, recommended reviewers
  - If HIGH: add label `requires-governance-review` (or equivalent)
  - Auto-approve for LOW risk: **default OFF** unless explicitly enabled in automation config
- **Save and activate**

## 2) PR Bug Review (Bugbot-style)

- **Name:** PR Bug Review
- **Trigger:** Pull request opened **OR** Pull request pushed
- **Repository/branch:** stock-bot, main
- **Tools:** Comment on pull request (inline). **Do not enable Slack.**
- **Prompt/instructions:** Use `.cursor/automations/pr_bug_review.ts`:
  - Analyze diff for logic errors, regressions, missing edge cases, inconsistent naming, dead code, missing tests
  - Leave inline comments where issues are found; suggest concrete fixes
- **Save and activate**

## 3) Security Review

- **Name:** Security Review
- **Trigger:** Push to branch → **main**
- **Repository/branch:** stock-bot, main
- **Tools:** Create GitHub issue. Comment on commit or PR if available. **Do not enable Slack.**
- **Prompt/instructions:** Use `.cursor/automations/security_review.ts`:
  - Scan for secrets/credentials, unsafe patterns, insecure network calls, dependency risk notes
  - Produce summary with severity (INFO / LOW / MEDIUM / HIGH / CRITICAL)
  - If HIGH or CRITICAL: open a GitHub issue with details and recommended actions
- **Save and activate**

## 4) Governance Integrity (Scheduled)

- **Name:** Governance Integrity
- **Trigger:** Scheduled → cron `*/10 * * * *` (every 10 minutes)
- **Repository/branch:** stock-bot, main
- **Tools:** Create/update GitHub issue. **Do not enable Slack.**
- **Prompt/instructions:** Use `.cursor/automations/governance_integrity.ts`:
  - Validate repo structure, config drift, governance contract files, required artifact dirs, no deprecated/Clawdbot/Moltbot reintroduction
  - Write/update `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json` with `timestamp`, `status` (ok | anomalies), `checks`, `anomalies`
  - If anomalies: open or update a GitHub issue summarizing anomalies
- **Save and activate**

## 5) Weekly Governance Summary

- **Name:** Weekly Governance Summary
- **Trigger:** Scheduled → cron `0 0 * * 0` (Sunday 00:00 UTC)
- **Repository/branch:** stock-bot, main
- **Tools:** Repo access and file writes only. **Do not enable Slack.**
- **Prompt/instructions:** Use `.cursor/automations/weekly_governance_summary.ts`:
  - Summarize last 7 days: commits to main, PRs merged, CSA verdicts, SRE anomalies, deploys, shadow/paper/live, config changes
  - Write `reports/board/WEEKLY_GOVERNANCE_SUMMARY_<YYYY-MM-DD>.md`
- **Save and activate**

## Verification

- In [cursor.com/automations](https://cursor.com/automations): confirm all 5 automations are **present**, **enabled**, **correct repo**, **correct triggers**
- Confirm **no Slack** is configured for any of them

## Integration

Once active, automation outputs are first-class evidence:

- **CSA** ingests `GOVERNANCE_AUTOMATION_STATUS.json` and weekly summaries via `scripts/audit/csa_automation_evidence.py`; verdict and findings include an "Automation Evidence" section.
- **SRE** reads `GOVERNANCE_AUTOMATION_STATUS.json`; when status is anomalies, writes `reports/audit/SRE_AUTOMATION_ANOMALY_<date>.md` and sets `automation_anomalies_present` in SRE_STATUS.json.
- **Mission runners** and board packets include automation status (e.g. `scripts/board/build_next_action_packet.py`).

See `docs/ALPACA_GOVERNANCE_CONTEXT.md` and `docs/governance/CHIEF_STRATEGY_AUDITOR.md` for full governance flow.
