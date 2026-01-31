# Governance Discovery Index

Generated: (run scripts/governance_cleanup_and_ai_board_activation.sh to refresh)

Canonical Scheduled Processes:
- EOD: board/eod/run_stock_quant_officer_eod.py @ 21:30 UTC (Memory Bank §5.5)
- Sync: scripts/droplet_sync_to_github.sh @ 21:32 UTC (droplet)
- Molt: scripts/run_molt_on_droplet.sh @ 21:35 UTC weekdays (install via scripts/install_molt_cron_on_droplet.py)
- Local pull (repeatable): scripts/pull_eod_to_local.ps1 or scripts/pull_eod_to_local.sh — run weekdays after 21:35 UTC to get latest EOD without conflicts.

Non-Canonical / Ad-Hoc Tools:
- reports/_daily_review_tools/run_droplet_end_of_day_review.py (Memory Bank §5.4)

Observability Runners (DropletClient):
- scripts/run_exit_join_and_blocked_attribution_on_droplet.py — exit join health + blocked trade intel
- scripts/run_snapshot_outcome_attribution_on_droplet.py — snapshot→outcome attribution + shadow
- scripts/run_snapshot_harness_on_droplet.py — snapshot harness verification
- scripts/run_molt_on_droplet.py — Molt workflow (orchestrator, sentinel, board, discipline, memory evolution)

Molt Artifacts:
- reports/LEARNING_STATUS_<DATE>.md
- reports/ENGINEERING_HEALTH_<DATE>.md
- reports/PROMOTION_PROPOSAL_<DATE>.md or REJECTION_WITH_REASON_<DATE>.md
- reports/PROMOTION_DISCIPLINE_<DATE>.md
- reports/MEMORY_BANK_CHANGE_PROPOSAL_<DATE>.md

Reports:
- reports/EXIT_JOIN_HEALTH_<DATE>.md — snapshot→exit match rate
- reports/BLOCKED_TRADE_INTEL_<DATE>.md — blocked counts, intelligence at block time

AI Governance:
- Multi-model review required for promotion decisions
- Counterfactual analysis assigned to Gemini 2.5 Pro

Cursor audits MUST consult:
1. Memory Bank
2. This index
3. Droplet cron/systemd
