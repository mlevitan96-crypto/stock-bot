# PnL audit — required fields (canonical)

This document defines the **minimum field set** for a massive Alpaca PnL audit. Names follow **repo telemetry** (some differ from informal labels, e.g. `entry_reason` → `final_decision_primary_reason` / `blocked_reason`).

**Governance:** `docs/pnl_audit/LINEAGE_MATRIX.json` is the machine contract; each field maps to emitter, persistence, and join keys.

---

## A) Decision / intent (pre-trade)

| Field | Description |
|-------|-------------|
| `score` / `entry_score` | Composite / v2 score at decision (intent uses `score`; attribution uses `entry_score`). |
| `entry_reason` (logical) | Human-auditable “why”: `final_decision_primary_reason` when intelligence trace present; else `blocked_reason` / `gate_summary` / thesis tags. |
| `market_regime` / `regime` | Regime at entry (`mixed`, `panic`, etc.). |
| `variant_id` | Strategy variant when applicable (often on exit row; entry may use `strategy_id`). |
| `attribution_components` / signal summary | Per-signal contributions or `intelligence_trace` / `active_signal_names`. |
| `decision_event_id`, `canonical_trade_id`, `trade_key` | Stable decision and trade identity for joins. |
| `ts` (UTC) | Row timestamp on JSONL records (`jsonl_write` prepends `ts`). |
| `feature_snapshot`, `thesis_tags` | Structured pre-trade context on `trade_intent` (built via `build_shared_feature_snapshot` / `derive_thesis_tags` from `telemetry/*` when present on disk; lineage matrix emitter row: `main.py:_emit_trade_intent`). |

## B) Order lifecycle

| Field | Description |
|-------|-------------|
| `order_id` (broker) | Alpaca order UUID (authoritative join key). |
| `client_order_id` | Idempotency / trace (when set). |
| `status` | `accepted`, `filled`, `canceled`, etc. (broker + local mirror). |
| `created_at`, `submitted_at`, `filled_at` | Broker timestamps (REST). |
| `symbol`, `side`, `qty` | Order identity. |

## C) Fills / executions

| Field | Description |
|-------|-------------|
| `filled_avg_price`, `filled_qty` | Execution truth (broker; mirrored in `orders.jsonl` when logged). |
| `order_id` | Parent order for the fill. |
| Activity `FILL` | Optional broker activities row (`transaction_time`, `order_id`, `net_amount`). |

## D) Fees

| Field | Description |
|-------|-------------|
| `commission` / `fees` / `net_amount` | Broker REST or FILL activities when present. |
| **Paper contract** | Deterministic **$0** regulatory fees for Alpaca paper; gross ≈ net unless enriched. |

## E) Position / PnL

| Field | Description |
|-------|-------------|
| `avg_entry_price`, `qty`, `market_value`, `unrealized_pl` | Broker position snapshot (REST / `logs/positions.jsonl` when logged). |
| `pnl`, `pnl_pct`, `entry_price`, `exit_price` | Realized trade economics on `exit_attribution`. |
| `entry_order_id`, `exit_order_id` | Join hooks on exit rows (when populated). |

## F) Join keys

| Key | Role |
|-----|------|
| `order_id` (broker) | Primary **order ↔ fill ↔ activities** join. |
| `canonical_trade_id` / `trade_key` | **Intent ↔ metadata ↔ exit** (symbol-time trade identity). |
| `symbol` + time proximity | Fallback when ids missing in local logs (documented fragility). |

## G) Time / session

| Field | Description |
|-------|-------------|
| ISO `ts` UTC | JSONL rows. |
| `api.get_clock()` | Session open/close (broker). |
| ET display | Derived for reporting (`TZ=America/New_York`). |

---

## References

- Emitters: `main.py` (`_emit_trade_intent`, `log_order`, `log_attribution`, `AlpacaExecutor.submit_entry`).
- Paths: `config.registry.LogFiles`, `StateFiles`.
- Exit schema: `src/exit/exit_attribution.py` (`build_exit_attribution_record`, `append_exit_attribution`).
