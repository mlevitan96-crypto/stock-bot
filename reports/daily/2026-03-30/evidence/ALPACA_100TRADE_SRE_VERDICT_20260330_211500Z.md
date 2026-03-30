# ALPACA_100TRADE_SRE_VERDICT_20260330_211500Z

**Verdict: OK**

- **Timer:** Still single `alpaca-telegram-integrity.timer`; no additional units.
- **Paging:** Deferred alert at most once per degraded episode per session anchor; informational at most once when green; distinct `script_name` values for Telegram audit trails.
- **Guard file:** Atomic write pattern (tmp + replace) consistent with other state JSON.
- **Logs:** `logs/alpaca_telegram_integrity.log` unchanged (one line per cycle).
- **Errors:** Send failures do not advance `checkpoint_100_info_sent`; state still saved with `last_count`.
