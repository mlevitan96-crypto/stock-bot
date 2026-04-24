# SRE verdict — Telegram + PnL (Phase 6)

## Scheduler reliability

- **`alpaca-postclose-deepdive.timer`:** **enabled** and **active**; last trigger **Fri 2026-03-27 20:30:06 UTC** aligned with **16:30 America/New_York**.
- **Failure mode:** Application **exit 4** — not timer drift.

## Secrets / env / systemd alignment

- **Telegram:** Resolved from **`stock-bot.service` + `.env`**; **`getMe` OK** (bot `Alpacadailybot`).
- **Post-close unit:** Uses `EnvironmentFile=-/root/stock-bot/.env` and `TRADING_BOT_ROOT` — consistent with script expectations.

## Dedupe / idempotency

- **Dedupe:** `_already_sent_live_for_session` in `scripts/alpaca_postclose_deepdive.py` — **not exercised** today (process exited before audit send).
- **Risk:** Stale **`state/postclose_watermark.json`** referencing **`2035-01-02`** creates **operator confusion**; recommend resetting watermark to a real session or documenting test-era state.

## Alerting recommendations

| Signal | Recommendation |
|--------|------------------|
| **`status=4` / Memory Bank** | Page or Telegram to ops channel when post-close exits **4** (text match `Memory Bank`). |
| **`telegram_ok: false`** in audit JSONL | Daily scanner on `reports/alpaca_daily_close_telegram.jsonl`. |
| **Runner not run** | Alert if **no** timer journal entry by **21:00 UTC** on NYSE weekdays. |
| **Gated learning BLOCKED** | Optional informational Telegram (low noise) — product decision; currently embedded in body only when send succeeds. |

## Top 3 risks

1. **Untracked / unversioned MEMORY_BANK** on droplet — markers can disappear without PR review.
2. **Strict incomplete trades** — dashboard learning remains **BLOCKED** until order join chain repaired for MSFT key.
3. **Fee telemetry gap** — economic audits incomplete without fee fields on orders.
