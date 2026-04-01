# CSA chain triage verdict

## Leading hypothesis

**Class A — emitters not executing (gated).** Strict runlog events (`entry_decision_made`, `trade_intent` entered, `exit_intent`) were suppressed when only `PHASE2_TELEMETRY_ENABLED` controlled emission and Phase 2 was off in production. `canonical_trade_id_resolved` is sparse when intent-time keys never diverge from fill-time keys because the intent chain never wrote attribution keys.

## Top three falsifiable checks (all exercised on droplet)

1. **Startup banner:** `logs/system_events.jsonl` contains `subsystem=telemetry_chain`, `event_type=startup_banner`, with `strict_runlog_effective: true` after restart → proves config path is live. **Result: PASS** (see `SRE_CHAIN_EMITTER_INVOCATION_PROOF.md`).
2. **Sink append after fix + backfill:** `evaluate_completeness(..., open_ts_epoch=STRICT_EPOCH_START)` returns `LEARNING_STATUS=ARMED` and `trades_incomplete=0` → proves strict reader sees sufficient rows (primary + backfill). **Result: PASS** (`ALPACA_STRICT_AFTER_FIX.json`).
3. **Not a sink mismatch (C):** Gate uses `_stream_jsonl_primary_then_backfill`; backfill writes `strict_backfill_*` files the gate already merges. **Result:** remediation via additive files confirms reader/writer alignment.

## Rejected (this incident)

- **D alone:** Orders tagging is downstream of the same attribution + intent chain; fixing gates + backfill restored joins without a separate late-bound order enricher in production.
- **B:** No permission errors observed; backfill applied 341 trades in one run.
