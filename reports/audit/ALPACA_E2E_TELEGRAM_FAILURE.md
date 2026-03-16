# Alpaca E2E — Telegram send failure (surfaced for debugging)

Direct Telegram send on droplet returned False. Governance chain ran successfully; only notification failed.

**Common cause:** HTTP 404 from Telegram API = invalid/revoked bot token or wrong token in droplet .env.

**Droplet TELEGRAM_NOTIFICATION_LOG.md (tail):**
```
2026-03-16 03:06:02 UTC — tier1 — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:03 UTC — tier2 — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:03 UTC — tier3 — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:04 UTC — convergence — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:04 UTC — promotion_gate — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:44 UTC — tier1 — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:44 UTC — tier2 — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:45 UTC — tier3 — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:45 UTC — convergence — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:46 UTC — promotion_gate — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:46 UTC — heartbeat — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:06:47 UTC — e2e_audit — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:08:04 UTC — tier1 — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:08:04 UTC — tier2 — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:08:05 UTC — tier3 — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:08:05 UTC — convergence — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:08:06 UTC — promotion_gate — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:08:06 UTC — heartbeat — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}
2026-03-16 03:08:06 UTC — e2e_audit — HTTP 404 {"ok":false,"error_code":404,"description":"Not Found"}

```

**Where Telegram lives on droplet (MEMORY_BANK / ARCHITECTURE_AND_OPERATIONS):** (1) `/root/stock-bot/.env` (systemd), (2) `/root/.alpaca_env` (cron/manual), (3) venv `activate`. The E2E runner now sources `.alpaca_env` and `venv/bin/activate` before running so Python sees TELEGRAM_* and runs `sync_telegram_to_dotenv.py` to write them into `.env`.

**Action:** Ensure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set in `/root/.alpaca_env` or in the venv environment on the droplet, then re-run E2E. Or run on droplet with env loaded: `source /root/.alpaca_env 2>/dev/null; source venv/bin/activate && python3 -c "from scripts.alpaca_telegram import send_governance_telegram; send_governance_telegram('E2E test', script_name='e2e')"`
