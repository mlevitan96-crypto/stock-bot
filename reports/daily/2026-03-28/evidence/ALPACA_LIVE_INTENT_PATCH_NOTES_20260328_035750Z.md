# Alpaca live intent — patch notes (telemetry-only)

**UTC:** 2026-03-28T03:57:50Z

## Files changed

| File | Change |
|------|--------|
| `telemetry/alpaca_entry_decision_made_emit.py` | **New:** build + emit `entry_decision_made`, audit helpers, best-row scoring |
| `main.py` | Entered `trade_intent`: `entry_intent_synthetic`, `entry_intent_source`; after fill emit `emit_entry_decision_made` |
| `telemetry/alpaca_strict_completeness_gate.py` | Collect `entry_decision_made`; post-epoch reason `live_entry_decision_made_missing_or_blocked` |
| `scripts/audit/alpaca_learning_invariant_confirmation.py` | Phase 2: post-epoch trades require contract `entry_decision_made`; stats |
| `docs/ALPACA_LIVE_ENTRY_INTENT_CONTRACT.md` | **New:** canonical contract |
| `tests/test_alpaca_entry_decision_made_emit.py` | **New:** contract + emit callback tests |
| `tests/test_strict_completeness_live_entry_decision_made.py` | **New:** strict gate ARMED/BLOCKED |

## Telemetry-only proof

- No changes to `submit_entry`, sizing, routing, thresholds, or signal scoring formulas.
- Only additional JSONL records and audit reads.
