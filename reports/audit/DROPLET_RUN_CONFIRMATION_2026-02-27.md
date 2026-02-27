# Droplet run confirmation — 2026-02-27

## What was run and confirmed

### 1. Phase 1 audit (on droplet via DropletClient)

- **Command:** `python scripts/run_phase1_audit_on_droplet.py --out-dir reports/audit`
- **Result:** Success. Outputs written to `reports/audit/PHASE1_DROPLET_RESULTS.md` and `PHASE1_DROPLET_RESULTS.json`.
- **Confirmed on droplet:**
  - **stock-bot.service:** active
  - **uw-flow-daemon.service:** active
  - **Env keys (masked):** SIGNAL_SCORE_BREAKDOWN_LOG, MIN_EXEC_SCORE, TRUTH_ROUTER_*, STOCKBOT_TRUTH_ROOT
  - **Log tail:** Market closed; some exit attempts (PFE, CAT) failed with `close_position_api_once returned None` (market closed).
- **Alpaca alignment:** Snapshot returned `snapshot_failed` (likely env: droplet may use different var names or .env path). `alpaca_alignment_snapshot.py` was updated to try both `ALPACA_KEY`/`ALPACA_SECRET` and `ALPACA_API_KEY`/`ALPACA_API_SECRET`. Re-run Phase 1 after pulling to get alignment.

### 2. Deploy (git pull + pytest_spine + kill stale dashboard + restart)

- **Command:** `DropletClient().deploy()`
- **Result:** Success. Steps: git_pull ✓, pytest_spine ✓ (recorded), kill_stale_dashboard ✓, restart_service ✓.
- **Pytest on droplet:** `No module named pytest` — tests did not run. To run the spine on droplet, install pytest there (e.g. `pip install pytest` in the droplet venv or add to deploy).

### 3. `/api/governance/status`

- **Result:** 404 Not Found when curling from the droplet. Dashboard is up (auth required for other endpoints) but the route is not present in the code currently on the droplet.
- **Cause:** The change that adds `GET /api/governance/status` is in your local repo. The droplet only gets it after you **push** these changes to GitHub and run **deploy** again (so `git pull` brings in the new dashboard).

---

## What you should do next

1. **Push local changes** (giveback fix, entry attribution, dashboard governance endpoint, Phase 1 script, alpaca snapshot, pytest in requirements, deploy pytest step, etc.) to GitHub.
2. **Run deploy again** from this machine:  
   `python -c "from droplet_client import DropletClient; DropletClient().deploy()"`  
   That will pull the new code and restart; then `/api/governance/status` should respond (use dashboard auth when curling).
3. **Re-run Phase 1** after deploy:  
   `python scripts/run_phase1_audit_on_droplet.py`  
   to refresh Alpaca alignment (with the snapshot script fix).
4. **Optional — pytest on droplet:** On the droplet run  
   `pip install pytest`  
   (or add it to your deploy/venv setup) so the deploy step `pytest_spine` actually runs the tests.

---

## Files updated by this run

- `reports/audit/PHASE1_DROPLET_RESULTS.md` — Phase 1 summary (services, env, log tail, Alpaca note).
- `reports/audit/PHASE1_DROPLET_RESULTS.json` — Same as JSON.
- `scripts/alpaca_alignment_snapshot.py` — Env var fallback for key/secret.
- `scripts/curl_governance_status_on_droplet.py` — Helper to curl governance/status with auth (for use after deploy).
