# Test determinism (20260327_MKTS_FINAL)

- `tests/test_alpaca_entry_ts_normalization.py` — `TestStrictCompletenessGate.test_gate_flags_missing_unified_exit` and `test_strict_gate_resolves_intent_vs_fill_via_canonical_trade_id_resolved` use `open_ts_epoch=0.0` instead of `None`, so synthetic `exit_attribution` rows are not filtered by the current calendar day’s ET market open.
- The intent/fill resolution test also sets `collect_complete_trade_ids=True` and asserts `len(complete_trade_ids)==1`.
