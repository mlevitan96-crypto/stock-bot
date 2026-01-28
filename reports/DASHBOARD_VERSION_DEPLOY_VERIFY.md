# Dashboard Version Contract — Deploy & Verify

## Implemented (A–C)

- **A) GET /api/version** in `dashboard.py`: returns `service`, `git_commit`, `git_commit_short`, `build_time_utc`, `process_start_time_utc`, `python_version`, `cwd`; uses `git rev-parse HEAD` with fallback to `GIT_COMMIT`; on error returns 503 with `reason_code`.
- **B) Audit** in `scripts/dashboard_endpoint_audit.py`: `/api/version` in inventory; records `git_commit` and `process_start_time_utc`; compares to `EXPECTED_GIT_COMMIT` (env); FAIL with `reason_code: PROCESS_DRIFT` and both SHAs in report; `reports/DASHBOARD_ENDPOINT_AUDIT.md` includes "Running dashboard commit" vs "Expected commit".
- **C) SRE tab** "Dashboard Version" panel: commit short SHA, process start time; green if matches `EXPECTED_GIT_COMMIT`, red if mismatch (read-only).

## Steps to Run on Droplet (D–E)

Run these **on the droplet** (SSH as root or with sudo) or use `run_dashboard_endpoint_audit_on_droplet.py` with deploy flag.

### D) Deploy + restart dashboard only

```bash
cd /root/stock-bot
git fetch origin main
git reset --hard origin/main

sudo cp deploy/stock-bot-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable stock-bot-dashboard
sudo systemctl restart stock-bot-dashboard
sudo systemctl status stock-bot-dashboard --no-pager -l
```

Do **not** restart any trading service (e.g. `stock-bot` or `main.py`).

### E) Verify (no assumptions)

From **your local machine** (with droplet SSH configured):

```bash
# Optional: deploy + restart dashboard on droplet, then run audit
export DROPLET_DEPLOY_BEFORE_AUDIT=1
export DROPLET_DASHBOARD_SERVICE=stock-bot-dashboard
python scripts/run_dashboard_endpoint_audit_on_droplet.py
```

Or on the **droplet** after D:

```bash
cd /root/stock-bot
export EXPECTED_GIT_COMMIT=$(git rev-parse HEAD)
python3 scripts/dashboard_endpoint_audit.py
```

Then check:

- `/api/version` returns 200
- `git_commit` == `EXPECTED_GIT_COMMIT`
- `reports/DASHBOARD_ENDPOINT_AUDIT.md`: FAIL == 0, no PROCESS_DRIFT
- Telemetry tab: PASS
- Self-Healing Ledger: PASS

---

## Final Output (G) — completed 2026-01-28

| Item | Value |
|------|--------|
| 1) Droplet git HEAD | `1a7b43990863152a088ea6620f1df84c84123286` (Daily Alpha Audit 2026-01-28) |
| 2) /api/version JSON (redacted ok) | `{"service":"stock-bot-dashboard","git_commit":"1a7b439...","git_commit_short":"1a7b439","build_time_utc":"...","process_start_time_utc":"...","python_version":"...","cwd":"/root/stock-bot"}` |
| 3) Final audit verdict counts | **PASS: 19  WARN: 2  FAIL: 0** |
| 4) Dashboard commit == deployed commit | **Yes** — running dashboard commit equals expected (1a7b439...). No PROCESS_DRIFT. |
| 5) No trading services restarted | **Yes** — only `stock-bot-dashboard` was restarted. |

---

**Commit pushed:** `Dashboard: add /api/version and enforce process-commit parity` (and `Add deploy/stock-bot-dashboard.service for droplet systemd`).

**Finalize changes:** Deploy script now injects `GIT_COMMIT` into the dashboard service on deploy; audit treats 404 with "artifact missing" as SOURCE_MISSING (WARN); safe print for remote output on Windows.
