# Phase 9 acceleration — Gate 50 comparison (droplet)
**Date:** 20260218

## Baseline (reports/effectiveness_baseline_blame)
| Metric | Value |
|--------|--------|
| joined_count | 2808 |
| total_losing_trades | 1755 |
| weak_entry_pct | 0.0 |
| exit_timing_pct | 0.0 |
| win_rate | 0.375 |
| avg_profit_giveback (weighted) | N/A |

## Proposed / paper (reports/effectiveness_paper_score028_gate50)
| Metric | Value |
|--------|--------|
| joined_count | 305 |
| total_losing_trades | 197 |
| weak_entry_pct | 0.0 |
| exit_timing_pct | 0.0 |
| win_rate | 0.3541 |
| avg_profit_giveback (weighted) | N/A |

## Deltas (paper − baseline)
| Metric | Delta |
|--------|--------|
| win_rate (pp) | -2.09 |
| avg_profit_giveback | N/A |

## LOCK criteria
- win_rate Δ ≥ -2%: **FAIL** (delta = -2.09)
- giveback Δ ≤ +0.05: **PASS** (delta = None)
- **Overall: FAIL — REVERT**

## Metric definitions
- win_rate = (joined_count - total_losing_trades) / joined_count.
- avg_profit_giveback = frequency-weighted average of avg_profit_giveback across exit_reason_code from exit_effectiveness.json (same for both dirs).

## Sanity checks (Step 1)
- weak_entry_pct / exit_timing_pct: read directly from each dir's entry_vs_exit_blame.json on droplet; baseline and paper both showed 0.0 (no update to baseline_blame memo needed).
- Paper window: 2026-02-18 to 2026-02-18 (single day); 305 joined trades. Overlay start confirmed from state/live_paper_run_state.json when accel script ran.
