# Alpaca Telegram Credentials — Verified (SRE)

**Droplet:** `/root/stock-bot`  
**UTC:** 2026-03-20T00:35Z

---

## Verification

| Credential | Status | Source |
|------------|--------|--------|
| **TELEGRAM_BOT_TOKEN** | **SET** | `/root/.alpaca_env` (sourced via `source /root/.alpaca_env`) |
| **TELEGRAM_CHAT_ID** | **SET** | `/root/.alpaca_env` (sourced via `source /root/.alpaca_env`) |

**Verification method:** `scripts/verify_telegram_env_alpaca.py` executed on droplet with Alpaca venv sourced.

---

## Production readiness

- **Credentials available** for `scripts/notify_alpaca_trade_milestones.py`.
- **Dry run succeeded** (mock 100 count → Telegram message sent; state file updated).

---

*SRE — Telegram credentials verified; ready for production cron.*
