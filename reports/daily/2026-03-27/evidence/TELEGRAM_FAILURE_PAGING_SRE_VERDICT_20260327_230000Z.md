# SRE verdict — Telegram failure paging

**SRE_VERDICT: `OPERATIONALLY_SOUND`**

- **Scheduler:** `telegram-failure-detector.timer` active on droplet; **5-minute** cadence.
- **Idempotency:** `state/telegram_failure_pager_state.json` tracks alerted signatures and last per-window state.
- **Failure modes:** `journalctl` + audit JSONL for Alpaca; file mtimes + cron log for Kraken integrity.
- **Risk:** Droplet must **`git pull`** (or deploy) so `telegram_failure_detector.py` exists at the `ExecStart` path; installer uploads units but **code ships with repo**.
