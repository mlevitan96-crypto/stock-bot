# Governance Discovery Index

Generated: (run scripts/governance_cleanup_and_ai_board_activation.sh to refresh)

Canonical Scheduled Processes:
- EOD: board/eod/run_stock_quant_officer_eod.py @ 21:30 UTC (Memory Bank §5.5)
- Sync: scripts/droplet_sync_to_github.sh @ 21:32 UTC (droplet)
- Local pull (repeatable): scripts/pull_eod_to_local.ps1 or scripts/pull_eod_to_local.sh — run weekdays after 21:35 UTC to get latest EOD without conflicts.

Non-Canonical / Ad-Hoc Tools:
- reports/_daily_review_tools/run_droplet_end_of_day_review.py (Memory Bank §5.4)

AI Governance:
- Multi-model review required for promotion decisions
- Counterfactual analysis assigned to Gemini 2.5 Pro

Cursor audits MUST consult:
1. Memory Bank
2. This index
3. Droplet cron/systemd
