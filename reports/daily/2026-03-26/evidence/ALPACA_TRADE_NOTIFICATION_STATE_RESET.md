# Alpaca Trade Notification State — Reset (SRE)

**Droplet:** `/root/stock-bot`  
**UTC:** 2026-03-20  
**File:** `state/alpaca_trade_notifications.json`

---

## Reset rationale

**Reason:** Semantic correction from entry-time to exit-time filtering requires state reset to ensure future notifications reflect only post-fix exits.

**Impact:** Historical notification flags cleared; next notifications will fire based on corrected exit-time semantics.

---

## Reset state

```json
{
  "promotion_tag": "PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS",
  "activated_utc": "2026-03-20T00:22:37Z",
  "notified_100": false,
  "notified_500": false,
  "last_count": 0,
  "last_count_utc": null
}
```

**Source:** `state/alpaca_diagnostic_promotion.json` (promotion_tag and activated_utc preserved).

---

## Verification

| Field | Value | Status |
|-------|-------|--------|
| **promotion_tag** | `PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS` | **Preserved** |
| **activated_utc** | `2026-03-20T00:22:37Z` | **Preserved** |
| **notified_100** | `false` | **Reset** |
| **notified_500** | `false` | **Reset** |
| **last_count** | `0` | **Reset** |
| **last_count_utc** | `null` | **Reset** |

---

## Future behavior

- **Next 100-trade notification:** Will fire when 100 exits occur with `exit_ts >= 2026-03-20T00:22:37Z` (corrected semantics)
- **Next 500-trade notification:** Will fire when 500 exits occur with `exit_ts >= 2026-03-20T00:22:37Z` (corrected semantics)
- **No historical overlap:** Previous notifications (if any) are cleared; fresh count begins

---

*SRE — state reset complete; future notifications will use exit-time semantics.*
