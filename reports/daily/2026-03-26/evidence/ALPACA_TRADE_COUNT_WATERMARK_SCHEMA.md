# Alpaca Trade-Count Watermark — Schema Extension (SRE)

**UTC:** 2026-03-20  
**File:** `state/alpaca_trade_notifications.json`

---

## Schema extension

**New field:** `counting_started_utc`

**Type:** `string` (ISO 8601 UTC timestamp)

**Definition:**
- Timestamp when notifier begins counting exits
- Immutable once set (never changes after initialization)
- Used as watermark for filtering: `exit_ts >= counting_started_utc`

---

## Updated schema

```json
{
  "promotion_tag": "PROMOTED_DIAGNOSTIC_ALPACA_SCORE_DETERIORATION_EMPHASIS",
  "activated_utc": "2026-03-20T00:22:37Z",
  "counting_started_utc": "2026-03-20T01:00:00Z",
  "notified_100": false,
  "notified_500": false,
  "last_count": 0,
  "last_count_utc": null
}
```

---

## Field semantics

| Field | Purpose | Mutability |
|-------|---------|------------|
| **promotion_tag** | Promotion identifier | Immutable (set once) |
| **activated_utc** | Promotion activation time | Immutable (from promotion state) |
| **counting_started_utc** | Notifier counting start time | **Immutable** (set on first run, never changes) |
| **notified_100** | 100-trade notification sent | Mutable (set to `true` when sent) |
| **notified_500** | 500-trade notification sent | Mutable (set to `true` when sent) |
| **last_count** | Last counted trade count | Mutable (updated each run) |
| **last_count_utc** | Last count timestamp | Mutable (updated each run) |

---

## Initialization logic

**If `counting_started_utc` is missing:**
1. Set `counting_started_utc = now` (current UTC)
2. Persist state atomically
3. Exit without sending notifications (first-run initialization)

**If `counting_started_utc` is present:**
- Use existing value (immutable)
- Count exits where `exit_ts >= counting_started_utc`

---

## Backward compatibility

**Existing state files without `counting_started_utc`:**
- Will be initialized on first run
- No migration required (automatic initialization)

---

*SRE — schema extended; counting watermark field defined; initialization logic specified.*
