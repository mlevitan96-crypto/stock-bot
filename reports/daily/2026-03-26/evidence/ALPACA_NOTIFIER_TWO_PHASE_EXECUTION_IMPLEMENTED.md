# Alpaca Notifier Two-Phase Execution — Implemented (SRE)

**UTC:** 2026-03-20  
**File:** `scripts/notify_alpaca_trade_milestones.py`

---

## Implementation

### Two-phase execution invariant

**Rule:** If state is mutated in this run, exit immediately without evaluating thresholds.

**State mutations that trigger guard:**
1. Watermark initialization (`counting_started_utc` set)
2. Baseline confirmation (`baseline_confirmed` set)
3. Any other state field mutation

---

## Code implementation

**Guard flag:**
```python
state_mutated_this_run = False
```

**Phase 1: State mutations**
```python
# Watermark initialization
if not counting_started_utc:
    state["counting_started_utc"] = now_utc
    state_mutated_this_run = True
    _atomic_write_state(NOTIFICATION_STATE, state)
    return 0  # Exit immediately

# Baseline confirmation
if not baseline_confirmed and count == 0:
    state["baseline_confirmed"] = True
    state_mutated_this_run = True
    _atomic_write_state(NOTIFICATION_STATE, state)
    return 0  # Exit immediately
```

**Phase 2: Threshold evaluation (only if no mutation)**
```python
# Two-phase execution guard
if state_mutated_this_run:
    print("State mutated this run; exiting without threshold evaluation")
    return 0

# Only evaluate thresholds if state was NOT mutated
if count >= 100 and not state.get("notified_100", False):
    # Send notification...
```

---

## Guarantees

| Requirement | Implementation |
|-------------|----------------|
| **No notifications on state mutation** | ✓ Hard exit if `state_mutated_this_run = True` |
| **Explicit guard flag** | ✓ `state_mutated_this_run` tracks mutations |
| **Immediate exit** | ✓ `return 0` after state mutation |
| **No threshold evaluation** | ✓ Guard prevents milestone checks |

---

## Execution flow

**Scenario 1: First run (watermark init)**
1. Script executes
2. `counting_started_utc` missing
3. Sets watermark, `state_mutated_this_run = True`
4. Persists state
5. Exits immediately (no notifications)

**Scenario 2: Baseline confirmation**
1. Script executes
2. `baseline_confirmed = False`, `count = 0`
3. Sends baseline message, sets `baseline_confirmed = True`, `state_mutated_this_run = True`
4. Persists state
5. Exits immediately (no threshold evaluation)

**Scenario 3: Normal run (no mutation)**
1. Script executes
2. Watermark present, baseline confirmed
3. `state_mutated_this_run = False`
4. Counts trades
5. Evaluates thresholds
6. Sends notifications if thresholds reached

---

*SRE — two-phase execution enforced; state mutations never trigger notifications in same run.*
