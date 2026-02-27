# Paper trade metric reconciliation

Explicit metrics (no single "Trades (paper)"):

- **candidates_evaluated:** 2922 (ledger events in window)
- **paper_orders_submitted:** 0 (SUBMIT_ORDER_CALLED / submit_entry path; from logs/submit_order_called.jsonl in window)
- **submit_entry log lines:** 334 (logs/submit_entry.jsonl in window)
- **paper_fills:** 5092 (broker fill telemetry from logs/orders.jsonl in window)

Window: last 7 days.

## DROPLET COMMANDS

```bash
cd /root/stock-bot
python3 scripts/full_signal_review_on_droplet.py --days 7
```
