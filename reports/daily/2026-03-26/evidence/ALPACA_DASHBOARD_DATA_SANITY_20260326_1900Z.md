# Alpaca dashboard data sanity and freshness audit

**Artifact ID:** `ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z`  
**Machine JSON:** [`reports/ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z.json`](../ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z.json)  
**Method:** `python scripts/alpaca_dashboard_truth_probe.py --json reports/ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z.json` with `DASHBOARD_USER` / `DASHBOARD_PASS` set (Flask `test_client`, repo root `c:\Dev\stock-bot`).

---

## Summary

| Check | Result |
|--------|--------|
| Tab-primary endpoints HTTP 200 | **22/22** after computed-artifact contract fix |
| Alpaca REST on dev workstation | **Not connected** — `/api/positions` returns `error: Alpaca API not connected` (expected without keys) — state **BLOCKED** for live positions truth until keys + network on runtime |
| Telemetry bundle | **latest_date `2026-02-04`** — stale vs wall clock → panels should show **STALE** (now explicit in UI for missing computed JSON) |
| `live_vs_shadow_pnl.json` | **Missing** in latest bundle → API returns **200**, `ok: false`, `error: computed artifact missing: live_vs_shadow_pnl.json` |
| Closed trades API | **174** rows returned (local data) |
| Signal history | **0** rows — **OK** if explained (UI copy updated) |
| Data integrity | `LEARNING_STATUS: BLOCKED`, `trades_complete: 0` (per payload) |

---

## Per-tab sanity (condensed)

| Tab | Row / key signal | Max timestamp / as-of | Freshness vs contract |
|-----|------------------|------------------------|------------------------|
| Positions | 0 positions | n/a | **BLOCKED** without Alpaca API |
| Closed trades | 174 | from `response_generated_at_utc` in payload | Compare to last exit log write on droplet |
| System health | `generated_at_utc` in JSON | Server time | **OK** as snapshot; compare log `last_write` rows inside payload |
| Telemetry | Bundle `2026-02-04` | `as_of_ts` in index | **STALE** relative to 2026-03-26 audit date |
| Fast lane | 1 cycle | cycle timestamps | **OK** if shadow job running |

---

## Droplet actions (Quant + SRE)

1. Ensure `telemetry/<latest>/computed/live_vs_shadow_pnl.json` (and related) are produced by the scheduled extract, **or** accept **STALE** until the pipeline runs.
2. Validate `logs/alpaca_*` and exit attribution freshness against `canonical_log_staleness` in `/api/dashboard/data_integrity`.
