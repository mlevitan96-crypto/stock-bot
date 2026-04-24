# ALPACA PnL AUDIT — Required fields contract

This contract maps **minimum audit-usable fields** to **emitters** and **persisted locations**.

## A) Order lifecycle row (`logs/orders.jsonl`)

| Field | Emitter | Persistence |
|-------|---------|-------------|
| `ts` | `main.jsonl_write` / `log_order` wrapper | prepended on write (`main.py`, `jsonl_write`) |
| `type` | `log_order` | `"order"` |
| `action` / `status` | `AlpacaExecutor` paths (`submit_*`, `log_order` on fill) | `main.py` (~4960–5340, ~10652–10663) |
| `symbol`, `side`, `qty` | `log_order` | same |
| `order_id` | order submission paths; merged via `telemetry.attribution_emit_keys.merge_attribution_keys_into_record` | `main.py` `log_order` |
| `price` / fill price | fill logging | `main.py` |
| `entry_score`, `market_regime` | `submit_entry` audit dry-run branch; merged keys | `main.py` `submit_entry`, `log_order` |

## B) Fill / execution row

| Field | Emitter | Persistence |
|-------|---------|-------------|
| Broker `id`, `filled_avg_price`, `filled_qty`, `status` | Alpaca REST (read path in audits) | Broker API + optional mirror in `orders.jsonl` |
| `commission` / fees | Alpaca order object or `FILL` activities | Broker REST; see Phase 4 gate |

Local **`orders.jsonl`** rows with `status: filled` or `action` containing `filled` carry execution truth for joins (`main.py`).

## C) Position snapshot row (`logs/positions.jsonl` / broker)

| Field | Emitter | Persistence |
|-------|---------|-------------|
| Symbol, qty, side, entry | position logging cycle | `config.registry.LogFiles.POSITIONS` |
| `entry_score` / metadata | `state/position_metadata.json` via registry | `StateFiles.POSITION_METADATA` |

## D) Attribution / decision row

| Field | Emitter | Persistence |
|-------|---------|-------------|
| Entry context: `entry_score`, `regime`, `components`, `attribution_components` | `log_attribution` / entry path | `logs/attribution.jsonl` |
| Exit PnL row: `symbol`, `pnl`, `entry_order_id`, `exit_order_id`, `order_id`, `trade_id` | `src/exit/exit_attribution.py` `append_exit_attribution` | `logs/exit_attribution.jsonl` |
| Pre-trade intent: `feature_snapshot`, `thesis_tags`, `score`, `canonical_trade_id`, `final_decision_primary_reason` | `main._emit_trade_intent` | `logs/run.jsonl` (`event_type: trade_intent`) |

**Note:** There is no literal DB table in-repo; audit spine is **JSONL + state JSON** under `logs/` and `state/`.

## Era-cut / post-era

Forward trades use the same paths; era metadata may be enforced by `utils/era_cut.py` in consumers (dashboard/learning) — not duplicated here.
