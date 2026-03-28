# Alpaca live intent — test results

**UTC:** 2026-03-28T03:57:50Z  
**Command:** `python -m pytest tests/test_alpaca_entry_decision_made_emit.py tests/test_strict_completeness_live_entry_decision_made.py tests/test_strict_completeness_forward_parity.py -v`

## Result

**9 passed** (Windows, Python 3.14.3, pytest 9.0.2).

## Coverage

- OK contract row passes `audit_entry_decision_made_row_ok`
- Blocker path (`MISSING_INTENT_BLOCKER`) fails audit
- Synthetic / `strict_backfilled` rejected
- `emit_entry_decision_made` invokes `write("run", …)`
- Deterministic builder output for fixed fixture input
- Strict gate **ARMED** when post-epoch trade has OK `entry_decision_made`
- Strict gate **BLOCKED** with `live_entry_decision_made_missing_or_blocked` when absent
- Legacy pre-epoch fixture still **ARMED** (`test_strict_completeness_forward_parity`)

## Full suite note

`pytest tests/` currently hits an unrelated failure in `tests/test_telegram_failure_detector.py::test_evaluate_alpaca_post_close_weekend` on this workspace; Alpaca live-intent tests above are green.
