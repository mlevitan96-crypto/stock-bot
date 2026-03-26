# Alpaca dashboard — `dashboard_verify_all_tabs.py` (Phase 3)

**Timestamp:** `20260327_0100Z`  
**Environment:** Cursor agent workspace; **not** Alpaca droplet.

## Verdict

**NOT EXECUTED ON DROPLET — BLOCKED**

## Blocker

- Authenticated verifier must run **on the droplet** (or against the droplet’s reachable `DASHBOARD_BASE_URL`) with `DASHBOARD_USER` / `DASHBOARD_PASS` from `.env`.
- This agent has **no** network path to that host from the workspace.

## Script enhancement (repo)

`scripts/dashboard_verify_all_tabs.py` now supports machine-readable output:

```bash
cd /root/stock-bot
set -a && source .env && set +a
export DASHBOARD_BASE_URL="${DASHBOARD_BASE_URL:-http://127.0.0.1:5000}"
python3 -u scripts/dashboard_verify_all_tabs.py --json-out reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_<TS>.json
echo "exit_code=$?"
```

Replace `<TS>` with your run timestamp; commit stdout + JSON + exit code.

## Workspace sanity (non-droplet)

- `curl.exe -m 3 http://127.0.0.1:5000/api/ping` from this workspace → **connection refused** (no local listener).  
- This does **not** assert droplet health; it only shows the verifier cannot be validated here against a live server.
