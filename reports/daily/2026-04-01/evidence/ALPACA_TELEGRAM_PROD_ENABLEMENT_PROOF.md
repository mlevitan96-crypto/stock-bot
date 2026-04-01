# Telegram production enablement — integrity closure (2026-04-01)

## Systemd units with `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1` (live `/etc/systemd/system`)

Verified via remote `systemctl cat` after `e8133504` deploy:

- `alpaca-postclose-deepdive.service` — **has** `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1`
- `telegram-failure-detector.service` — **has** `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1`

(`ALPACA_INTEGRITY_CLOSURE_CONTEXT.md` — updated `systemd_cat_*` sections.)

## Timers / enablement (droplet)

| Unit | Enabled |
|------|---------|
| `alpaca-telegram-integrity.timer` | **enabled** |
| `telegram-failure-detector.timer` | **disabled** |
| `alpaca-postclose-deepdive.timer` | **enabled** |

Post-close and failure-detector **services**, when triggered, inherit **integrity-only** Telegram from their unit files. Integrity timer invokes **integrity service**, which does **not** force global integrity-only — allowlisted `script_name` values still send.

## Cron

`crontab -l` and `/etc/cron.d` grep for `stock-bot` returned **empty** in Phase 0 capture (`ALPACA_INTEGRITY_CLOSURE_CONTEXT.md`).

## Allowlist (code)

`scripts/alpaca_telegram.py` — `_INTEGRITY_ONLY_SCRIPT_NAMES` (checkpoint, milestone, integrity alert, test hooks).

## Residual risk (documented)

Manual runs of board / gate / other scripts **without** `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1` in the environment could still call `send_governance_telegram`. Mitigation: optional `.env` global flag (see `ALPACA_TELEGRAM_LOCKDOWN_IMPLEMENTATION.md`).

## Verdict (systemd / scheduled paths)

**YES** — enabled timers that previously sent from post-close or failure-detector are **gated** so only integrity allowlist can open the API from those units. **NO blocker artifact** required for Phase 4 given scope above.
