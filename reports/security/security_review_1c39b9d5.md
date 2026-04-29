## Security Review (push to main)

**Commit / ref:** `1c39b9d56d157473b6608a7d462ec6500ec419e4` — `feat(uw): 50k/day REST cap, RTH quota throttle, Spot GEX spine`  
**Pushed by:** mlevitan96-crypto  
**Date:** 2026-04-29  
**Changed files (8):** `MEMORY_BANK_ALPACA.md`, `config/registry.py`, `scripts/alpaca_ml_multi_signal.py`, `src/uw/uw_client.py`, `tests/test_uw_quota_and_spot_gex.py`, `uw_composite_v2.py`, `uw_enrichment_v2.py`, `uw_flow_daemon.py`

---

### Findings

| Severity | Location | Description |
|----------|----------|-------------|
| CLEAN | Changed files (all 8) | **No hardcoded secrets or credential leaks.** All API keys/secrets are read from environment variables via `os.getenv()`. No `.env` file committed. |
| CLEAN | Changed files (all 8) | **No new unsafe patterns.** No `eval()`, `exec()`, `pickle.loads()`, `shell=True`, or SQL string concatenation introduced in this push. |
| CLEAN | Changed files (all 8) | **No insecure network calls.** No `verify=False`. All `requests.get()` calls include `timeout` parameters. UW API base URL defaults to HTTPS. |
| CLEAN | `requirements.txt` | **No dependency changes** in this push. |
| LOW | `src/uw/uw_client.py` | `uw_client.py` line 128: URL prefix check for `http://` — this is normalization logic (not an HTTP call); acceptable. |
| LOW | Repo-wide (pre-existing) | `requests==2.31.0`, `urllib3==1.26.20` — recommend periodic `pip-audit` in CI to catch future CVEs. |

### Pre-existing patterns (not introduced in this push, noted for awareness)

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_*.py` | `exec(base64.b64decode(...))` used for remote droplet script execution over SSH. Controlled internal use; not user-input-driven. |
| MEDIUM | `scripts/alpaca_rampant_analysis_mission.py`, `scripts/alpaca_blocker_closure_mission.py`, and ~10 other scripts | `subprocess.run(..., shell=True)` with internally constructed commands. Not user-input-driven but could be hardened with `shell=False`. |
| MEDIUM | Multiple diagnostic/dashboard scripts | `http://127.0.0.1:5000` — localhost-only health check endpoints. Acceptable for internal use. |
| LOW | `deploy_dashboard_ssh_direct.py`, `deploy_dashboard_fixes_ssh.py` | Hardcoded droplet IP `104.236.102.57` in print statements. Not a credential but should be parameterized. |
| LOW | `force_cycle_run.py` | `exec(f.read(), {'__file__': activate_this})` for venv activation — known pattern, low risk in controlled environment. |

### Recommendations

1. **No action required for this push.** All changed files pass security review cleanly.
2. **CI improvement (backlog):** Add `pip-audit` to CI pipeline to catch dependency CVEs automatically.
3. **Backlog hardening:** Consider replacing `shell=True` patterns in diagnostic scripts with explicit argument lists where feasible.
4. **Backlog hardening:** Parameterize hardcoded droplet IPs in deployment scripts.

### Verdict

**PASS** — No HIGH or CRITICAL findings. No GitHub issue opened.
