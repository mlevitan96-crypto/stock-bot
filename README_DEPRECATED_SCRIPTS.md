# Deprecated / legacy one-off scripts

**Canonical production entry points:** See MEMORY_BANK.md and `reports/repo_audit/CANONICAL_REPO_STRUCTURE.md`.

This repo contains many root-level and `scripts/` scripts that were written for one-off diagnostics, fixes, or investigations. They are **not** invoked by cron, deploy, or the governance loop.

## Prefer these for production

- **Trading / dashboard:** `main.py`, `dashboard.py`, `deploy_supervisor.py`
- **EOD / cron:** `board/eod/run_stock_quant_officer_eod.py`, `board/eod/run_eod_on_droplet.py`, `board/eod/deploy_on_droplet.sh`
- **Governance:** `scripts/run_equity_governance_loop_on_droplet.sh`, `scripts/governance/deploy_and_start_governance_loop_on_droplet.py`, `scripts/governance/generate_recommendation.py`, `scripts/governance/run_board_review_on_droplet_data.py`
- **Effectiveness:** `scripts/analysis/run_effectiveness_reports.py`, `scripts/analysis/compare_effectiveness_runs.py`
- **Replay:** `historical_replay_engine.py`, `scripts/replay/*.py`
- **Deploy:** `droplet_client.py`, `deploy_to_droplet.py`

## Legacy one-off scripts (use only for manual diagnostics)

Root-level examples: `RUN_*_NOW.py`, `EXECUTE_*.py`, `FIX_*.py`, `COMPLETE_*.py`, `*_diagnostic*.py`, `*_investigation*.py`, `run_droplet_*.py` (ad-hoc), etc.  
Scripts under `archive/` are legacy deployment and investigation; do not use for production paths.

If in doubt, check `reports/repo_audit/CANONICAL_PATHS.json` and `reports/repo_audit/UNUSED_SCRIPTS.json`.
