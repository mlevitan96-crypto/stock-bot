# Unified Truth Audit — Verdict

**Date:** 20260218
**Verdict:** **FAIL**

## Ranked integrity failures
1. Axis 1 (Live vs Diagnostic) — No scoring events observed in score_snapshot window; diagnostic produced no data
2. Axis 2 (Signal Contribution) — No scoring events observed in score_snapshot window
3. Axis 3 (Score Distribution) — No scoring events observed in score_snapshot window

## Exact fixes (no tuning)

1. Ensure score_snapshot.jsonl is emitted (live paper run) or data/uw_flow_cache.json exists and diagnostic runs.

## Axis results
1. Live vs Diagnostic: FAIL
2. Signal Contribution: FAIL
3. Score Distribution: FAIL
4. Gate Alignment: PASS
5. Entry/Exit Symmetry: PASS
6. Data Freshness: PASS