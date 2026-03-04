# Learning Tab Triage

**Triage time (UTC):** (run `python scripts/audit/run_learning_tab_triage_on_droplet.py` on droplet or via SSH to fill)

## Purpose

Identify exact failure mode for Learning & Readiness tab: 404, 401/403, 500, or 200 with invalid/wrong shape.

## Endpoints

- `/api/learning_readiness` — MUST return 200 with JSON `ok`, `run_ts`, `deployed_commit`, `telemetry_trades`, `visibility_matrix`, `error`
- `/api/telemetry_health` — unauthenticated GET allowed
- `/api/situation` — unauthenticated GET allowed

## Evidence

(Run triage script; output appended below or in separate run.)

## Failure mode checklist

- [ ] 404 — route missing (dashboard code not deployed or wrong route)
- [ ] 401/403 — auth blocking (allow list or creds)
- [ ] 500 — uncaught exception (check logs/dashboard_learning_readiness.log)
- [ ] 200 but invalid JSON / wrong shape — frontend parse or render fails

## Remediation

- Backend: API wrapped in try/except, always 200, safe payload with error_code; logging to dashboard_learning_readiness.log.
- Frontend: Never blank; ERROR/DEGRADED state with message; matrix supports field/present/total/pct.
