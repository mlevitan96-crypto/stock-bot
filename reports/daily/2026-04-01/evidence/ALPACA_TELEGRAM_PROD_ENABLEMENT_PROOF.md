# Phase 5 — Telegram governance / prod enablement (droplet)

## Systemd services (grep: telegram / alpaca / stock-bot)

```
alpaca-forward-truth-contract.service   inactive dead
alpaca-postclose-deepdive.service       inactive dead
alpaca-telegram-integrity.service       inactive dead
stock-bot-dashboard.service             active running
stock-bot.service                       active running
```

## Timers (enabled / active)

```
systemctl is-enabled alpaca-postclose-deepdive.timer alpaca-telegram-integrity.timer alpaca-forward-truth-contract.timer
enabled
enabled
enabled

systemctl is-active alpaca-postclose-deepdive.timer alpaca-telegram-integrity.timer
active
active
```

## Unit: integrity cycle

`systemctl cat alpaca-telegram-integrity.service`:

- `ExecStart=/root/stock-bot/venv/bin/python3 /root/stock-bot/scripts/run_alpaca_telegram_integrity_cycle.py`

## Unit: post-close deep dive (also sends Telegram)

`systemctl cat alpaca-postclose-deepdive.service`:

- `ExecStart=/root/stock-bot/venv/bin/python3 /root/stock-bot/scripts/alpaca_postclose_deepdive.py`
- Unit description explicitly includes **Telegram**.

Repo code `scripts/alpaca_postclose_deepdive.py` calls `send_governance_telegram` for live sends (`script_name="postclose_deepdive"`).

## Cron

- `crontab -l` / `sudo crontab -l`: **no** lines matching `telegram|alpaca|stock` (empty / no matches).

## `.env` governance keys

`grep` for `TELEGRAM_GOVERNANCE`, `STRICT_RUNLOG`, `PHASE2_TELEMETRY` on `/root/stock-bot/.env` returned **no lines** at capture (either unset or keys absent from file).

## Verdict: integrity-only Telegram in prod?

**NO** (with current enabled timers).

**Evidence:** `alpaca-postclose-deepdive.timer` is **enabled** and **active**, and its service runs a script that **sends Telegram** independently of the integrity cycle. Therefore Telegram is **not** restricted to the integrity pipeline only.

**Integrity pipeline:** `alpaca-telegram-integrity.timer` → `run_alpaca_telegram_integrity_cycle.py` (enabled/active).
