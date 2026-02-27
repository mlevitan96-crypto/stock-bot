# Entry Score and Dashboard Verification

**Conclusion:** Entry scores are **not** broken. The "0.00" in the Open Positions Entry column is a **dashboard display issue** (path + no recovery). Trading life cycle is correct; no other issues found.

## Entry scores in the trading life cycle

- **Computed** before entry in `main.py`; entry is blocked if score <= 0 (`invalid_entry_score_blocked`).
- **Passed** to `executor.mark_open(..., entry_score=score)` on fill.
- **Persisted** in `state/position_metadata.json` via `_persist_position_metadata()` (key: symbol, field: `entry_score`).
- **Recovery:** For positions added by reconciliation, `recover_entry_score_for_symbol()` fills in score from `pending_fill_scores.json` or `logs/attribution.jsonl`; reconciliation and health checks update metadata.

So the backend never drops entry scores; they are stored (or recovered) for open positions.

## Why the dashboard showed 0.00

- Position metadata was read with **cwd-relative** path (`StateFiles.POSITION_METADATA`). If the dashboard ran with a different cwd (e.g. systemd), it read the wrong file and got no `entry_score`.
- When `entry_score` was missing or 0, the dashboard had **no fallback** to recovery (pending_fill / attribution).

Current/Prev/Delta showed values because they come from other caches/compute; only the Entry column depended on metadata + recovery.

## Fixes in code (dashboard)

1. **Path:** Load position metadata from `(Path(_DASHBOARD_ROOT) / StateFiles.POSITION_METADATA).resolve()` so the same file as the bot is used.
2. **Recovery:** When `entry_score` is missing or <= 0, call `recover_entry_score_for_symbol(symbol, pop_pending=False)` and use the result for display.
3. **Cwd:** Dashboard does `os.chdir(_DASHBOARD_ROOT)` at startup so relative paths (e.g. in recovery) resolve to repo root.
4. **UW / signal caches** in the positions API are also resolved against `_DASHBOARD_ROOT`.

## Trading life cycle – other issues

Reviewed: entry (compute, validate, persist), pending fill, reconciliation, reload/health, exit attribution, dashboard. No other issues; P&L and Current/Prev/Delta behavior support that scoring and tracking work.

## What to do

1. **Deploy** the latest dashboard so the path and recovery changes are live.
2. **Refresh** Open Positions; Entry column should show correct scores for positions that have (or can recover) an entry score.
3. If some rows still show 0.00, check on the server that `state/position_metadata.json` has `entry_score` for those symbols; new entries should persist correctly.
