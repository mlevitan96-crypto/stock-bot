# Alpaca dashboard fix plan (SRE + Quant)

**Artifact ID:** `ALPACA_DASHBOARD_FIX_PLAN_20260326_1900Z`  
**CSA:** Approved dashboard-only items below. No trading logic changes.

---

## P1 — Banner + situation wiring (truth restoration)

| Item | Problem | Minimal fix | Files | Invariant | Rollback | Proof |
|------|---------|-------------|-------|-----------|----------|-------|
| SSR + DOM | Placeholders not in HTML; JS never ran | Add `#direction-banner` / `#situation-strip` with `__BANNER_*__` / `__SITUATION_HTML__`; call loaders on load + 60s | `dashboard.py` | First paint matches API contract; JS refreshes | Revert HTML/CSS/JS block | View source: banner HTML present; Network: `/api/direction_banner` 200 |
| Styles | Unstyled text | Add CSS for banner severity + situation + promo badges | `dashboard.py` | Visual state matches severity | Revert CSS | Screenshot / DOM class `direction-banner info|warning|error|success` |

## P2 — Telemetry computed contract (no tab-breaking 404)

| Item | Problem | Minimal fix | Files | Invariant | Rollback | Proof |
|------|---------|-------------|-------|-----------|----------|-------|
| Missing JSON | 404 broke `Promise.all` | Return **200** with `ok: false`, `error`, `data: null`, `as_of_ts` | `dashboard.py` `api_telemetry_latest_computed` | Never 404 for missing optional artifact | Restore 404 behavior | `truth_probe` + Telemetry tab loads with STALE banner |

## P3 — STALE banner in Telemetry UI

| Item | Problem | Minimal fix | Files | Invariant | Rollback | Proof |
|------|---------|-------------|-------|-----------|----------|-------|
| Silent zeros | Missing LVS JSON looked like healthy zeros | Inject **STALE / INCOMPLETE TELEMETRY** when `ok === false` | `dashboard.py` (telemetry `loadTelemetryContent`) | Operator sees explicit degradation | Remove `staleBanner` block | Manual tab open |

## P4 — Operator tooling

| Item | Problem | Minimal fix | Files | Invariant | Rollback | Proof |
|------|---------|-------------|-------|-----------|----------|-------|
| Verify script | Incomplete endpoint list | Extend `TAB_ENDPOINTS` | `scripts/dashboard_verify_all_tabs.py` | Droplet script matches tab wiring | Revert list | Run on droplet |
| Probe | No machine artifact | Add `scripts/alpaca_dashboard_truth_probe.py` | `scripts/alpaca_dashboard_truth_probe.py` | Reproducible JSON | Delete script | JSON artifact committed |

## P5 — Empty signal copy + ledger fetch

| Item | Problem | Minimal fix | Files | Invariant | Rollback | Proof |
|------|---------|-------------|-------|-----------|----------|-------|
| Signal empty | Looked like failure | Explain `GET /api/signal_history` + typical log path | `dashboard.py` | No unexplained empty | Revert string | UI copy |
| Self-heal ledger | fetch without error handling on non-JSON | `credentials: 'same-origin'`, reject non-OK | `dashboard.py` | Failed load → table error row | Revert fetch | Network 401/500 → error row |

---

## Deferred (needs separate CSA / data pipeline)

- **Top strip** swallowing errors → add explicit **STALE** strip (larger UX change).
- **Direction banner import failure** on Windows dev → runtime must have `src.dashboard` importable (PYTHONPATH/cwd); droplet Linux typically OK.
