# Dashboard Telemetry Diagnosis

**Generated:** 2026-01-29T02:00:17.209577+00:00

---

## Telemetry tab endpoints

- **/api/telemetry/latest/index**: PASS — OK — 
- **/api/telemetry/latest/computed**: PASS — OK — 
- **/api/telemetry/latest/health**: PASS — OK — 
- Evidence: Latest 2026-01-28, computed artifacts: 20.

## Root cause classification

1. UI calling wrong endpoint — check frontend fetch URLs.
2. Backend reading wrong file/log — check dashboard.py route handlers.
3. Schema mismatch causing UI to drop — check expected_schema vs response.
4. Data filtered out (time/symbol) — check query params and backend filters.
5. Data not produced (artifact missing) — check telemetry pipeline / reports.