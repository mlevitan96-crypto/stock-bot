# Alpaca Trade-Count Semantics Correction — Intent (CSA)

**UTC:** 2026-03-20

---

## Governance declaration

**CSA intent:** Trade-count milestones must reflect exits occurring under promoted logic, not entries.

**Rationale:**
- **Entry-time filtering is insufficient** in live systems with overlapping positions
- A trade that entered before promotion but exited after promotion was affected by the promoted exit logic
- For diagnostic evaluation, we care about exits that occurred under the new logic, not entries
- **Exit-time semantics are canonical** for diagnostic evaluation

---

## Current behavior (to be corrected)

**Previous logic (if any):** Filter by `entry_ts >= activated_utc`

**Problem:**
- Trades that entered before promotion but exited after promotion would be excluded
- This undercounts the actual impact of the promoted exit logic
- Historical overlap creates ambiguity about which trades were affected

---

## Corrected behavior

**New logic:** Filter by `exit_ts >= activated_utc`

**Benefits:**
- Counts all trades that exited under the promoted logic
- Accurately reflects diagnostic promotion impact
- Eliminates ambiguity from overlapping positions

---

## Requirements

1. **exit_ts is required** — trades without exit_ts are ignored
2. **exit_ts is validated** — malformed timestamps are skipped
3. **Canonical uniqueness preserved** — deduplication still uses `live:SYMBOL:entry_ts` for uniqueness, but filtering uses `exit_ts`

---

*CSA — exit-time semantics declared canonical for diagnostic trade counting.*
