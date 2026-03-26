# Alpaca forward truth contract — droplet proof

**Timestamp:** `20260327_FORWARD_TRUTH_FINAL`

## Git on droplet

`git fetch origin main && git reset --hard origin/main` → **41362211274e01a4e92de141ddad4e781537b090** (see `reports/audit/ALPACA_FORWARD_TRUTH_CONTRACT_DROPLET_BUNDLE_20260327_FORWARD_TRUTH_FINAL.json`).

## Scheduler

- **Timer:** `alpaca-forward-truth-contract.timer` — `active (waiting)`, `enabled`; triggers every 15 minutes (`OnCalendar=*-*-* *:00,15,30,45:00`).
- **Service:** `alpaca-forward-truth-contract.service` — `Type=oneshot`, `ExecStart=/bin/bash /root/stock-bot/deploy/systemd/alpaca-forward-truth-contract-run.sh`.

Full `systemctl cat` excerpts are in the bundle JSON under `steps.systemctl_cat_service` and `steps.systemctl_cat_timer`.

## Manual invocation

Deploy helper runs the same shell wrapper as the timer. **Runner process exit code:** **0** (`manual_exit_code` in bundle) → **CERT_OK** (`trades_incomplete == 0`).

## Artifacts (examples from droplet)

Recent JSON runs (newest first), from bundle `steps.recent_run_artifacts`:

- `/root/stock-bot/reports/ALPACA_FORWARD_TRUTH_RUN_20260326_181503Z.json`
- (additional timestamps in bundle list)

Head of latest run JSON (`steps.latest_run_json_head` in bundle) shows `forward_truth_contract` / `initial_gate.trades_incomplete: 0` / `open_ts_epoch` aligned with `max(STRICT_EPOCH_START, now−72h)` (here floor clamped to `STRICT_EPOCH_START`).

## Journal

`journalctl -u alpaca-forward-truth-contract.service` shows timer-fired starts and successful `Deactivated successfully` (excerpt in bundle `steps.journalctl_service`).

## Machine-readable bundle

`reports/audit/ALPACA_FORWARD_TRUTH_CONTRACT_DROPLET_BUNDLE_20260327_FORWARD_TRUTH_FINAL.json`
