# Alpaca dashboard — droplet proof closeout (STOP-GATE)

**Timestamp:** `20260327_0100Z`

## Update (20260326 droplet run)

**Superseded.** Executed proof: `ALPACA_DASHBOARD_DROPLET_PROOF_20260326_1815Z` — verifier **23/23**, verdict **DASHBOARD_TRUTH_RESTORED** in `ALPACA_DASHBOARD_UI_CLOSEOUT_20260326_1815Z.md`.

---

## Original CSA verdict (workspace-only): **BLOCKED**

Droplet Phases 0–5 were **not** completed from the Cursor agent environment because there is **no** deterministic remote execution path to `/root/stock-bot` (no SSH host, no keys, no forwarded `DASHBOARD_BASE_URL` to production).

## Single blocker list

| # | Blocker | Exact failure mode |
|---|---------|-------------------|
| 1 | **No droplet shell** | Cannot run `systemctl list-units …`, `git reset`, `systemctl restart`, `journalctl`, or browser/screenshot capture against the Alpaca host. |
| 2 | **No live dashboard endpoint from workspace** | `curl.exe -m 3 http://127.0.0.1:5000/api/ping` → connection refused (`http_code=000`) on agent loopback only; **not** a droplet test. |
| 3 | **Verifier not run against production** | `scripts/dashboard_verify_all_tabs.py` was **not** executed on the droplet with production auth; see `reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_20260327_0100Z.json` (`executed_on_droplet: false`). |

## Minimal fix required (operator)

1. SSH to droplet; run Phase 0 discovery commands; record **actual** unit name(s).  
2. `git fetch` / `git reset --hard origin/main`; record commit SHA.  
3. `systemctl restart <unit>`; capture `systemctl status` + `journalctl -n 300`.  
4. `set -a && source .env && python3 -u scripts/dashboard_verify_all_tabs.py --json-out reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_<NEW_TS>.json` — must exit `0` with **23/23** HTTP 200.  
5. Capture authenticated `curl` JSON for endpoints listed in `reports/audit/ALPACA_DASHBOARD_HTTP_TRACES_20260327_0100Z.md`.  
6. Save screenshots under `reports/screenshots/alpaca_dashboard_<NEW_TS>/`.  
7. Commit artifacts; add `reports/audit/ALPACA_DASHBOARD_UI_CLOSEOUT_<NEW_TS>.md` with **DASHBOARD_TRUTH_RESTORED**.

## If any tab fails after droplet run

**STOP.** Do not claim restore. One markdown table: tab → endpoint → HTTP status → body snippet (≤500 chars) → minimal UI-only fix.

## References

- Prior UI closeout: `reports/audit/ALPACA_DASHBOARD_UI_CLOSEOUT_20260326_2200Z.md`  
- This proof bundle: `reports/audit/ALPACA_DASHBOARD_DROPLET_PROOF_20260327_0100Z.md` / `reports/ALPACA_DASHBOARD_DROPLET_PROOF_20260327_0100Z.json`
