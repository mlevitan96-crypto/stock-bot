# ALPACA_TELEGRAM_LEGACY_REMOVAL_20260330_190500Z

## Disabled / removed on droplet (operator actions)

1. **Crontab:** Remove `notify_alpaca_trade_milestones.py` line:
   - `python3 scripts/install_cron_alpaca_notifier.py` (strips lines), or
   - `(crontab -l | grep -v notify_alpaca_trade_milestones) | crontab -`
2. **systemd:** Prefer **`alpaca-telegram-integrity.timer`** as primary integrity + milestone cadence.
3. **Optional duplicate paging:** `sudo systemctl disable --now telegram-failure-detector.timer` (rollback: `enable --now`).

## Codebase

- `notify_alpaca_trade_milestones.py` → **no-op stub** (prints deprecation to stderr, exit 0).
- `install_alpaca_notifier_cron.sh` → exits 1 with deprecation message.
- `install_cron_alpaca_notifier.py` → removes legacy crontab lines only.

## Unchanged (by design)

- `alpaca_postclose-deepdive` timer/service (EOD path).
- `alpaca_telegram.py` helper.
- Governance `--telegram` on Tier reviews.
- `check_direction_readiness_and_run.py` cron (still separate).

Kraken: not modified.
