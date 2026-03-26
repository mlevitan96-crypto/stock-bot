# Alpaca forward truth contract — scheduler (systemd)

**Timestamp:** `20260327_FORWARD_TRUTH_FINAL`

## Choice: systemd timer + oneshot service (preferred)

**Repository paths:**

- `deploy/systemd/alpaca-forward-truth-contract.service`
- `deploy/systemd/alpaca-forward-truth-contract.timer`
- `deploy/systemd/alpaca-forward-truth-contract-run.sh`

**Timer:** `OnCalendar=*-*-* *:00,15,30,45:00` (every 15 minutes wall clock), `Persistent=true`, `AccuracySec=1min`.

**Service:** `Type=oneshot`, `WorkingDirectory=/root/stock-bot`, runs the shell wrapper so each invocation gets a fresh UTC timestamp for artifact filenames.

**Command (effective):**

`/root/stock-bot/venv/bin/python -u scripts/audit/alpaca_forward_truth_contract_runner.py` with `--window-hours 72`, `--repair-max-rounds 6`, `--repair-sleep-seconds 10`, and timestamped `--json-out` / `--md-out` / `--incident-*` under `reports/` and `reports/audit/`.

## Droplet install

```bash
cp /root/stock-bot/deploy/systemd/alpaca-forward-truth-contract.service /etc/systemd/system/
cp /root/stock-bot/deploy/systemd/alpaca-forward-truth-contract.timer /etc/systemd/system/
chmod +x /root/stock-bot/deploy/systemd/alpaca-forward-truth-contract-run.sh
systemctl daemon-reload
systemctl enable --now alpaca-forward-truth-contract.timer
```

## Verification commands

- `systemctl cat alpaca-forward-truth-contract.service`
- `systemctl cat alpaca-forward-truth-contract.timer`
- `systemctl status alpaca-forward-truth-contract.timer --no-pager -l`
- `journalctl -u alpaca-forward-truth-contract.service -n 120 --no-pager`

**Note:** Live `systemctl` / `journalctl` text is captured in `reports/audit/ALPACA_FORWARD_TRUTH_CONTRACT_DROPLET_BUNDLE_20260327_FORWARD_TRUTH_FINAL.json` after deploy.
