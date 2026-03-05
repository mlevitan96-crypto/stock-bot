# Governance Discovery Index

Generated: (run scripts/governance_cleanup_and_ai_board_activation.sh to refresh)

Canonical Scheduled Processes:
- EOD: board/eod/run_stock_quant_officer_eod.py @ 21:30 UTC (Memory Bank §5.5)
- Sync: scripts/droplet_sync_to_github.sh @ 21:32 UTC (droplet)
- Learning workflow: scripts/run_molt_on_droplet.sh @ 21:35 UTC weekdays (install via scripts/install_molt_cron_on_droplet.py)
- Daily governance (fail-closed): scripts/run_daily_governance.sh [YYYY-MM-DD] — learning workflow + artifact validation; single PASS/FAIL. See docs/ALPACA_DAILY_RUN_INTEGRITY_CONTRACT.md.
- Local pull (repeatable): scripts/pull_eod_to_local.ps1 or scripts/pull_eod_to_local.sh — run weekdays after 21:35 UTC to get latest EOD without conflicts.

Non-Canonical / Ad-Hoc Tools:
- reports/_daily_review_tools/run_droplet_end_of_day_review.py (Memory Bank §5.4)

Observability Runners (DropletClient):
- scripts/run_exit_join_and_blocked_attribution_on_droplet.py — exit join health + blocked trade intel
- scripts/run_snapshot_outcome_attribution_on_droplet.py — snapshot→outcome attribution + shadow
- scripts/run_snapshot_harness_on_droplet.py — snapshot harness verification
- scripts/run_molt_on_droplet.py — learning workflow (orchestrator, sentinel, board, discipline, memory evolution)

Learning workflow artifacts:
- reports/LEARNING_STATUS_<DATE>.md
- reports/ENGINEERING_HEALTH_<DATE>.md
- reports/PROMOTION_PROPOSAL_<DATE>.md or REJECTION_WITH_REASON_<DATE>.md
- reports/PROMOTION_DISCIPLINE_<DATE>.md
- reports/MEMORY_BANK_CHANGE_PROPOSAL_<DATE>.md

Reports:
- reports/EXIT_JOIN_HEALTH_<DATE>.md — snapshot→exit match rate
- reports/BLOCKED_TRADE_INTEL_<DATE>.md — blocked counts, intelligence at block time

Schema / contract diagnostics (Alpaca governance context):
- scripts/validate_lifecycle_events_schema.py — validate blocked_trades + shadow.jsonl per docs/ALPACA_LIFECYCLE_EVENTS_SCHEMA.md; optional --report PATH, --fail-on-required
- scripts/diagnose_shadow_starvation.py — WARN-only shadow starvation diagnostic per docs/ALPACA_SHADOW_STARVATION_POLICY.md; optional --report PATH, --strict
- scripts/data_feed_health_contract.py — data feed health → reports/data_integrity/DATA_FEED_HEALTH_CONTRACT.md

Daily run integrity (fail-closed):
- scripts/validate_daily_governance_artifacts.py — verify required learning workflow/board artifacts per docs/ALPACA_DAILY_RUN_INTEGRITY_CONTRACT.md; --date, --base-dir, --skip-timestamps
- scripts/run_daily_governance.sh — canonical entry: learning workflow then validation; single PASS/FAIL

AI Governance:
- Multi-model review required for promotion decisions
- Counterfactual analysis assigned to Gemini 2.5 Pro

Cursor Automations (pre-merge/pre-deploy; Cursor Cloud):
- Specs: .cursor/automations/ (README, pr_risk_classifier, pr_bug_review, security_review, governance_integrity, weekly_governance_summary). Activation: reports/audit/CURSOR_AUTOMATIONS_ACTIVATION.md (Slack disabled).
- Artifacts: reports/audit/GOVERNANCE_AUTOMATION_STATUS.json; reports/board/WEEKLY_GOVERNANCE_SUMMARY_<date>.md; Security/Governance Integrity open GitHub issues.
- Integration: CSA ingests automation evidence (scripts/audit/csa_automation_evidence.py); SRE ingests governance status and writes reports/audit/SRE_AUTOMATION_ANOMALY_<date>.md when anomalies. See docs/ALPACA_GOVERNANCE_CONTEXT.md, docs/governance/CHIEF_STRATEGY_AUDITOR.md, docs/SRE_SCANNER_CONTEXT.md.

Cursor audits MUST consult:
1. Memory Bank
2. This index
3. Droplet cron/systemd
