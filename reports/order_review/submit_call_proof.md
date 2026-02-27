# Submit call proof (Order Truth Contract)

Generated: 2026-02-20 18:54 UTC
Window: last 24h (since ts 1771527295)

## Counts

- **SUBMIT_ORDER_CALLED** (lines in `logs/submit_order_called.jsonl` in window): **0**
- **submit_entry.jsonl** lines in window: **0**
- **Broker responses** (from `logs/orders.jsonl`): success (filled)=**0**, fail/error/reject=**0**

## Interpretation

- If SUBMIT_ORDER_CALLED = 0 and orders.jsonl has lines: those lines are from other sources (e.g. audit_dry_run, log_order from elsewhere), not from the broker submit path.
- If SUBMIT_ORDER_CALLED > 0 and order_success = 0: submit is called but broker never fills (or telemetry for fills is missing).
- If SUBMIT_ORDER_CALLED = 0: submit is never reached; see submit_call_map.md for guards that block before submit.
