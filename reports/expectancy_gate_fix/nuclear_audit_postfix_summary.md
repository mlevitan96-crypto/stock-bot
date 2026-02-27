# Expectancy gate fix — Nuclear audit post-fix summary

**Date:** 2026-02-18  
**Audit run:** After deploy (commit 539c5f9) and unblock proof window.

## Nuclear audit result
- **Verdict:** PASS
- **Why no open trades:** Candidates exist but selected_count=0 (gates blocking; see gate_counts)
- **Entry pipeline (05):** candidate_count (considered last cycle) = 33; selected_count (orders last cycle) = 0
- **Aggregated gate_counts (from full tail):** expectancy_blocked:score_floor_breach 495, score_below_min 277

## Interpretation
- Audit PASS: runtime healthy, data fresh, attribution flowing, pipeline produces candidates with a clear gating reason.
- selected_count=0: gates (including expectancy and/or score_below_min) still blocking orders in the sampled window.
- The 495 score_floor_breach are from the full gate.jsonl tail and may include entries from **before** the fix was deployed; the audit does not filter by timestamp.
- Unblock proof window had considered=0 in the last 10 cycle_summary entries, so we did not observe post-fix cycles with candidates in that 15-min window.

## Conclusion
- No regression: nuclear audit PASS.
- Entry pipeline shows candidates (33 in last non-zero cycle) and clear gate_counts.
- Whether score_floor_breach is fixed requires evidence from a window where considered > 0 and gate.jsonl is dominated by post-restart lines (or re-run unblock proof when market has clusters).
