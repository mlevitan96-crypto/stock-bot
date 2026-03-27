# Dashboard tab live-data audit (SRE / CSA operator view)

**Date:** 2026-03-27  
**Scope:** Flask dashboard tabs — whether UI refetches on open + periodic refresh, and which APIs back each surface.  
**CSA note:** Panels labeled PARTIAL / “not certified” remain correct; this audit is **operational liveness**, not learning certification.

## Code fix applied (2026-03-27)

- **SRE Monitoring:** `loadSREContent()` previously **skipped** `fetch('/api/sre/health')` after the first successful render (`dataset.loaded` + no `"Loading"` substring), so the **60s interval and revisiting the tab showed stale data**. It now **always refetches** on each call.
- **`/api/sre/health` (8081 proxy path):** When health comes from `http://localhost:8081/api/sre/health`, the dashboard now **merges `stagnation_watchdog`** via `_calculate_stagnation_watchdog()` if the bot payload omitted it (parity with the local `sre_monitoring` fallback path).
- **SRE UI:** Footer line documents refresh behavior and shows payload `ts` / `timestamp` when present.

## Tab-by-tab (data source + refresh behavior)

| Tab | Primary APIs / artifacts | Refresh on revisit / interval |
|-----|---------------------------|-------------------------------|
| **Open Positions** | `/api/positions`; strip uses SRE + executive | `updateDashboard()` when tab active; interval elsewhere in page |
| **SRE Monitoring** | `/api/sre/health`, `bar_health_summary`, `/api/version`, `/api/versions`, ledger `/api/sre/self_heal_events` | **Fixed:** every open + ~60s while tab active |
| **Executive Summary** | `/api/executive_summary`, `/api/sre/health` | Always refetches; **~60s** when tab active |
| **Closed Trades** | `/api/stockbot/closed_trades` | Minimal loader always refetches; **~60s** interval calls `loadClosedTrades` |
| **Trading Readiness** | `/api/failure_points` | Always refetches; loading banner only first paint; **~30s** when tab active |
| **Signal Review** | `/api/signal_history` | Always refetches; **~30s** when tab active |
| **Telemetry** | `/api/telemetry/latest/*`, computed JSON | Full `loadTelemetryContent` always refetches; **~60s** when tab active |
| **System Health** | `/api/dashboard/data_integrity`, telemetry index | Minimal `loadSystemHealth` always refetches; **~120s** when tab active |
| **Learning & Readiness** | `/api/learning_readiness` | Always refetches on call (no stale guard found) |
| **Profitability & Learning** | `/api/profitability_learning` (cockpit file) | Always refetches on call |
| **Alpaca Fast-Lane** | `/api/stockbot/fast_lane_ledger` | Always refetches on call |
| **Alpaca operational activity** (positions area) | `/api/alpaca_operational_activity` | Loaded on bootstrap / switchTab positions path |

## Droplet verification

Run on the droplet (with `.env` auth):

```bash
set -a && source /root/stock-bot/.env && set +a
python3 -u scripts/dashboard_verify_all_tabs.py --json-out reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_<TS>.json
```

Expect **all endpoints HTTP 200** (24 paths as of this change, including `bar_health_summary`). **Droplet check 2026-03-27:** `24 / 24 returned 200` after deploy.

## Minimal bootstrap script (first paint)

The first `<script>` block defines thin `window.loadSREContent` / `loadExecutiveSummary` / etc. A **full** `loadSREContent` in the second script is **not** present — the **rich SRE panel** is the `function loadSREContent` above, which runs after the IIFE. If JS fails mid-page, the minimal SRE card may show; normal load uses the full implementation.

**CSA_VERDICT:** DASHBOARD_TAB_REFRESH_HARDENED (SRE + health proxy parity + verifier list updated)
