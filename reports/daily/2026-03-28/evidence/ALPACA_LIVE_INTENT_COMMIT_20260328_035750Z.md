# Alpaca live intent — commit record

**UTC:** 2026-03-28T03:57:50Z

## Commit

- **Message:** `feat(telemetry): emit live entry_decision_made and gate post-epoch learning intent`
- **Resolve canonical hash:** `git log -1 --format=%H -- telemetry/alpaca_entry_decision_made_emit.py`  
  (returns the commit that introduced the emitter; same commit as this bundle when checked out on `main`.)

## Files (summary)

- `telemetry/alpaca_entry_decision_made_emit.py` (new)
- `telemetry/alpaca_strict_completeness_gate.py` (live-intent epoch gate)
- `main.py` (emit + trade_intent LIVE markers)
- `scripts/audit/alpaca_learning_invariant_confirmation.py` (Phase 2 contract)
- `docs/ALPACA_LIVE_ENTRY_INTENT_CONTRACT.md` (new)
- `tests/test_alpaca_entry_decision_made_emit.py`, `tests/test_strict_completeness_live_entry_decision_made.py` (new)
- Evidence under `reports/daily/2026-03-28/evidence/ALPACA_*_20260328_035750Z.md`
