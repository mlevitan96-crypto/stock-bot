# Monday Open Readiness — BLOCKERS

**Generated (UTC):** 2026-03-08T21:41:02.592336+00:00

## Root cause

stock-bot service not active.

## Exact remediation

- Start stock-bot on droplet: sudo systemctl start stock-bot

## Re-run after fix

python scripts/audit/run_monday_open_readiness.py

Do not proceed to trading until blockers are resolved and suite is re-run.