# Final Intelligence Verdict

**Generated:** 2026-01-28T17:19:47.047926+00:00 (UTC)

---

## Subsystem verdicts

| Subsystem | Verdict | Notes |
|-----------|---------|-------|
| Data presence | PASS | See INTEL_DATA_PRESENCE.md |
| Signal/features | PASS | PASS when trade_intent in window; WARN when none |
| Score components | PASS | See INTEL_SCORE_COMPONENTS.md |
| Gates | PASS | See INTEL_GATES.md |
| Decision trace | PASS | missing_trace=0, sentinel_events=0 |
| Artifacts | WARN | See INTEL_ARTIFACT_HEALTH.md |
| Silent failures | FAIL | 64 patterns found; do not PASS if any remain |

## Missing / stale / disabled intelligence
- Code patterns indicating silent fallbacks / swallowed errors: 64

## Statement

**The STOCK-BOT intelligence pipeline is NOT complete, coherent, or free of silent degradation.**

(Do not declare PASS unless zero silent failures and zero missing traces.)