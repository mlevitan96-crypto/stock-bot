# Dashboard Telemetry Diagnosis

**Generated:** 2026-02-13T02:00:20.520265+00:00

---

## Telemetry tab endpoints

- **/api/telemetry/latest/index**: PASS — OK — 
- **/api/telemetry/latest/computed**: WARN — SOURCE_MISSING — HTTP Error 404: NOT FOUND
  Excerpt: {"error":"computed artifact missing: live_vs_shadow_pnl.json","latest_date":"2026-02-12"}
...
- **/api/telemetry/latest/health**: PASS — OK — 
- Evidence: Latest 2026-02-12, computed artifacts: 11.

## Root cause classification

1. UI calling wrong endpoint — check frontend fetch URLs.
2. Backend reading wrong file/log — check dashboard.py route handlers.
3. Schema mismatch causing UI to drop — check expected_schema vs response.
4. Data filtered out (time/symbol) — check query params and backend filters.
5. Data not produced (artifact missing) — check telemetry pipeline / reports.