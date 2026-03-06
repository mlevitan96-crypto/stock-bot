# CSA Every-100-Trades — Implementation Report

**Date:** 2026-03-06

## Overview

Dual-layer trigger runs a full CSA profitability review every 100 trade events (executed + blocked + counter-intelligence):

- **Primary trigger:** Trading engine (`main.py`). Every final trade decision calls `record_trade_event()`; at multiples of 100, CSA is run (in a background thread) and state is updated immediately to avoid double-runs.
- **Backup trigger:** Droplet script `scripts/csa_backup_trigger_every_100.py`. Run periodically (e.g. cron every 5 min). Reconciles `total_trade_events` from `reports/state/trade_events.jsonl`; if at a 100-event milestone with no CSA run recorded, runs the same CSA wrapper and updates state. Only fires when the primary missed updating state (e.g. process died after incrementing to 100).

No changes were made to live trading logic (order routing, risk, or execution); only hooks, counters, and CSA trigger calls were added.

## File paths

| Purpose | Path |
|--------|------|
| State file | `reports/state/TRADE_CSA_STATE.json` |
| Event log (for backup reconciliation) | `reports/state/trade_events.jsonl` |
| State + trigger logic | `src/infra/csa_trade_state.py` |
| Trade event model (doc) | `reports/state/trade_event_types.md` |
| CSA wrapper (both triggers) | `scripts/run_csa_every_100_trades.py` |
| Backup trigger (droplet) | `scripts/csa_backup_trigger_every_100.py` |
| Dashboard summarizer | `scripts/summarize_csa_latest_for_dashboard.py` |
| Test harness | `scripts/test_csa_trade_100_trigger.py` |

## How to confirm CSA is firing every 100 trades

1. **State:** Inspect `reports/state/TRADE_CSA_STATE.json`: `total_trade_events` increments with each trade event; `last_csa_trade_count` and `last_csa_mission_id` update when CSA runs at 100, 200, …
2. **Artifacts:** After each 100-event milestone, expect:
   - `reports/audit/CSA_VERDICT_CSA_TRADE_100_<YYYYMMDD-HHMMSS>.json`
   - `reports/audit/CSA_FINDINGS_CSA_TRADE_100_<YYYYMMDD-HHMMSS>.md`
   - `reports/board/CSA_TRADE_100_<YYYY-MM-DD>.md` (board-grade summary)
   - `reports/audit/CSA_VERDICT_LATEST.json`, `CSA_SUMMARY_LATEST.md` (updated by CSA)
3. **Test:** Run `python scripts/test_csa_trade_100_trigger.py` (uses test state dir); should print `OK: ...` and create the above artifacts once at 100.

## How to inspect CSA findings

- **Verdict:** `reports/audit/CSA_VERDICT_LATEST.json` or `reports/audit/CSA_VERDICT_<mission_id>.json`
- **Findings (Markdown):** `reports/audit/CSA_FINDINGS_<mission_id>.md` or `reports/audit/CSA_SUMMARY_LATEST.md`
- **Board summary for 100-trade run:** `reports/board/CSA_TRADE_100_<date>.md`

## How to view CSA_DASHBOARD_LATEST.md

- Run: `python scripts/summarize_csa_latest_for_dashboard.py`
- Output: `reports/board/CSA_DASHBOARD_LATEST.md` (mission_id, verdict, recommendation, top findings, total trade events, last CSA trade count)

## Droplet backup

- On the droplet, schedule `scripts/csa_backup_trigger_every_100.py` (e.g. cron every 5 minutes). It loads state, reconciles from `trade_events.jsonl` if needed, and if `should_run_csa_every_100(state)` is true (and primary had not already run for that count), runs `scripts/run_csa_every_100_trades.py` and updates state.

## Limitations and assumptions

- **Counter-intelligence:** No separate “counter-intelligence rejected” event type; such events are currently counted as blocked (same as `log_blocked_trade`). Can be refined later if a distinct rejection path exists.
- **Reconciliation fill path:** Fills detected only in the position reconciliation loop (and not via `submit_entry` in main) do not call `record_trade_event`; the backup trigger can reconcile from `trade_events.jsonl` only for events that were recorded before a crash.
- **One event per decision:** Exactly one increment per trade event (one per blocked trade, one per filled entry, one per exit attribution); no per-leg or per-partial-fill counting.
- **Background run:** Primary trigger runs CSA in a daemon thread so the trading thread is not blocked; CSA output and exit code are not observed by the engine.
