# Order reconciliation (Phase 4)

Window: last 7 days (same bot instance / account).

## Counts (same window)

| Metric | Source | Count |
|--------|--------|-------|
| SUBMIT_ORDER_CALLED | logs/submit_order_called.jsonl | 0 |
| submit_entry log lines | logs/submit_entry.jsonl | 334 |
| Fills (broker) | logs/orders.jsonl (action/status filled) | 5092 |
| Rejected/error | logs/orders.jsonl | 364 |
| Other orders | logs/orders.jsonl | 2274 |

## Reconciliation

- **Submits (code path):** SUBMIT_ORDER_CALLED is the single telemetry for "submit_entry called and order submitted." Count above is for this window.
- **Broker responses:** orders.jsonl holds broker-side events (filled, rejected, etc.). Fills may be from earlier runs or different time window if ledger and orders use different clocks.
- **Why fills ≠ submits:** If fills (6382) >> submit_called (0), fills are from a different window or historical; for the current run with expectancy gate blocking all, submit_called should be 0 and fills in window may still be non-zero from prior runs.

## DROPLET COMMANDS

```bash
cd /root/stock-bot
python3 scripts/order_reconciliation_on_droplet.py
```