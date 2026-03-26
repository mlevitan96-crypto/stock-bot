# Alpaca SRE auto-repair — droplet proof

**Timestamp:** `20260327_SRE_AUTO_REPAIR_FINAL`

## Git / deploy

- Droplet `git reset --hard origin/main` → commit recorded in `reports/ALPACA_SRE_AUTO_REPAIR_DROPLET_BUNDLE_20260327_SRE_AUTO_REPAIR_FINAL.json` (`steps.git.stdout`).
- `systemctl restart alpaca-forward-truth-contract.timer` after upload (`steps.restart_timer`).

## Manual runner invocation

- Wrapper: `deploy/systemd/alpaca-forward-truth-contract-run.sh` → `alpaca_forward_truth_contract_runner.py`.
- **Process exit code:** see `manual_exit_code` in bundle (latest run: **2** = INCIDENT after bounded SRE cycles).
- Log tail: `steps.manual_run.stdout_tail` (stderr from runner includes `alpaca_forward_truth_contract_runner: exit 2 INCIDENT` when applicable).

## Strict gate + SRE (from `latest_run_json_head`)

- `sre_auto_repair_engine: true`.
- `initial_gate` excerpt shows live `/root/stock-bot` cohort (e.g. `trades_seen` / `trades_incomplete` / `reason_histogram`).
- Full per-run JSON on droplet: newest path under `steps.recent_run_artifacts` (e.g. `ALPACA_FORWARD_TRUTH_RUN_*.json`) containing `sre_repair_actions_applied`, `sre_classification_per_trade_id`, `sre_engine_meta`, `final_gate`.

## Artifacts

- Bundle: `reports/ALPACA_SRE_AUTO_REPAIR_DROPLET_BUNDLE_20260327_SRE_AUTO_REPAIR_FINAL.json`
- Forward bundle duplicate: `reports/audit/ALPACA_FORWARD_TRUTH_CONTRACT_DROPLET_BUNDLE_20260327_FORWARD_TRUTH_FINAL.json`

## Interpretation (latest capture)

Exit **2** with residual incompletes indicates **actionable INCIDENT** after bounded additive attempts (e.g. trades where `build_lines_for_trade` cannot emit rows). Exit **0** when cohort returns to `trades_incomplete == 0`.
