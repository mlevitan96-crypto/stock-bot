# Canonical Trade Event Model

Used by the CSA-every-100-trades trigger to count trade events (executed, blocked, counter-intelligence rejected).

## Event types

| Type | Description | Where recorded |
|------|-------------|----------------|
| **executed** | Filled entry order or closed exit (exit attribution). | Entry: after `submit_entry` returns filled with `filled_qty > 0`. Exit: when `append_exit_attribution(rec)` is called. |
| **blocked** | Candidate was blocked by a gate (score, displacement, max positions, etc.). | When `log_blocked_trade(...)` is called. |
| **counter_intel_rejected** | Reserved for future use (e.g. counter-intelligence layer rejecting a candidate). | Currently counted as **blocked**; same as `log_blocked_trade`. |

## Single recording point

- **Function:** `record_trade_event(event_type, ...)` in `src/infra/csa_trade_state.py`.
- Called from:
  1. End of `log_blocked_trade()` in main.py (one call per blocked trade).
  2. After a filled entry in main.py (one call per filled order).
  3. After `append_exit_attribution(rec)` in main.py (one call per exit).
- Each call increments `total_trade_events` in `reports/state/TRADE_CSA_STATE.json`. Every 100 events, CSA is triggered (primary: from engine; backup: from droplet post-trade hook).

## Tags (optional)

- Shadow/paper/live: not required for counting. Event type and existing logs carry mode; state file does not tag by mode.
