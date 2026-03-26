# Dashboard rationalization — proof (20260325_1900Z)

## STOP-GATE

1. **Plan (restated):** Inventory all dashboard tabs; add a **System Health & Data Integrity** surface computed only from existing telemetry files and documented APIs; remove or merge misleading tabs; make Open/Closed trade views declare sources, freshness, and explicit INCOMPLETE states; add Alpaca strict completeness signaling without changing trading or learning code; record proof + summary.

2. **Failure modes reviewed:** Silent “healthy” when JSON empty; confusing strict vs legacy cohorts; double-counting P&amp;L between Executive and Closed Trades without disclosure; HTML injection from log text; performance hit scanning JSONL on every closed-trades request; forward-reference of `_compute_visibility_matrix` (resolved at runtime — OK).

3. **PLAN_VERDICT: APPROVE** (executed as specified).

---

## Phase 0 — Inventory (TAB → PURPOSE → DATA PATH → STATUS)

| TAB | PURPOSE | DATA PATH | STATUS |
|-----|---------|-----------|--------|
| Positions | Live positions, scores | `GET /api/positions` | VALID |
| Closed Trades | Closed ledger + wheel cols | `GET /api/stockbot/closed_trades` | VALID |
| System Health | Integrity cockpit | `GET /api/dashboard/data_integrity` + `GET /api/telemetry/latest/index` | VALID |
| Executive Summary | Rolling metrics / recent slice | `GET /api/executive_summary` (+ wheel/SRE in full JS) | VALID (banner: not strict cohort) |
| SRE Monitoring | Bot/signal/API health | `/api/sre/health`, `/api/telemetry/latest/computed`, `/api/version` | VALID |
| Wheel Strategy | Wheel P&amp;L / open wheel | `/api/stockbot/wheel_analytics`, `/api/wheel/universe_health` | VALID |
| Strategy Comparison | Equity vs wheel promotion | `/api/strategy/comparison` | VALID |
| Signal Review | Last N signals | `/api/signal_history` | VALID |
| Trading Readiness | Failure points | `/api/failure_points` | VALID |
| Telemetry | Telemetry bundle index + panels | `/api/telemetry/latest/*`, paper intel | VALID |
| Learning &amp; Readiness | Direction replay gate | `/api/learning_readiness`, `state/direction_readiness.json` | VALID |
| Profitability &amp; Learning | CSA / cockpit MD | `/api/profitability_learning` | VALID |
| Fast-Lane | Shadow 25-trade cycles | `/api/stockbot/fast_lane_ledger` | VALID |
| ~~Natural Language Auditor~~ | *(removed)* | `/api/xai/auditor` (API retained, no UI) | STALE → removed |
| ~~Telemetry Health~~ | *(merged)* | `/api/telemetry_health` (API retained) | MERGED → System Health |

`wheel_universe-tab` remains hidden (no nav button); UNKNOWN for operator — acceptable legacy shell.

---

## Phase 1 — Data integrity surface (implementation)

- **Route:** `GET /api/dashboard/data_integrity` → `_build_data_integrity_payload(Path(_DASHBOARD_ROOT))`.
- **Payload:** `generated_at_utc`, `data_sources` map, `alpaca_strict` (full gate dict or null), `alpaca_strict_error`, `kraken_direction_readiness`, `canonical_log_staleness`, `join_coverage_exit_attribution`, `contract_audit_gate`, `temporal_and_structural_flags`, `last_droplet_analysis`.
- **UI:** `window.loadSystemHealth` → `#system_health-content`.

---

## Phase 2 — Prune & merge

- XAI tab + dropdown entry + main/minimal loaders removed.
- Telemetry Health dropdown entry removed; content merged into System Health.

---

## Phase 3 — Trade truth

- **Closed trades:** `entry_timestamp`, `exit_timestamp` (via close `timestamp`), `entry_reason_display`, `close_reason`, `fees_display`, `strict_alpaca_chain`, `data_sources`, API-level `alpaca_strict_summary`.
- **Open positions:** `entry_ts`, `entry_reason_display`, `fees_display`, `strict_alpaca_chain` (explicit N/A for open), `row_data_source`, table footnote.

---

## Phase 4 — Proof & safety

- `python -m py_compile dashboard.py` and `import dashboard` succeed locally.
- `scripts/verify_dashboard_contracts.py` extended with `/api/dashboard/data_integrity` (`generated_at_utc`, `data_sources`).
- Panels show explicit “unavailable” or INCOMPLETE rather than blank success.

---

## Phase 5 — Artifacts

- `reports/DASHBOARD_RATIONALIZATION_PROOF_20260325_1900Z.md` (this file)
- `reports/DASHBOARD_RATIONALIZATION_SUMMARY_20260325_1900Z.md`

---

## Code references (dashboard only)

- New API and helpers: `dashboard.py` — `_canonical_log_status_list`, `_build_data_integrity_payload`, `api_dashboard_data_integrity`, `_strict_alpaca_chain_badge`, `_load_stock_closed_trades` row enrichments, `api_stockbot_closed_trades` summary fields, `_api_positions_impl` position enrichments.
- Frontend: `dashboard.py` embedded HTML/JS — tab `system_health`, `loadSystemHealth`, closed trades table, positions table (18 columns in full `updateDashboard`), executive banner.
