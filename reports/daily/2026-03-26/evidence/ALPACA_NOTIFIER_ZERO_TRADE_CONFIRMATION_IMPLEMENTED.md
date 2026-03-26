# Alpaca Notifier Zero-Trade Confirmation — Implemented (SRE)

**UTC:** 2026-03-20  
**File:** `scripts/notify_alpaca_trade_milestones.py`

---

## Implementation

### State schema extension

**New field:** `baseline_confirmed`

**Type:** `boolean`

**Default:** `false`

**Purpose:** Tracks whether 0-trade baseline has been confirmed via governance-grade Telegram message.

---

## Baseline confirmation logic

**Trigger conditions:**
1. `counting_started_utc` is set and stable (watermark initialized)
2. `baseline_confirmed == false` (not yet confirmed)
3. `last_count == 0` (actual count is zero)

**Action:**
1. Send governance-grade Telegram message:
   ```
   Alpaca diagnostic promotion baseline confirmed.
   0 exits counted since notifier arming.
   CSA + SRE verification in progress.
   ```
2. Set `baseline_confirmed = true`
3. Update `last_count = 0` and `last_count_utc = now`
4. Persist state atomically
5. Exit immediately (two-phase execution guard)

---

## Code implementation

```python
# Phase 1: 0-trade baseline confirmation
baseline_confirmed = state.get("baseline_confirmed", False)
if not baseline_confirmed:
    # Count trades to check baseline
    if args.mock_count is not None:
        count = args.mock_count
    else:
        count = _count_trades_since(counting_started_utc)
    
    if count == 0:
        # Send baseline confirmation message
        msg = (
            "Alpaca diagnostic promotion baseline confirmed.\n"
            "0 exits counted since notifier arming.\n"
            "CSA + SRE verification in progress."
        )
        if _send_telegram(msg):
            state["baseline_confirmed"] = True
            state["last_count"] = 0
            state["last_count_utc"] = datetime.now(timezone.utc).isoformat()
            state_mutated_this_run = True
            _atomic_write_state(NOTIFICATION_STATE, state)
            print("Sent 0-trade baseline confirmation")
            print("Exiting without threshold evaluation (baseline confirmation)")
            return 0
```

---

## Guarantees

| Requirement | Implementation |
|-------------|----------------|
| **Governance-grade message** | ✓ Explicit baseline confirmation text |
| **0-trade verification** | ✓ Actual count checked before sending |
| **One-time only** | ✓ `baseline_confirmed` flag prevents duplicates |
| **Two-phase guard** | ✓ Exits immediately after confirmation (no threshold evaluation) |

---

## Message semantics

**Message text:**
> Alpaca diagnostic promotion baseline confirmed.  
> 0 exits counted since notifier arming.  
> CSA + SRE verification in progress.

**Purpose:**
- Confirms 0-trade starting point
- Signals governance verification required
- Provides audit trail for baseline establishment

---

## Execution flow

1. Script executes
2. Watermark present (`counting_started_utc` set)
3. `baseline_confirmed == false`
4. Count trades: `count = 0`
5. Send baseline confirmation Telegram
6. Set `baseline_confirmed = true`
7. Set `state_mutated_this_run = true`
8. Persist state
9. Exit immediately (no threshold evaluation)

**Next run:**
- `baseline_confirmed == true`
- Skips baseline confirmation
- Proceeds to threshold evaluation (if no other mutations)

---

*SRE — 0-trade baseline confirmation implemented; governance-grade message sent once.*
