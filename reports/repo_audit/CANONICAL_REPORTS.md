# Canonical Reports

**Which report paths are read by code (dashboard, governance, effectiveness).** Generated 2026-02-27.

## Dashboard reads

| Path pattern | Purpose |
|--------------|---------|
| `reports/equity_governance/equity_governance_*/lock_or_revert_decision.json` | /api/governance/status |
| `reports/effectiveness_*/effectiveness_aggregates.json` | /api/governance/status fallback |
| `reports/effectiveness_baseline_blame` | Fallback when no effectiveness_* dirs |
| `reports/{date}_stock-bot_combined.json` | /api/strategy/comparison |
| `reports/*_weekly_promotion_report.json` | /api/strategy/comparison |
| `reports/*_stock-bot_wheel.json` | /api/stockbot/wheel_analytics fallback |

## Governance loop / scripts

| Path | Used by |
|------|---------|
| `reports/equity_governance/` | dashboard, run_board_review_on_droplet_data.py, run_board_persona_review.py |
| `reports/effectiveness_baseline_blame/effectiveness_aggregates.json` | dashboard, generate_recommendation.py, run_board_persona_review.py |
| `reports/effectiveness_*/effectiveness_aggregates.json` | run_effectiveness_reports.py output; compare_effectiveness_runs.py |
| `reports/signal_review/*` | run_investigation_on_droplet_and_fetch.py, enable_truth_logs_on_droplet_and_re_run.py |
| `reports/governance/BOARD_REVIEW_*.md|.json` | run_board_review_on_droplet_data.py output |
| `reports/EXIT_DAY_SUMMARY_*.md`, `reports/EXIT_INTEL_PNL_*.md`, `reports/UW_INTEL_PNL_*.md` | run_postclose_analysis_pack.py |
| `reports/_dashboard/intel_dashboard_generator.py` | run_postclose_analysis_pack.py |
| `reports/data_integrity/DATA_FEED_HEALTH_CONTRACT.*` | data_feed_health_contract.py |

## Not canonical (do not depend on these for live behavior)

- reports/blocked_expectancy, reports/blocked_signal_expectancy
- reports/cursor_final_remediation, reports/followup_diag_artifacts
- reports/nuclear_audit, reports/truth_audit, reports/truth_audit_fix
- reports/effectiveness_example, reports/effectiveness_test_run
- One-off root reports/*.md (STRATEGIC_RESET_*.md, etc.) — keep for history or archive
