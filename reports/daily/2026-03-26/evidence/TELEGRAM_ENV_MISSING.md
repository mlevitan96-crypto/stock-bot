# Telegram environment missing — E2E audit blocked

**Step 0 failed.** TELEGRAM_BOT_TOKEN and/or TELEGRAM_CHAT_ID were not set at runtime.

- Token present: NO
- Chat ID present: NO

Set both in your environment (or in `.env` and ensure it is loaded before running governance scripts), then re-run:
  `python scripts/verify_telegram_env.py`

Once both show YES, proceed with the Alpaca E2E governance audit (Steps 1–6).
