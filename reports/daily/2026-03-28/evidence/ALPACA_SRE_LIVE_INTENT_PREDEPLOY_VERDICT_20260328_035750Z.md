# SRE pre-deploy verdict — Alpaca live intent

**UTC:** 2026-03-28T03:57:50Z

## Reviewed

- Emission path: same `jsonl_write("run", …)` pipeline as `trade_intent` (append-only, `ts` injected)
- Failure visibility: `telemetry.entry_decision_made_emit_failed` + `emit_learning_blocker` on emit exceptions
- Session boundaries: per-line JSONL; no new rotation semantics
- Audit vs live: gate reads primary + `strict_backfill_run.jsonl` mirrors (unchanged policy)

## Verdict

**SRE_ALPACA_LIVE_INTENT_PIPELINE_HEALTHY**
