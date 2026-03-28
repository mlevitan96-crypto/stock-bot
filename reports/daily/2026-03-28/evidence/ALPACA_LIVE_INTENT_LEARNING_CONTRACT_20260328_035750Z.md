# Alpaca live intent — learning contract (evidence)

**UTC:** 2026-03-28T03:57:50Z

Canonical doc: `docs/ALPACA_LIVE_ENTRY_INTENT_CONTRACT.md`

## Summary

- **Event:** `entry_decision_made` on `logs/run.jsonl`.
- **LIVE OK:** `entry_intent_status=OK`, `entry_intent_synthetic=false`, `signal_trace.policy_anchor` set, numeric `entry_score_total`, non-empty `entry_score_components` (or `_no_breakdown` echo of total).
- **Stay-live failure:** `entry_intent_status=MISSING_INTENT_BLOCKER`, `entry_score_components._blocked=true`, audits **FAIL** (no fake breakdown).
- **Synthetic:** `strict_backfill_*` repairs or `entry_intent_synthetic: true` — **not** acceptable as live intent for audits.
- **Non-gating:** MFE/MAE, path/vol analytics unchanged for strict reasons.

## Enforcement epoch

`telemetry/alpaca_strict_completeness_gate.LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH` — opens on/after **2026-03-28 00:00 UTC** require a passing LIVE `entry_decision_made` or the trade chain is incomplete with reason `live_entry_decision_made_missing_or_blocked`.
