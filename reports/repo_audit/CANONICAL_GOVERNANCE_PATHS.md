# Canonical Governance Paths

**Governance loop, board review, effectiveness — single source of truth.** Generated 2026-02-27.

## Scripts (invoked by cron or deploy)

| Script | Purpose |
|--------|---------|
| `scripts/run_equity_governance_loop_on_droplet.sh` | Main governance loop on droplet |
| `scripts/governance/deploy_and_start_governance_loop_on_droplet.py` | Deploy and start loop |
| `scripts/governance/generate_recommendation.py` | Recommendation from effectiveness + governance state |
| `scripts/governance/run_board_review_on_droplet_data.py` | Board review from droplet data → reports/governance/ |
| `scripts/analysis/run_effectiveness_reports.py` | Effectiveness run → reports/effectiveness_baseline_blame or effectiveness_* |
| `scripts/analysis/compare_effectiveness_runs.py` | Compare two effectiveness dirs |
| `scripts/analysis/run_expectancy_gate_diagnostic.py` | Expectancy gate diagnostic → reports/effectiveness_baseline_blame |

## Paths (read/write)

| Path | Role |
|------|------|
| `reports/equity_governance/equity_governance_*` | Run dirs; lock_or_revert_decision.json, overlay_config.json |
| `reports/effectiveness_baseline_blame/` | Default effectiveness output; effectiveness_aggregates.json |
| `reports/effectiveness_*/` | Alternative effectiveness run dirs |
| `state/equity_governance_loop_state.json` | Loop state (last lever, candidate expectancy, etc.) |
| `reports/governance/BOARD_REVIEW_DROPLET_DATA_*.md|.json` | Board review output |

## Dashboard

- `/api/governance/status` reads: latest `reports/equity_governance/equity_governance_*/lock_or_revert_decision.json` and `reports/effectiveness_*/effectiveness_aggregates.json` (fallback: effectiveness_baseline_blame).

Cleanup must not remove or relocate these paths without updating dashboard and all scripts above.
