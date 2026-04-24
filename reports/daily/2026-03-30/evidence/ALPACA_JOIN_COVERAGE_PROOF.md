# ALPACA JOIN COVERAGE PROOF

- Sample window: last **20** qualifying rows per stream (tail scan).

## Canonical join keys

- **Primary:** Alpaca `order_id` (also duplicated as `order_id` on `exit_attribution` rows when present).
- **Secondary:** `canonical_trade_id` / `trade_key` on `trade_intent` (`main._emit_trade_intent`).
- **Fallback:** `symbol` + time proximity (used in truth missions; not recomputed in depth here).

## Local `orders.jsonl` (fill-shaped rows)

- Fills sampled: **20**
- Fills with non-empty `order_id`: **0** (0.0%)
- Fills with `order_id` matching any `exit_attribution` key: **0** (0.0%)
- Fills whose `symbol` appears in recent `positions.jsonl` tail: **0** (0.0%)
- `trade_intent` sampled: **3** with `feature_snapshot`+`score`: **3** (100.0%)

## Broker REST (authoritative order id for PnL audit)

- broker REST order sample n=20 with id=20

> Massive PnL audit missions join **broker REST** `list_orders` / activities to local JSONL; local fill rows may omit `order_id` while still audit-usable via broker id + symbol/ts.

