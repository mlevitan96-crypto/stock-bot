# Alpaca Telegram Notifier — Implemented (SRE)

**Script:** `scripts/notify_alpaca_trade_milestones.py`

---

## Logic flow

1. **Load promotion state** from `state/alpaca_diagnostic_promotion.json` → get `activated_utc`.
2. **Load notification state** from `state/alpaca_trade_notifications.json` (or initialize if missing).
3. **Count closed trades** from `logs/exit_attribution.jsonl`:
   - Filter: `exit_ts` ≥ `activated_utc`
   - Deduplicate: unique canonical keys `live:SYMBOL:entry_ts` (second-precision)
4. **Check thresholds:**
   - If `count ≥ 100` AND `notified_100 == false`:
     - Send: *"Alpaca diagnostic promotion active — 100 trades reached. Telemetry and exit attribution confirmed operational."*
     - Set `notified_100 = true`
   - If `count ≥ 500` AND `notified_500 == false`:
     - Send: *"Alpaca diagnostic promotion review window complete — 500 trades reached. Ready for Quant + CSA evaluation."*
     - Set `notified_500 = true`
5. **Update state** atomically (temp file + `os.replace()`).

---

## Guarantees

| Property | Implementation |
|----------|----------------|
| **Each message fires once** | `notified_*` flags prevent re-send even if script runs multiple times |
| **Safe to run repeatedly** | Idempotent: re-counting same data yields same count; flags block duplicates |
| **Atomic state writes** | `os.replace()` on POSIX; temp file pattern |

---

## Dependencies

- **Telegram:** `scripts/alpaca_telegram.send_governance_telegram()` (handles failures gracefully; logs to `TELEGRAM_NOTIFICATION_LOG.md`).
- **Env vars:** `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (from Alpaca venv / `.alpaca_env`).
- **Files:** `state/alpaca_diagnostic_promotion.json`, `logs/exit_attribution.jsonl`.

---

## Error handling

- Missing promotion state → exit 1.
- Missing exit_attribution → count = 0 (no crash).
- Telegram send failure → logged; script continues; flag **not** set (retry on next run).
- JSON parse errors → skip malformed lines; continue.

---

*SRE — notifier implemented; ready for scheduling.*
