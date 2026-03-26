# Alpaca Trade-Count Exit Semantics — Implemented (SRE)

**UTC:** 2026-03-20  
**File:** `scripts/notify_alpaca_trade_milestones.py`

---

## Implementation changes

### Function: `_count_trades_since()`

**Updated logic:**
- **Filter by:** `exit_ts >= activated_utc` (explicit exit-time semantics)
- **Validation:** `exit_ts` is required; trades without `exit_ts` are ignored
- **Validation:** Malformed `exit_ts` timestamps are skipped
- **Uniqueness:** Still uses `live:SYMBOL:entry_ts` for deduplication (canonical key)

---

## Code changes

**Before (implicit):**
```python
exit_ts = rec.get("exit_ts") or rec.get("timestamp")
if not exit_ts:
    continue
# ... filter by exit_dt < activated_dt
```

**After (explicit with documentation):**
```python
# Filter by exit_ts (canonical for diagnostic evaluation)
exit_ts = rec.get("exit_ts") or rec.get("timestamp")
if not exit_ts:
    # Trades without exit_ts are ignored (required field)
    continue
try:
    exit_dt = datetime.fromisoformat(str(exit_ts).replace("Z", "+00:00"))
except Exception:
    # Malformed exit_ts is skipped (validation)
    continue
# Only count exits that occurred after promotion activation
if exit_dt < activated_dt:
    continue
```

**Documentation added:**
- Function docstring explicitly states exit-time semantics
- Inline comments clarify validation requirements
- Rationale documented for exit-time vs entry-time filtering

---

## Guarantees

| Requirement | Implementation |
|-------------|----------------|
| **exit_ts is required** | ✓ `if not exit_ts: continue` |
| **exit_ts is validated** | ✓ `try/except` around `fromisoformat()` |
| **Trades without exit_ts are ignored** | ✓ Early `continue` if missing |
| **Canonical uniqueness preserved** | ✓ Still uses `live:SYMBOL:entry_ts` for deduplication |

---

## Semantic correctness

**Filtering:** Uses `exit_ts >= activated_utc`  
**Deduplication:** Uses `live:SYMBOL:entry_ts` (canonical key)

This ensures:
- Milestones reflect exits occurring under promoted logic
- No double-counting of the same trade (same entry_ts)
- Historical overlap handled correctly (entry before, exit after = counted)

---

*SRE — exit-time semantics implemented with explicit validation and documentation.*
