# Alpaca Trade-Count Watermark — State Reset (SRE)

**Droplet:** `/root/stock-bot`  
**UTC:** 2026-03-20T00:43:36Z  
**File:** `state/alpaca_trade_notifications.json`

---

## Reset rationale

**Reason:** Watermark implementation requires state reset to establish `counting_started_utc` and ensure no historical exits qualify.

**Impact:** Fresh counting watermark set; future notifications will fire only for NEW exits after watermark.

---

## Reset state

```json
{
  "promotion_tag": "PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS",
  "activated_utc": "2026-03-20T00:22:37Z",
  "counting_started_utc": "2026-03-20T00:43:36.320609+00:00",
  "notified_100": false,
  "notified_500": false,
  "last_count": 0,
  "last_count_utc": null
}
```

**Source:**
- `promotion_tag` and `activated_utc`: from `state/alpaca_diagnostic_promotion.json`
- `counting_started_utc`: set to current UTC at reset time

---

## Verification

| Field | Value | Status |
|-------|-------|--------|
| **promotion_tag** | `PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS` | **Preserved** |
| **activated_utc** | `2026-03-20T00:22:37Z` | **Preserved** |
| **counting_started_utc** | `2026-03-20T00:43:36.320609+00:00` | **Set** (immutable watermark) |
| **notified_100** | `false` | **Reset** |
| **notified_500** | `false` | **Reset** |
| **last_count** | `0` | **Reset** |
| **last_count_utc** | `null` | **Reset** |

---

## Historical exclusion

**Watermark:** `2026-03-20T00:43:36.320609+00:00`

**Qualifying exits:**
- Only exits where `exit_ts >= 2026-03-20T00:43:36.320609+00:00`

**Excluded exits:**
- All exits before `2026-03-20T00:43:36.320609+00:00` (permanently ignored)
- Historical exits between `activated_utc` (00:22:37Z) and watermark (00:43:36Z) are excluded

---

## Future behavior

- **Next 100-trade notification:** Will fire when 100 NEW exits occur with `exit_ts >= 2026-03-20T00:43:36.320609+00:00`
- **Next 500-trade notification:** Will fire when 500 NEW exits occur with `exit_ts >= 2026-03-20T00:43:36.320609+00:00`
- **No historical overlap:** Previous exits are permanently excluded by watermark

---

*SRE — state reset complete; counting watermark established; future notifications require NEW exits only.*
