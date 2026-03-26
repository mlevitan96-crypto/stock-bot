# Signal Contribution Audit

**Date:** 2026-03-08
**Decisions analyzed:** 300

## Per-signal summary

| Signal | Fired% | Non-zero% | Mean | Median | Min | Max | Always zero? |
|--------|--------|-----------|------|--------|-----|-----|---------------|
| flow | 100.0 | 100.0 | 2.3319 | 2.4 | 0.754 | 2.4 | no |
| dark_pool | 100.0 | 100.0 | 0.26 | 0.26 | 0.26 | 0.26 | no |
| insider | 100.0 | 100.0 | 0.125 | 0.125 | 0.125 | 0.125 | no |
| iv_skew | 100.0 | 100.0 | 0.0653 | 0.063 | 0.008 | 0.117 | no |
| smile | 100.0 | 100.0 | 0.007 | 0.007 | 0.007 | 0.007 | no |
| whale | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | no |
| event | 100.0 | 100.0 | 0.3244 | 0.34 | 0.08 | 0.34 | no |
| motif_bonus | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | no |
| toxicity_penalty | 100.0 | 98.7 | -0.2554 | -0.27 | -0.27 | 0.0 | no |
| regime | 100.0 | 100.0 | 0.012 | 0.012 | 0.012 | 0.012 | no |
| congress | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | no |
| shorts_squeeze | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | no |
| institutional | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | no |
| market_tide | 100.0 | 100.0 | -0.0104 | -0.052 | -0.052 | 0.285 | no |
| calendar | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | no |
| greeks_gamma | 100.0 | 87.3 | 0.0699 | 0.08 | 0.0 | 0.08 | no |
| ftd_pressure | 100.0 | 100.0 | 0.06 | 0.06 | 0.06 | 0.06 | no |
| iv_rank | 100.0 | 100.0 | 0.0832 | 0.1 | 0.03 | 0.2 | no |
| oi_change | 100.0 | 100.0 | 0.07 | 0.07 | 0.07 | 0.07 | no |
| etf_flow | 100.0 | 100.0 | 0.06 | 0.06 | 0.06 | 0.06 | no |
| squeeze_score | 100.0 | 100.0 | 0.046 | 0.04 | 0.04 | 0.1 | no |
| freshness_factor | 100.0 | 100.0 | 0.9922 | 0.993 | 0.979 | 1.0 | no |

## Justification (always-zero allowed)
V3 expanded intel (congress, shorts_squeeze, institutional, market_tide, calendar, greeks_gamma, ftd_pressure, iv_rank, oi_change, etf_flow, squeeze_score) use neutral default when data missing (MEMORY_BANK §7.1). Always-zero in snapshot is acceptable.

## Blockers

- None