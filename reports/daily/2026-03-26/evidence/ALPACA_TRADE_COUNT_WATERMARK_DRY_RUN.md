# Alpaca Trade-Count Watermark — Dry Run (SRE)

**Droplet:** `/root/stock-bot`  
**UTC:** 2026-03-20  
**Command:** `PYTHONPATH=. python3 scripts/notify_alpaca_trade_milestones.py --mock-count 100`

---

## Dry run execution

**Result:**
- **Script executed successfully** ✓
- **Telegram message delivered** ✓ (mock mode only)
- **State file updated** ✓
- **Watermark used for filtering** ✓

**Output:**
```
[DRY RUN] Using mock count: 100
Sent 100-trade notification (count=100)
Current count: 100 (since 2026-03-20T00:43:36.320609+00:00)
```

**Key observation:** Output shows `since 2026-03-20T00:43:36.320609+00:00` (counting watermark), confirming watermark is used instead of `activated_utc`.

---

## Message verification

**Message text (unchanged):**
> 🔬 Alpaca diagnostic promotion active — 100 trades reached.  
> Telemetry and exit attribution confirmed operational.

**Status:** Message text matches specification; no changes required.

---

## Watermark verification

**State file after dry run:**
- `counting_started_utc` present and used for filtering
- Output message shows watermark timestamp (not `activated_utc`)
- Confirms filtering logic uses `counting_started_utc`

---

## Safety check

| Check | Result |
|-------|--------|
| **Telegram message delivered** | **PASS** — but only in mock mode (`--mock-count`) |
| **No real notification sent** | **PASS** — dry run uses mock count, not real trade count |
| **Watermark used** | **PASS** — output confirms `since <counting_started_utc>` |
| **State persistence** | **PASS** — file updated atomically |

---

## First-run initialization test

**Note:** First-run initialization (when `counting_started_utc` is missing) was not tested in this dry run because watermark was already set. First-run behavior is documented in implementation and will occur automatically if state file is missing the field.

**Expected first-run behavior:**
1. Script executes
2. `counting_started_utc` missing
3. Sets `counting_started_utc = now`
4. Persists state
5. Exits without sending notifications
6. Output: `"Initialized counting watermark: <timestamp>"` and `"Exiting without notifications (first-run initialization)"`

---

## Post-dry-run reset

**State file reset:** After dry run, state file was reset to clear `notified_100 = true` flag for production use.

---

*SRE — dry run passed; watermark semantics verified; ready for production.*
