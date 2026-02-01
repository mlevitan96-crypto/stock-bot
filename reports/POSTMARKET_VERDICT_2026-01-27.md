# Post-Market Verdict — 2026-01-27

**Generated:** 2026-01-27T22:02:19.785752+00:00

---

## Summary of live trading behavior

- **Signals (trade_intent):** 1693 total | 63 entered | 1630 blocked
- **Real orders:** 1171
- **Exits (exit_intent):** 56
- **Positions still open:** 16
- **Displacement:** evaluated=68 allowed=0 blocked=68
- **Shadow decisions:** 0

## What worked

- Signal coverage: 1693 trade_intent events.
- Executions: 1171 real orders.
- Exit intent: 56 exit_intent events.

## What underperformed

- Low enter rate 3.7%; blocked 96.3%.
- Blocked reasons: {'displacement_blocked': 1630}.
- Displacement: 68 blocked vs 0 allowed.

## Notable patterns

- Blocked reasons: {'displacement_blocked': 1630}
- Exit reasons: {'signal_decay(0.46)+flow_reversal': 1, 'signal_decay(0.53)': 1, 'signal_decay(0.60)': 4, 'signal_decay(0.45)+flow_reversal': 2, 'signal_decay(0.49)': 2, 'signal_decay(0.56)+flow_reversal': 1, 'trail_stop': 1, 'stale_alpha_cutoff(121min,0.00%)': 1, 'signal_decay(0.26)': 3, 'signal_decay(0.23)': 2, 'signal_decay(0.27)': 1, 'signal_decay(0.16)': 1, 'signal_decay(0.32)': 1, 'signal_decay(0.25)': 1, 'signal_decay(0.13)': 1, 'signal_decay(0.18)': 1, 'signal_decay(0.24)': 1, 'signal_decay(0.28)': 1, 'signal_decay(0.20)': 1, 'signal_decay(0.15)': 1, 'signal_decay(0.59)': 3, 'signal_decay(0.41)': 1, 'signal_decay(0.48)': 2, 'signal_decay(0.52)': 4, 'signal_decay(0.42)': 1, 'signal_decay(0.54)': 1, 'signal_decay(0.39)+flow_reversal': 2, 'signal_decay(0.47)': 1, 'signal_decay(0.55)': 1, 'signal_decay(0.48)+flow_reversal': 1, 'signal_decay(0.60)+flow_reversal': 1, 'signal_decay(0.55)+flow_reversal': 1, 'signal_decay(0.56)': 1, 'signal_decay(0.57)': 1, 'signal_decay(0.47)+flow_reversal': 1, 'signal_decay(0.53)+flow_reversal': 1, 'signal_decay(0.58)': 5}
- Thesis break: {'other': 53, 'trail_stop': 1, 'flow_reversal': 2}

## Readiness for next trading day

- **Needs attention: review underperformed segments before next day.**

## Generated reports and CSVs

- reports/POSTMARKET_PREFLIGHT.md
- reports/POSTMARKET_SIGNALS.md
- exports/POSTMARKET_trade_intent_summary.csv
- reports/POSTMARKET_EXECUTION.md
- exports/POSTMARKET_orders_summary.csv
- reports/POSTMARKET_POSITIONS_AND_EXITS.md
- exports/POSTMARKET_exit_summary.csv
- reports/POSTMARKET_GATES_AND_DISPLACEMENT.md
- exports/POSTMARKET_displacement_stats.csv
- reports/POSTMARKET_SHADOW_ANALYSIS.md
- exports/POSTMARKET_shadow_scoreboard.csv
- reports/EOD_ALPHA_DIAGNOSTIC_2026-01-27.md

---

**EOD diagnostic:** PASS — all required sections present.
