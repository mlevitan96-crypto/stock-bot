# Dashboard Endpoint Audit

**Generated:** 2026-01-28T20:49:05.152771+00:00 (UTC)
**Base URL:** http://127.0.0.1:5000

---

## Version / commit parity

- **Running dashboard commit:** 10699bf6cc2e86667730ca1e54426bcc7ac0eb6a
- **Expected commit:** 10699bf6cc2e86667730ca1e54426bcc7ac0eb6a

---

## Summary

| Result | Count |
|--------|-------|
| PASS | 19 |
| WARN | 2 |
| FAIL | 0 |

| Panel / Endpoint | Result | reason_code | Freshness | Notes |
|------------------|--------|-------------|-----------|-------|
| Positions / Positions stats + table | PASS | OK | unknown |  |
| Positions / Positions stats + table | PASS | OK | fresh (age_sec=0.0) |  |
| Signal Review / Signal history (last 50) | PASS | OK | unknown |  |
| SRE Monitoring / SRE health + funnel + ledger | WARN | EMPTY_DATA | stale (age_sec=3600.0) | sre_health_timeout |
| SRE Monitoring / SRE health + funnel + ledger | PASS | OK | unknown | empty events list (allowed) |
| Executive Summary / Executive summary | PASS | OK | fresh (age_sec=3600.0) |  |
| Natural Language Auditor (XAI) / XAI auditor | PASS | OK | unknown |  |
| Natural Language Auditor (XAI) / XAI auditor | PASS | OK |  |  |
| Trading Readiness / Failure points | PASS | OK | unknown |  |
| Telemetry / Telemetry latest index + computed + health | PASS | OK | fresh (age_sec=3600.0) |  |
| Telemetry / Telemetry latest index + computed + health | WARN | SOURCE_MISSING |  | HTTP Error 404: NOT FOUND |
| Telemetry / Telemetry latest index + computed + health | PASS | OK | fresh (age_sec=3600.0) |  |
|  / /api/system-events | PASS | OK |  |  |
|  / /api/regime-and-posture | PASS | OK |  |  |
|  / /api/scores/distribution | PASS | OK |  |  |
|  / /api/scores/components | PASS | OK |  |  |
|  / /api/scores/telemetry | PASS | OK |  |  |
|  / /api/closed_positions | PASS | OK |  |  |
|  / /api/pnl/reconcile | PASS | OK |  |  |
|  / /health | PASS | OK |  |  |
|  / /api/version | PASS | OK |  |  |

## Failing endpoints (detail)
