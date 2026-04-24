# UW_GRANULARITY_RECOVERY_OR_RECAPTURE

## Phase 6 trigger (from WHY)

- **WHY taxonomy:** `OVERRIDE_CONFLICT` / displacement policy (`BLOCKED_WHY_DIAGNOSIS.json`) — **not** `MISSING_FEATURE` for UW payloads at the blocked row.
- **Blocked rows already carry:** `components`, `signals`, optional `uw_signal_quality_score`, `uw_edge_suppression_rate` via `log_blocked_trade` (`main.py` ~1102–1167).

## Recovery (no new sink required)

| Sink | Evidence |
|------|----------|
| `logs/score_snapshot.jsonl` | **2000** lines on droplet (`wc -l` 2026-04-01 capture) |
| `state/blocked_trades.jsonl` | **8669** rows; includes `components` dict at decision time |
| `state/uw_cache/` | Shard JSON cache (listed in prior Profit V2 inventory) |

## Re-capture

- **`logs/uw_signal_context.jsonl`** — **not** created: **not required** by diagnosis; would duplicate fields already on blocked rows + `score_snapshot`.

## Hard gate

- **`UW_GRANULARITY_BLOCKER.md`** — **not written.**
