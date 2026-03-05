# B2 Live Paper — Start-of-Test Snapshot

**Captured (UTC):** 2026-03-05 (immediately after enabling B2 + PAPER on droplet)  
**Scope:** Last 387 exits (same as learning baseline)  
**Deployed commit:** 49e5fe92b51b  

## Exit reason distribution (baseline for B2 test)

- **Signal_decay share (30d window):** 97.81% of exits (1967 / 2011).
- Exit reason mix is dominated by signal_decay; B2 is expected to **reduce** the share of early signal_decay exits (hold < 30 min) over the test window.

## PnL attribution summary

| Metric | Value |
|--------|--------|
| total_pnl_attribution_usd | -60.39 |
| total_exits | 387 |
| win_rate | 21.02% |
| avg_hold_minutes | 31.77 |

## Telemetry readiness

| Metric | Value |
|--------|--------|
| total_exits_in_scope | 387 |
| telemetry_backed | 387 |
| pct_telemetry | 100% |
| ready_for_replay | true |

## Purpose

This snapshot is the baseline for comparing post-B2 metrics: delta in exit reason mix (signal_decay share should drop), delta in PnL attribution, and tail risk. See B2_LIVE_PAPER_TEST_PLAN.md for success metrics and tripwires.
