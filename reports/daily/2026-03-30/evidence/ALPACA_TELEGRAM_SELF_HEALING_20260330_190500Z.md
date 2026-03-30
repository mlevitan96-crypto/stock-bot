# ALPACA_TELEGRAM_SELF_HEALING_20260330_190500Z

## Implemented (safe)

| Action | Condition |
|--------|-----------|
| `mkdir -p` | `logs/`, `state/`, `reports/`, `reports/daily/` |
| `systemctl try-restart alpaca-postclose-deepdive.service` | Unit is **failed** (read-only post-close job) |

## Explicitly NOT auto-fixed

- Missing Telegram secrets, broken venv, `stock-bot` / trading services, schema migrations, log corruption, disk full, Alpaca API auth — **operator alert only** via integrity messaging when detected indirectly (e.g. stale coverage, strict BLOCKED).

## Config

`config/alpaca_telegram_integrity.json` → `self_heal` object toggles `ensure_log_dirs` and `restart_failed_postclose_service`.
