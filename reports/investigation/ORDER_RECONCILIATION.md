# Order reconciliation (Phase 4)

Window: last 7 days (same bot instance / account).

## Counts (same window)

| Metric | Source | Count |
|--------|--------|-------|
| SUBMIT_ORDER_CALLED | logs/submit_order_called.jsonl | 0 |
| submit_entry log lines | logs/submit_entry.jsonl | 0 |
| Fills (broker) | logs/orders.jsonl (action/status filled) | 0 |
| Rejected/error | logs/orders.jsonl | 0 |
| Other orders | logs/orders.jsonl | 0 |

## Proof (entry path)

- **Submit decisions → submit calls:** submit_entry (and thus SUBMIT_ORDER_CALLED) is only invoked after the expectancy gate passes (decision to trade). So every submit call has a preceding decision.
- **Submit calls → broker responses:** Each SUBMIT_ORDER_CALLED line corresponds to an order sent to the broker; broker responses (filled, rejected, etc.) are logged to logs/orders.jsonl.
- **No fills without submit:** In this window, SUBMIT_ORDER_CALLED = 0. Fills = 0. So no fills in window without a submit in window (or fills are from prior/other source).
- **No submit without decision:** Submits only occur after gate pass; no submit without a prior pass decision.

## Verdict

**Entry reconciliation:** CLEAN

Zero submits, zero fills. No fills without submit; no submit without decision (submit only after gate pass).

## DROPLET COMMANDS

```bash
cd /root/stock-bot
python3 scripts/order_reconciliation_on_droplet.py
```
