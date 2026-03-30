# ALPACA_TELEGRAM_LEGACY_INVENTORY_20260330_190500Z

Alpaca droplet (`/root/stock-bot`), read-only inventory before reset.

## systemd / timers (observed)

| Unit | Role |
|------|------|
| `telegram-failure-detector.timer` | Every 5m — `telegram_failure_detector.py` (post-close, milestone log freshness, direction_readiness) |
| `alpaca-postclose-deepdive.timer` | Weekday post-close deep dive + Telegram audit jsonl |
| `alpaca-forward-truth-contract.timer` | Forward truth contract (separate) |

## crontab (root, observed)

| Schedule | Command |
|----------|---------|
| `*/5 9-21 * * 1-5` | `check_direction_readiness_and_run.py` → `logs/direction_readiness_cron.log` |
| `*/10 13-21 * * 1-5` | `notify_alpaca_trade_milestones.py` → `logs/notify_milestones.log` (**legacy milestone**) |

## Scripts / helpers

- `scripts/alpaca_telegram.py` — `send_governance_telegram` (retained; used by all sends).
- `scripts/notify_alpaca_trade_milestones.py` — **100/500 promotion watermark** (legacy; replaced).
- `scripts/governance/telegram_failure_detector.py` — pager + auto-heal (Alpaca-only code paths; unit Description previously implied Kraken — corrected in repo).
- `scripts/alpaca_postclose_deepdive.py` — EOD Telegram + `reports/alpaca_daily_close_telegram.jsonl`.
- Board Tier1/2/3, convergence, gate, heartbeat — optional `--telegram` (unchanged).

## Env

- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` — `/root/.alpaca_env` and/or `/root/stock-bot/.env`.

## State / logs

- `state/alpaca_trade_notifications.json` — legacy milestone dedupe (no longer written by stub).
- `state/telegram_failure_pager_state.json` — failure pager dedupe.
- `logs/notify_milestones.log` — legacy milestone cron output.

Kraken: no Kraken Telegram scripts found in this inventory slice.
