# Alpaca Telegram Notifier — Production Dry Run (SRE)

**Droplet:** `/root/stock-bot`  
**UTC:** 2026-03-20T00:34Z

---

## Dry run execution

**Command:**
```bash
cd /root/stock-bot
source /root/.alpaca_env
PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py --mock-count 100
```

**Result:**
- **Telegram message delivered** ✓
- **State file created:** `state/alpaca_trade_notifications.json`
- **`notified_100 = true`** ✓

**Message received:**
> 🔬 Alpaca diagnostic promotion active — 100 trades reached.  
> Telemetry and exit attribution confirmed operational.

---

## State file after dry run

```json
{
  "promotion_tag": "PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS",
  "activated_utc": "2026-03-20T00:22:37Z",
  "notified_100": true,
  "notified_500": false,
  "last_count_utc": "2026-03-20T00:34:48.350381+00:00",
  "last_count": 100
}
```

---

## Reset for production

**State reset:** `scripts/reset_notification_state.py` executed to restore `notified_100 = false` for real threshold crossing.

**Post-reset state:**
- `notified_100 = false`
- `notified_500 = false`
- `last_count = 0`

---

## Production readiness

- **Telegram delivery confirmed** ✓
- **State persistence confirmed** ✓
- **Idempotency verified** (re-run with same mock count would not send again) ✓

---

*SRE — production dry run passed; ready for cron installation.*
