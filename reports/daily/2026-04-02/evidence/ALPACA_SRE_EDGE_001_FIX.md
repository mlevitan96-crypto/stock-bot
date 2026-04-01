# SRE-EDGE-001 — strict cohort trade_id dedupe (source fix)

## Problem

`strict_cohort_trade_ids` could contain the same `trade_id` twice when `exit_attribution.jsonl` had duplicate lines for one close. That made `len(strict_cohort_trade_ids) > len(set(...))` while `trades_seen` counted duplicate rows, breaking cohort ↔ rollup alignment.

## Root cause

`evaluate_completeness` iterated every row in `closed` without collapsing on `trade_id`.

## Fix (chronological + deterministic)

**File:** `telemetry/alpaca_strict_completeness_gate.py`

1. **Helper:** `_dedupe_closed_rows_by_trade_id(closed_rows)`  
   - Iterates rows in order.  
   - **First-seen order** of `trade_id` is preserved in the output list.  
   - **Last row wins** for the `(tid, sym, ent_iso, rec)` tuple (latest duplicate line dominates payload).

2. **Call site:** Immediately after the postfix / recent-closes filter on `closed`, before the completeness loop:
   - Records `exit_attribution_rows_before_trade_id_dedupe`
   - Sets `closed, _dup_removed = _dedupe_closed_rows_by_trade_id(closed)`

3. **Gate output (new fields):**
   - `exit_attribution_rows_before_trade_id_dedupe`
   - `exit_attribution_duplicate_trade_id_rows_removed`
   - `trades_seen` is now `len(closed)` **after** dedupe (unique trade closes in cohort).

4. **`strict_cohort_trade_ids`:** Still appended once per row in `closed`; with deduped `closed`, list length equals unique count and matches `trades_seen` when `collect_strict_cohort_trade_ids` collects all.

## Audit script

`scripts/audit/check_strict_cohort_dedup.py` — loads newest `ALPACA_STRICT_GATE_SNAPSHOT_*.json` (or `--json`) and asserts `cohort_len == unique_len`.

## Before / after

| Before | After |
|--------|--------|
| Duplicate exit lines → duplicate `tid` in `closed` → double `complete` risk and duplicate strict ids | One row per `trade_id` → single completeness outcome and unique strict cohort list |
| `400` list entries, `399` unique (SOFI duplicate observed) | `len == len(set)` for strict cohort export |
