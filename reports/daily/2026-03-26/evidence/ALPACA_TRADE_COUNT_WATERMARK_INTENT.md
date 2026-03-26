# Alpaca Trade-Count Watermark — Intent (CSA)

**UTC:** 2026-03-20

---

## Governance declaration

**CSA intent:** Trade-count milestones must be based on exits occurring AFTER notifier arming, not promotion activation.

**Rationale:**
- **Promotion activation time and notification counting start time are distinct**
- Historical exits that occurred before the notifier was armed should never be counted
- Prevents duplicate milestone alerts from historical re-counting
- Ensures milestones reflect only NEW exits after notifier initialization

---

## Problem statement

**Current behavior:**
- Notifier counts exits since `activated_utc` (promotion activation)
- If notifier is deployed/armed after promotion activation, it may count historical exits
- This can cause immediate milestone notifications for trades that occurred before notifier was ready

**Example scenario:**
1. Promotion activated: `2026-03-20T00:22:37Z`
2. 150 exits occur between activation and notifier deployment
3. Notifier deployed: `2026-03-20T01:00:00Z`
4. Notifier immediately fires 100-trade notification (counting historical exits)
5. **Problem:** Notification reflects historical data, not new exits

---

## Solution: Counting watermark

**New behavior:**
- Notifier maintains `counting_started_utc` (immutable watermark)
- Only counts exits where `exit_ts >= counting_started_utc`
- On first run, sets `counting_started_utc = now` and exits without sending notifications
- Subsequent runs count only NEW exits after watermark

**Benefits:**
- Prevents historical re-counting
- Ensures milestones reflect only exits after notifier arming
- Immutable watermark prevents accidental reset
- Clear separation between promotion activation and counting start

---

## Requirements

1. **counting_started_utc is immutable** — once set, never changes
2. **First-run initialization** — if missing, set to current UTC and exit without notifications
3. **Filtering uses watermark** — `exit_ts >= counting_started_utc` (not `activated_utc`)
4. **Preserve idempotency** — `notified_100` / `notified_500` flags still prevent duplicates

---

*CSA — counting watermark declared required for accurate milestone tracking.*
