# Alpaca dashboard tab inventory and routing audit

**Artifact ID:** `ALPACA_DASHBOARD_TAB_INVENTORY_20260326_1900Z`  
**Scope:** Alpaca paper dashboard only (`dashboard.py` single-page app, route `/`).  
**Evidence:** Route definitions in `dashboard.py` (Flask `@app.route`); UI tab IDs in `DASHBOARD_HTML`.

---

## STOP-GATE 0 — CSA governance contract (APPROVED with notes)

Each **tab** (or global strip) SHALL declare:

| Field | Requirement |
|--------|----------------|
| Route | Browser-visible tab id + primary `fetch` path(s) |
| Backend endpoint | Exact path(s) |
| Data source(s) | Files, APIs, or derived joins |
| Freshness rule | Expected max age or “on-demand / SSR” |
| Join dependencies | Upstream logs or bundles required |

**Allowed states:** `OK` | `STALE(reason, last_update)` | `BLOCKED(integrity reason)` | `DISABLED(wiring reason)`.

**Forbidden:** “Loads but empty” with no explanation.

**CSA verdict:** **APPROVED** for execution of dashboard-only wiring and API contract fixes documented in `ALPACA_DASHBOARD_FIX_IMPLEMENTATION_20260326_1900Z.md`. Trading logic unchanged.

---

## Phase 1 — Tab enumeration (SRE)

| Tab id | UI route | Primary endpoint(s) | Data source(s) | Freshness | Join / deps |
|--------|----------|----------------------|----------------|-----------|-------------|
| *(global)* | `/` (header) | `/api/direction_banner` | `state/direction_readiness.json`, `state/direction_replay_status.json`, board reports | On load + 60s poll | Direction replay pipeline |
| *(global)* | `/` (header) | `/api/situation` | Learning readiness + governance + closed trades sampling | On load + 60s poll | `_get_situation_data_sync` |
| *(global)* | `/` (top strip) | `/api/sre/health`, `/api/executive_summary` | SRE module, trade logs | 60s | Bot/market process |
| positions | `#positions-tab` | `/api/positions` | Alpaca REST (when keys present) | Per refresh (~60s) | `ALPACA_*` env |
| closed_trades | `#closed_trades-tab` | `/api/stockbot/closed_trades` | `logs/*`, attribution logs | Per tab open | Strict cohort eval |
| system_health | `#system_health-tab` | `/api/dashboard/data_integrity`, `/api/telemetry/latest/index` | Logs, state, telemetry index | Per tab open | Multiple file joins |
| executive | `#executive-tab` | `/api/executive_summary` | Closed trade / PnL aggregates | Per tab open | Not strict Alpaca cohort (UI disclaims) |
| sre | `#sre-tab` | `/api/sre/health`, `/api/version`, `/api/versions`, `/api/telemetry/latest/computed?name=bar_health_summary`, `/api/sre/self_heal_events` | SRE + telemetry | 60s active tab | Self-heal ledger DB/log |
| signal_review | `#signal_review-tab` | `/api/signal_history` | `logs/signal_history.jsonl` (typical) | Per tab open | Bot logging |
| failure_points | `#failure_points-tab` | `/api/failure_points` | Readiness checks | 30s active tab | Config + health |
| telemetry | `#telemetry-tab` | `/api/telemetry/latest/index`, `/api/telemetry/latest/computed?...`, `/api/telemetry/latest/health`, `/api/paper-mode-intel-state` | `telemetry/<date>/computed/*.json` | Bundle date = as-of | Extract pipeline |
| learning_readiness | `#learning_readiness-tab` | `/api/learning_readiness` | Exit attribution / readiness | SSR + manual refresh | Telemetry coverage |
| profitability_learning | `#profitability_learning-tab` | `/api/profitability_learning` | Cockpit artifacts | SSR + manual refresh | `update_profitability_cockpit` |
| fast_lane | `#fast_lane-tab` | `/api/stockbot/fast_lane_ledger` | Fast-lane shadow ledger | Per tab open | Shadow runner |

**Additional registered API routes** (not all are separate tabs): `/api/ping`, `/api/telemetry_health`, `/api/governance/status`, `/api/closed_positions`, `/api/pnl/reconcile`, `/api/regime-and-posture`, `/api/scores/*`, `/api/rolling_pnl_5d`, `/api/health_status`, `/sre`, `/api/system/*`, `/api/xai/export`, `/reports/board/<path>`.

**Hard failure rule:** HTTP **404** on any tab-primary endpoint is unacceptable for production; use **200 + explicit `ok`/`error`** for missing optional artifacts (see fix implementation).

---

## Backend availability (local probe, not droplet)

Machine-generated JSON: `reports/ALPACA_DASHBOARD_DATA_SANITY_20260326_1900Z.json` (22/22 endpoints returned **200** with test Basic Auth after fixes).

**Droplet:** Re-run `scripts/dashboard_verify_all_tabs.py` after `git pull` and service restart; artifact `ALPACA_DASHBOARD_DROPLET_PROOF_*.md` is **not yet populated** from this environment.

---

## Defects found in inventory (pre-fix)

1. **SSR placeholders missing from HTML:** `index()` replaced `__BANNER_HTML__`, `__BANNER_SEV__`, `__SITUATION_HTML__` but `DASHBOARD_HTML` contained no placeholders — server-side banner/situation never appeared.
2. **JS never refreshed banner/situation:** `loadDirectionBanner` / `loadSituationStrip` were defined but not called; DOM nodes were missing.
3. **Telemetry computed 404:** Missing `live_vs_shadow_pnl.json` returned **404**, breaking `Promise.all` in the Telemetry tab.
4. **`scripts/dashboard_verify_all_tabs.py` incomplete:** Did not cover many tab endpoints (false sense of safety).
