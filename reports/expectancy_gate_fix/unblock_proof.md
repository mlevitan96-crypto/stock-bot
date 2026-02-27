# Expectancy gate fix — Unblock proof

**Date:** 2026-02-18 19:48 UTC
**Proof window:** ~15 min after deploy

## Aggregated (last 10 cycles / proof window)
- candidate_count (considered) last cycle: **0**
- total considered (last 10 cycles): **0**
- orders_submitted_count (last cycle): **0**
- total orders (last 10 cycles): **0**
- expectancy_pass_count (from EXPECTANCY_DEBUG or gate_counts): **0**
- score_floor_breach blocks: **291** (of 291 expectancy_blocked)
- score_floor_breach share: **100.0%**

## Gate counts (expectancy_blocked by reason)
```
{
  "score_floor_breach": 291
}
```

## Last cycle_summary entries (up to 5)
```
[
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  },
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  },
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  },
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  },
  {
    "considered": 0,
    "orders": 0,
    "gate_counts": {}
  }
]
```

## Example candidate traces (EXPECTANCY_DEBUG)
```
(no EXPECTANCY_DEBUG lines in captured pane)
```

## PASS criteria
- expectancy_pass_count > 0: **FAIL**
- score_floor_breach not ~100%: **FAIL**
- orders_submitted_count > 0 or clear cap: **PASS**

## Verdict
**FAIL** (in this proof window)

## Note
Last 10 cycle_summary entries have **considered=0** (no candidates in those cycles — market or no_clusters). The 291 score_floor_breach are from **earlier** log lines (pre-fix or prior cycles). So this run **cannot confirm** unblock; need evidence from a window where considered > 0. See nuclear_audit_postfix_summary for current pipeline state.