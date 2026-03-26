# CSA Review — Alpaca Trade-Count Semantics Correction

**UTC:** 2026-03-20

---

## Review inputs

- [ALPACA_TRADE_COUNT_SEMANTICS_CORRECTION_INTENT.md](./ALPACA_TRADE_COUNT_SEMANTICS_CORRECTION_INTENT.md)
- [ALPACA_TRADE_COUNT_EXIT_SEMANTICS_IMPLEMENTED.md](./ALPACA_TRADE_COUNT_EXIT_SEMANTICS_IMPLEMENTED.md)
- [ALPACA_TRADE_NOTIFICATION_STATE_RESET.md](./ALPACA_TRADE_NOTIFICATION_STATE_RESET.md)
- [ALPACA_TRADE_COUNT_EXIT_SEMANTICS_DRY_RUN.md](./ALPACA_TRADE_COUNT_EXIT_SEMANTICS_DRY_RUN.md)
- [ALPACA_TRADE_COUNT_CRON_CONTINUITY_CONFIRMED.md](./ALPACA_TRADE_COUNT_CRON_CONTINUITY_CONFIRMED.md)

---

## Semantic correction

| Component | Status |
|-----------|--------|
| **Exit-time filtering** | **Implemented** — `exit_ts >= activated_utc` |
| **exit_ts validation** | **Implemented** — required field, malformed timestamps skipped |
| **Documentation** | **Updated** — function docstring and inline comments clarify semantics |
| **Code clarity** | **Improved** — explicit comments explain exit-time vs entry-time rationale |

---

## State reset

| Field | Status |
|-------|--------|
| **Historical notifications cleared** | **PASS** — `notified_100 = false`, `notified_500 = false` |
| **Count reset** | **PASS** — `last_count = 0` |
| **Promotion metadata preserved** | **PASS** — `promotion_tag` and `activated_utc` unchanged |

---

## Dry-run proof

| Check | Result |
|-------|--------|
| **Script executes** | **PASS** — no errors |
| **Telegram delivery** | **PASS** — message sent |
| **State persistence** | **PASS** — file updated correctly |
| **Message text** | **PASS** — unchanged (as expected) |

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
| **ALPACA_TRADE_COUNT_NOTIFICATIONS_CORRECTED** | **YES** |

**Rationale:**
- Exit-time semantics implemented and documented
- State reset ensures no historical overlap
- Dry-run confirms functional correctness
- Cron continuity maintained (no disruption)

---

## Corrected behavior

**Next notifications will:**
- Count trades with `exit_ts >= 2026-03-20T00:22:37Z` (exit-time semantics)
- Fire at 100 and 500 exit thresholds (once each)
- Reflect exits occurring under promoted logic (canonical for diagnostic evaluation)

**No historical overlap:**
- Previous notifications (if any) are cleared
- Fresh count begins with corrected semantics
- Future milestones accurately reflect promoted logic impact

---

*CSA — trade-count notifications corrected; exit-time semantics canonical; hands-off operation resumes.*
