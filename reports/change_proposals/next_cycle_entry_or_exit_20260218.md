# Next cycle lever — entry vs exit (stub only, no execution)

**Date:** 2026-02-18  
**Status:** Proposal stub; **do not** execute a new overlay or paper run until blame is classifiable and (optionally) giveback is populated.

## Multi-model committee input (post–baseline v4)

- **Baseline v4:** joined 2000, losers 1292; weak_entry_pct=0, exit_timing_pct=0, **unclassified_pct=100** (see `reports/phase9_data_integrity/20260218_baseline_v4_verification.md`).
- **Exit quality:** Proof doc shows with_exit_quality_metrics = 0 in newest 500 lines (no new exits since deploy, or process not restarted after pull). Giveback still N/A in aggregates.
- **Attribution:** Last 200 attribution lines have entry_score in context (200/200). Join may still fail (exit records’ entry_timestamp not matching entry’s entry_ts bucket), so joined rows may not get entry_score.
- **Conclusion:** Unclassified still dominates. **STOP:** Fix remaining missing fields before choosing a lever.

## Required before proposing a lever

1. **Join key:** Ensure exit_attribution records have **entry_timestamp** that matches the attribution entry’s **entry_ts** (or entry_ts_bucket) so joined rows receive **entry_score**. Then re-run effectiveness; weak_entry_pct should become non-zero where entry_score < 3.
2. **Exit quality (optional but recommended):** Restart paper after pull so new exits use the high_water fix; after new exits, re-sample and confirm exit_quality_metrics > 0; then giveback can populate.

## Conditional proposal (after above)

- **If weak_entry dominates:** Propose **one entry lever** — e.g. down-weight or gate the worst signal_id by harm.
- **If exit_timing dominates:** Propose **one exit lever** — e.g. small adjustment to exit_score weight or threshold for the worst exit_reason_code by giveback.
- **If still unclassified dominates:** Do not propose a lever; fix join/exit_timestamp and re-run.

## What was done

- Exit quality emission proof written (0/500; diagnosis: no new exits or process not restarted).
- entry_score defensive logging added in log_attribution (open_ records).
- Baseline v4 run; verification written. Next lever stub updated; **no lever proposed** until blame is classifiable.
