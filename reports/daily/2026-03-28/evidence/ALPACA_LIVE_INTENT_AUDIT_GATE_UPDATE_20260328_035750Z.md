# Alpaca live intent — audit / gate update

**UTC:** 2026-03-28T03:57:50Z

## Strict completeness (`evaluate_completeness`)

- Ingests `entry_decision_made` from primary + `strict_backfill_run.jsonl` (same iterator as other run events).
- For each closed trade whose **open** epoch ≥ `LIVE_ENTRY_INTENT_REQUIRED_SINCE_EPOCH` (2026-03-28T00:00:00Z):
  - Picks **best** row by `(non-synthetic, audit_ok, layer_count)` via `score_entry_decision_made_row`.
  - If `audit_entry_decision_made_row_ok(best)` is false → `live_entry_decision_made_missing_or_blocked`.
- `MISSING_INTENT_BLOCKER` rows fail `audit_entry_decision_made_row_ok` → **FAIL** (loud).
- MFE/MAE / path metrics remain non-gating.

## Learning invariant confirmation (`alpaca_learning_invariant_confirmation.py`)

- Phase 2: trades in the post-epoch cohort require contract-satisfying `entry_decision_made` (same picker + audit); legacy path retained for older opens.
- Reports `entry_decision_made_rows_total`, non-synthetic counts, contract-OK row count.
