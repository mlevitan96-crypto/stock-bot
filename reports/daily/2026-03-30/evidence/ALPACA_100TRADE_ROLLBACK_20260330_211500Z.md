# ALPACA_100TRADE_ROLLBACK_20260330_211500Z

1. **Revert commit** (or restore files): `runner_core.py`, `templates.py`, `checkpoint_100.py`, `config/alpaca_telegram_integrity.json`, `run_alpaca_telegram_integrity_cycle.py`, tests, MEMORY_BANK, TELEMETRY_CHANGELOG, evidence.
2. **Remove** `telemetry/alpaca_telegram_integrity/checkpoint_100.py` if reverting manually.
3. **State:** Delete or truncate `state/alpaca_100trade_sent.json` on droplet if desired.
4. **systemd:** `alpaca-telegram-integrity.timer` **unchanged** — no unit edits required for rollback.
