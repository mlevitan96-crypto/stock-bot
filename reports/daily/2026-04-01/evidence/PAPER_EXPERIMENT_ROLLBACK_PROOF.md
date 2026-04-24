# PAPER_EXPERIMENT_ROLLBACK_PROOF

- **Stateful services:** **unchanged** — no `systemctl restart stock-bot` before or after `paper_experiment_offline_displacement_stats.py`.
- **Codebase on disk:** script **additive** under `scripts/audit/`; no modification to `main.py`, `deploy_supervisor.py`, or systemd units for this experiment.
- **Rollback action:** delete or ignore `PAPER_EXPERIMENT_RESULTS.json` / this memo; no runtime flag was toggled.
