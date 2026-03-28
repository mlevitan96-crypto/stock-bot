# CSA pre-deploy verdict — Alpaca live intent

**UTC:** 2026-03-28T03:57:50Z

## Reviewed

- Contract: `docs/ALPACA_LIVE_ENTRY_INTENT_CONTRACT.md` + evidence contract memo
- Audits: strict gate + invariant confirmation Phase 2
- Telemetry-only surface area (`main.py` logging branch only)
- Synthetic rejection paths

## Verdict

**CSA_ALPACA_LIVE_INTENT_READY_TO_DEPLOY**

Rationale: LIVE rows are explicitly non-synthetic; blockers fail closed without fabricated scores; best-row selection prevents duplicate/stale rows from masking missing intent; Kraken isolation preserved.
