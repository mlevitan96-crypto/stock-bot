# Alpaca dashboard UI — CSA closeout (droplet proof complete)

**Timestamp:** 20260326_1815Z

## Verdict: **DASHBOARD_TRUTH_RESTORED**

**Hard gate:** `python3 -u scripts/dashboard_verify_all_tabs.py --json-out …` exited **0** with **23/23** HTTP **200** on the Alpaca droplet (`reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_20260326_1815Z.json`, `all_pass`: true).

**Evidence bundle:** `reports/audit/ALPACA_DASHBOARD_DROPLET_PROOF_20260326_1815Z.md` / `reports/ALPACA_DASHBOARD_DROPLET_PROOF_20260326_1815Z.json` (`executed`: true).

**Operational disclaimer** (exact CSA line) confirmed in live JSON: *“Trades are executing on Alpaca. Data is NOT certified for learning or attribution.”* (`reports/ALPACA_DASHBOARD_HTTP_TRACES_20260326_1815Z.json`).

**Screenshots:** `reports/screenshots/alpaca_dashboard_20260326_1815Z/` (see index).

## Deploy note

`origin/main` at reset lacked `/api/alpaca_operational_activity`; **hotfix** via `scp` of `dashboard.py` + full verifier from workspace (documented in deploy artifact). **Push** these commits to `main` so the next bare `git reset --hard origin/main` preserves the gate.
