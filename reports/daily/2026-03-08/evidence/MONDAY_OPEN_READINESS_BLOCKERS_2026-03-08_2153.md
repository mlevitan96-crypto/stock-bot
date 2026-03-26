# Monday Open Readiness — BLOCKERS

**Generated (UTC):** 2026-03-08T21:53:21.836869+00:00

## Root cause

Alpaca paper API unreachable or auth failed.

## Exact remediation

- Check network and paper API keys on droplet.

## Re-run after fix

python scripts/audit/run_monday_open_readiness.py

Do not proceed to trading until blockers are resolved and suite is re-run.