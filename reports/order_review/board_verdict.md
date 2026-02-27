# Board verdict — Order Submission Truth Contract

Generated: 2026-02-20 18:54 UTC

## FINAL VERDICT

Submit never called — all candidates blocked at expectancy_gate (score floor) before reaching submit_entry or before _submit_order_guarded. Exact blocker: expectancy_gate (composite score below MIN_EXEC_SCORE).

## Single fix (restore truthful order submission telemetry)

No order-layer fix; address score/signal so candidates pass expectancy gate, or run with AUDIT_DRY_RUN=1 to confirm submit path without broker call. If instrumentation (main.py SUBMIT_ORDER_CALLED log) was just deployed, restart the bot and run for a few minutes then re-run this script.

## Evidence summary

- SUBMIT_ORDER_CALLED (24h): 0
- submit_entry.jsonl lines (24h): 0
- Broker success (filled): 0, fail: 0
