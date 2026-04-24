# UW_CAPTURE_SKIPPED (Phase 13)

**Condition:** Phase 13 runs only if Phase 11 concludes missing features are required **and** UW is named among them.

**Evidence:** `DISPLACEMENT_GOOD_VS_BAD_SEPARATION.json` records `conclusion_AB` as **A)** — separation using existing decision-time features (distance-to-threshold, hour UTC, ATR%, volume, concurrency, snapshot join).

**Decision:** No additive `logs/uw_signal_context.jsonl` sink, no `verify_uw_signal_context_nonempty.py`, and no `UW_CAPTURE_IMPLEMENTATION.md` / `UW_CAPTURE_SMOKE_PROOF.md` for this run.
