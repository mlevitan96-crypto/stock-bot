# ALPACA_TRUTH_WAREHOUSE_SCHEMA_20260413_1502

## execution_truth
- `orders`: normalized order/fill events (sources: logs/orders.jsonl, optional Alpaca REST).
- `fills`: subset with fill price / fill semantics.
- `fees`: rows with broker-reported commission/fee only (never inferred).
- `positions`: logs/positions.jsonl samples in window.
- `execution_joined`: fill rows keyed by order_id with sibling count.

## market_context
- Reference price rule: `signal_context.jsonl` nearest row within 300s; fields mid/last/quote.mid.
- Bars: `data/bars_cache/<SYM>/<date>_1Min.json` when present (not joined in this mission unless --max-compute).

## corporate_actions
- API status: `NO_API_KEYS`; announcements fetched: 0

## decision_ledger
- Executed: exit_attribution rows; blocked: blocked_trades + gate failures in score_snapshot + blocked intents.

