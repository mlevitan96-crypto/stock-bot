# Alpaca Trade-Count Watermark — Implemented (SRE)

**UTC:** 2026-03-20  
**File:** `scripts/notify_alpaca_trade_milestones.py`

---

## Implementation changes

### 1. State schema extension

**New field:** `counting_started_utc`

**Initialization logic:**
- If `counting_started_utc` is missing on startup:
  - Set `counting_started_utc = now` (current UTC)
  - Persist state atomically
  - Exit without sending notifications (first-run initialization)

---

### 2. Trade counting logic update

**Function:** `_count_trades_since()`

**Changed parameter:** `activated_utc` → `counting_started_utc`

**Filtering:**
- **Before:** `exit_ts >= activated_utc` (promotion activation time)
- **After:** `exit_ts >= counting_started_utc` (notifier counting start time)

**Documentation updated:**
- Function docstring clarifies watermark semantics
- Comments explain prevention of historical re-counting

---

### 3. Main function updates

**First-run behavior:**
```python
counting_started_utc = state.get("counting_started_utc")
if not counting_started_utc:
    # First run: set watermark and exit without sending notifications
    now_utc = datetime.now(timezone.utc).isoformat()
    state["counting_started_utc"] = now_utc
    _atomic_write_state(NOTIFICATION_STATE, state)
    print(f"Initialized counting watermark: {now_utc}")
    print("Exiting without notifications (first-run initialization)")
    return 0
```

**Subsequent runs:**
- Use `counting_started_utc` for filtering (not `activated_utc`)
- Count exits where `exit_ts >= counting_started_utc`
- Preserve idempotent notification flags

---

## Guarantees

| Requirement | Implementation |
|-------------|----------------|
| **counting_started_utc is immutable** | ✓ Set once on first run, never changed |
| **First-run initialization** | ✓ If missing, set to now and exit without notifications |
| **Filtering uses watermark** | ✓ `exit_ts >= counting_started_utc` (not `activated_utc`) |
| **Preserve idempotency** | ✓ `notified_100` / `notified_500` flags still prevent duplicates |
| **Canonical uniqueness** | ✓ Still uses `live:SYMBOL:entry_ts` for deduplication |

---

## Behavior changes

**Before:**
- Counted exits since promotion activation (`activated_utc`)
- Could count historical exits if notifier deployed after activation
- Risk of immediate milestone notifications for historical data

**After:**
- Counts exits since notifier arming (`counting_started_utc`)
- First run initializes watermark and exits silently
- Subsequent runs count only NEW exits after watermark
- No historical re-counting possible

---

## Example flow

1. **First run (watermark initialization):**
   - Script executes
   - `counting_started_utc` missing
   - Sets `counting_started_utc = 2026-03-20T01:00:00Z`
   - Persists state
   - Exits without sending notifications

2. **Second run (counting begins):**
   - Script executes
   - `counting_started_utc = 2026-03-20T01:00:00Z` (present)
   - Counts exits where `exit_ts >= 2026-03-20T01:00:00Z`
   - Sends notifications if thresholds reached (only for NEW exits)

---

*SRE — counting watermark implemented; first-run initialization prevents historical re-counting.*
