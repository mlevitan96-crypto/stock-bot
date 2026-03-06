# CSA Trade 100 Trigger — Test Report

**Date:** 2026-03-06  
**Harness:** `scripts/test_csa_trade_100_trigger.py`

## Summary

- **Simulated trades:** 105 (all via `record_trade_event("executed", _run_csa_in_background=False)`).
- **CSA fired:** Exactly once at trade count 100.
- **Result:** PASS.

## Assertions

| Check | Result |
|-------|--------|
| `total_trade_events` == 105 | OK |
| `last_csa_trade_count` == 100 | OK |
| `last_csa_mission_id` starts with `CSA_TRADE_100_` | OK |
| Event log line count == 105 | OK |
| `CSA_VERDICT_<mission_id>.json` exists | OK |
| `CSA_FINDINGS_<mission_id>.md` exists | OK |
| `reports/board/CSA_TRADE_100_*.md` exists | OK |

## Artifacts created

- `reports/audit/CSA_VERDICT_CSA_TRADE_100_<timestamp>.json`
- `reports/audit/CSA_FINDINGS_CSA_TRADE_100_<timestamp>.md`
- `reports/audit/CSA_VERDICT_LATEST.json`, `CSA_SUMMARY_LATEST.md`
- `reports/board/CSA_TRADE_100_2026-03-06.md`

## Notes

- Test uses `TRADE_CSA_STATE_DIR=reports/state/test_csa_100` so production state is not overwritten.
- CSA ran synchronously in the test (`_run_csa_in_background=False`) so artifacts are present before assertions.

## Errors

None.
