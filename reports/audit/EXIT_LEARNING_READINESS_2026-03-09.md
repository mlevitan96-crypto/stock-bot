# Exit Learning Readiness

**Date:** 2026-03-09
**Generated:** 2026-03-09T15:51:11.038256+00:00

## CSA verification

| Check | Status | Notes |
|-------|--------|-------|
| Trace file exists | NO | `reports/state/exit_decision_trace.jsonl` |
| Trace record count | 0 | Append-only samples |
| Schema doc exists | YES | EXIT_DECISION_TRACE_SCHEMA.md |
| Signal registry exists | YES | 14 signals |

## Reconstructability

| Question | Can answer? |
|----------|-------------|
| Peak unrealized moment + signal state at peak | NO — need trace samples with unrealized_pnl + signals |
| Exit eligibility timeline | NO — need ts + exit_eligible + exit_conditions |
| Which exit should have fired? | NO — need exit_conditions |
| What signal component was decisive? | NO — need signals + registry |

## Conclusion

**Gaps:** Ensure trace is populated on droplet (open positions sampled every N seconds), schema and registry are present. After first run with open positions, re-run this check.
