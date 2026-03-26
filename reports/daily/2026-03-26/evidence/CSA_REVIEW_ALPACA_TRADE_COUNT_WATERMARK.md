# CSA Review — Alpaca Trade-Count Watermark

**UTC:** 2026-03-20

---

## Review inputs

- [ALPACA_TRADE_COUNT_WATERMARK_INTENT.md](./ALPACA_TRADE_COUNT_WATERMARK_INTENT.md)
- [ALPACA_TRADE_COUNT_WATERMARK_SCHEMA.md](./ALPACA_TRADE_COUNT_WATERMARK_SCHEMA.md)
- [ALPACA_TRADE_COUNT_WATERMARK_IMPLEMENTED.md](./ALPACA_TRADE_COUNT_WATERMARK_IMPLEMENTED.md)
- [ALPACA_TRADE_COUNT_WATERMARK_STATE_RESET.md](./ALPACA_TRADE_COUNT_WATERMARK_STATE_RESET.md)
- [ALPACA_TRADE_COUNT_WATERMARK_DRY_RUN.md](./ALPACA_TRADE_COUNT_WATERMARK_DRY_RUN.md)
- [ALPACA_TRADE_COUNT_WATERMARK_CRON_CONFIRMED.md](./ALPACA_TRADE_COUNT_WATERMARK_CRON_CONFIRMED.md)

---

## Watermark semantics

| Component | Status |
|-----------|--------|
| **counting_started_utc field** | **Implemented** — immutable watermark in state schema |
| **First-run initialization** | **Implemented** — sets watermark and exits without notifications |
| **Filtering uses watermark** | **Implemented** — `exit_ts >= counting_started_utc` (not `activated_utc`) |
| **Immutable watermark** | **Implemented** — set once, never changes |

---

## State reset

| Field | Status |
|-------|--------|
| **counting_started_utc set** | **PASS** — `2026-03-20T00:43:36.320609+00:00` |
| **Historical notifications cleared** | **PASS** — `notified_100 = false`, `notified_500 = false` |
| **Count reset** | **PASS** — `last_count = 0` |
| **Promotion metadata preserved** | **PASS** — `promotion_tag` and `activated_utc` unchanged |

---

## Dry-run proof

| Check | Result |
|-------|--------|
| **Script executes** | **PASS** — no errors |
| **Telegram delivery (mock)** | **PASS** — message sent in mock mode |
| **Watermark used** | **PASS** — output shows `since <counting_started_utc>` |
| **State persistence** | **PASS** — file updated correctly |

---

## Cron continuity

| Check | Result |
|-------|--------|
| **Cron installed** | **PASS** — entry present |
| **No duplicates** | **PASS** — single entry |
| **Script path unchanged** | **PASS** — no cron modifications needed |

---

## CSA declaration

| Field | Value |
|-------|--------|
| **ALPACA_TRADE_COUNT_NOTIFIER_SEALED** | **YES** |

**Rationale:**
- Counting watermark implemented and immutable
- First-run initialization prevents historical re-counting
- State reset ensures clean counting start
- Dry-run confirms functional correctness
- Cron continuity maintained (no disruption)

---

## Sealed behavior

**Next notifications will:**
- Count trades with `exit_ts >= counting_started_utc` (watermark filtering)
- Fire at 100 and 500 exit thresholds (once each)
- Reflect only NEW exits after notifier arming (no historical overlap)

**Historical exclusion:**
- All exits before `counting_started_utc` are permanently excluded
- Watermark is immutable (never changes after initialization)
- Future milestones accurately reflect only post-arming exits

**First-run safety:**
- If watermark missing, script initializes it and exits silently
- No notifications sent during first-run initialization
- Subsequent runs count only NEW exits after watermark

---

*CSA — trade-count notifier sealed; counting watermark prevents historical re-counting; hands-off operation resumes.*
