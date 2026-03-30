# ALPACA_TELEGRAM_ROLLBACK_PLAN_20260330_190500Z

## Git rollback

```bash
cd /root/stock-bot
git log --oneline -5   # find pre-change SHA
git checkout <SHA> -- scripts/notify_alpaca_trade_milestones.py scripts/install_cron_alpaca_notifier.py scripts/install_alpaca_notifier_cron.sh scripts/governance/telegram_failure_detector.py deploy/systemd/telegram-failure-detector.service MEMORY_BANK.md memory_bank/TELEMETRY_CHANGELOG.md
# Or: git revert <commit>
```

Remove new paths if reverting fully:

- `telemetry/alpaca_telegram_integrity/`, `scripts/run_alpaca_telegram_integrity_cycle.py`, `config/alpaca_telegram_integrity.json`, `deploy/systemd/alpaca-telegram-integrity.*`, `scripts/install_alpaca_telegram_integrity_on_droplet.sh`, tests, evidence (optional).

## systemd

```bash
sudo systemctl disable --now alpaca-telegram-integrity.timer
sudo rm -f /etc/systemd/system/alpaca-telegram-integrity.service /etc/systemd/system/alpaca-telegram-integrity.timer
sudo systemctl daemon-reload
```

## Restore legacy cron (only if intentionally reverting script behavior)

Re-install old `notify_alpaca_trade_milestones` from git history and add crontab line manually (not recommended once stubbed).

## Restore failure pager timer

```bash
sudo systemctl enable --now telegram-failure-detector.timer
```

## State cleanup (optional)

`state/alpaca_milestone_250_state.json`, `state/alpaca_telegram_integrity_cycle.json` — safe to delete to reset counters (will re-alert).
