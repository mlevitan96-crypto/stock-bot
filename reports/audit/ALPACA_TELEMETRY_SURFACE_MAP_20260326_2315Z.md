# Alpaca telemetry surface map

**TS:** `20260326_2315Z`

## Files / streams (primary)

| Path | Role | Primary keys / fields |
|------|------|------------------------|
| `logs/run.jsonl` | Decisions, intents, canonical resolution | `event_type`, `trade_intent` + `canonical_trade_id`, `trade_key`; `canonical_trade_id_resolved` (`canonical_trade_id_intent` / `canonical_trade_id_fill`); `exit_intent` |
| `logs/orders.jsonl` | Execution leg | `canonical_trade_id`, order ids as emitted |
| `logs/exit_attribution.jsonl` | Economic close / PnL | `trade_id` (`open_<SYM>_<ISO>`), `symbol`, `timestamp`, `pnl`, `exit_price`, side |
| `logs/alpaca_unified_events.jsonl` | Unified entry/exit terminal events | `event_type` `alpaca_entry_attribution` / `alpaca_exit_attribution`, `trade_key`, `canonical_trade_id`, `trade_id`, `terminal_close` on exits |
| `logs/alpaca_entry_attribution.jsonl` | Sidecar (if used) | Attribution rows (emitter-dependent) |
| `logs/alpaca_exit_attribution.jsonl` | Sidecar (if used) | Exit attribution mirror |
| `logs/alpaca_emit_failures.jsonl` | Emitter failures | Fail-closed audit trail |

## Code references

- Strict evaluator: `telemetry/alpaca_strict_completeness_gate.py` → `evaluate_completeness`
- Trade key helpers: `src/telemetry/alpaca_trade_key.py`
- Dashboard strict snapshot: `dashboard.py` (`evaluate_completeness`, `STRICT_EPOCH_START`)

## Timestamp / cohort assumptions

- **Exit window floor:** `--open-ts-epoch` (UTC) filters **exit** rows in `exit_attribution.jsonl`.
- **Entry-era floor:** Same epoch also excludes closes whose **position open** time parsed from `trade_id` is **before** the floor (`strict_cohort_entry_era_floor_applied`).
- **Forward split:** Optional `--forward-since-epoch` partitions closed trades by open time vs legacy.

## Strict gate definition (summary)

A closed trade in cohort is **complete** only if: resolvable `trade_key`, unified exit with `terminal_close`, unified entry present, orders with canonical id, exit_intent, entered trade_intent joinable via alias closure, valid `trade_id` schema, positive exit price, `pnl` present, sane timestamps.
