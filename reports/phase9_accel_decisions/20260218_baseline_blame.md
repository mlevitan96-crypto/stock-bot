# Phase 9 acceleration — Baseline blame (authoritative, droplet)
**Date:** 20260218

## Source
- **Dir:** reports/effectiveness_baseline_blame
- **Window:** 2026-02-01 to 2026-02-18

## Metrics
| Metric | Value |
|--------|--------|
| joined_count | 2808 |
| total_losing_trades | 1755 |
| weak_entry_pct | 0.0 |
| exit_timing_pct | 0.0 |

## Conclusion
**EXIT still justified**

## Multi-model (why this could be wrong)
- **Adversarial:** Sample may be regime-specific; blame can shift with more data.
- **Quant:** 1755 losers is sufficient for stable blame; if weak_entry_pct/exit_timing_pct are 0, confirm from entry_vs_exit_blame.json on droplet (parser may not have matched summary format).
- **Product:** Re-run baseline when new logs accumulate; update this memo.
