# Strict learning chain — code pointers

Strict gate reads (via `telemetry/alpaca_strict_completeness_gate._stream_jsonl_primary_then_backfill`): `logs/run.jsonl` + `logs/strict_backfill_run.jsonl`, `logs/orders.jsonl` + `logs/strict_backfill_orders.jsonl`, `logs/alpaca_unified_events.jsonl` + `logs/strict_backfill_alpaca_unified_events.jsonl`, and `logs/exit_attribution.jsonl`.

| Event / concern | Emitter (file:function) | Sink | Preconditions / flags |
|-----------------|---------------------------|------|-------------------------|
| `entry_decision_made` | `telemetry/alpaca_entry_decision_made_emit.py:emit_entry_decision_made` (called from `main.py` entry path ~10539) | `write_run("run", …)` → `logs/run.jsonl` | `phase2_enabled` arg must be true → wired to `strict_runlog_effective()` |
| `trade_intent` (entered) | `main.py:_emit_trade_intent` | `jsonl_write("run", …)` → `logs/run.jsonl` | `strict_runlog_effective()` true |
| `exit_intent` | `main.py:_emit_exit_intent` | `jsonl_write("run", …)` | `strict_runlog_effective()` true |
| `canonical_trade_id_resolved` | `AlpacaPaperBroker.mark_open` in `main.py:mark_open` | `jsonl_write("run", …)` | Prior `canonical_trade_id` from attribution keys must **differ** from fill-time `build_trade_key` |
| Unified entry attribution | `emit_entry_attribution` paths in `main.py` + backfill script | `logs/alpaca_unified_events.jsonl` (+ strict backfill mirror) | Emitted on entry / backfill |
| Orders `canonical_trade_id` | `main.py:log_order` (enrichment from pending rows) | `logs/orders.jsonl` | Metadata / pending order row with `canonical_trade_id` |
| Historical repair | `scripts/audit/strict_chain_historical_backfill.py:main` | `logs/strict_backfill_run.jsonl`, `logs/strict_backfill_orders.jsonl`, unified backfill | `logs/exit_attribution.jsonl` present |

Config helpers: `main.py:strict_runlog_effective`, env `STRICT_RUNLOG_TELEMETRY_ENABLED`, `PHASE2_TELEMETRY_ENABLED`.
