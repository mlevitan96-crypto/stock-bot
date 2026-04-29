## Security Review (push to main)

**Commit / ref:** `da2e512c879831096aa02c21f285a33e271f59a0` (branch `main`)
**Author:** Mark (mlevitan96@gmail.com)
**Date:** 2026-04-29
**Changed files (4):** `uw_flow_ws.py`, `scripts/build_daily_universe.py`, `tests/test_uw_flow_ws.py`, `MEMORY_BANK_ALPACA.md`

---

### Push-Specific Analysis

The commit refactors the Unusual Whales WebSocket client to support Bearer-header authentication (instead of only query-string token), expands the daily universe builder with a 175-name liquid seed and environment-driven extras, and adds test coverage.

**No security findings in the changed files.** Specifically:

- **No hardcoded secrets:** All API tokens flow from environment variables (`UW_API_KEY`, `UW_WS_AUTH_MODE`) or function parameters. Token values are URL-encoded before use.
- **No unsafe code patterns:** No `eval()`, `exec()`, `pickle`, `shell=True`, or user-input-driven deserialization introduced.
- **Secure WebSocket connection:** Uses `wss://` (TLS) exclusively. No `verify=False` or TLS bypass. Proper ping/pong timeouts configured.
- **No HTTP for sensitive endpoints:** All WS connections use `wss://api.unusualwhales.com/socket`.

---

### Full-Tree Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_*.py` | **base64+exec pattern for remote execution** — Multiple droplet-runner scripts encode Python payloads as base64 and execute them on a remote server via `import base64; exec(base64.b64decode(...))`. The payloads are developer-authored (not user input), but this pattern is fragile and reduces auditability. Consider shipping scripts as files and invoking them directly on the droplet. |
| MEDIUM | `scripts/alpaca_canonical_memory_bank_and_edge_mission.py`, `scripts/alpaca_blocker_closure_mission.py`, `scripts/alpaca_rampant_analysis_mission.py`, and ~15 more | **`subprocess.run(cmd, shell=True)`** — Used with hardcoded or developer-composed commands (no user input). Low practical risk but `shell=True` is a code-smell. Where feasible, pass argument lists instead. |
| MEDIUM | `scripts/run_uw_intel_on_droplet.py` (lines 141–176) | **`os.system()` calls** — 13 invocations of `os.system(f"{os.sys.executable} scripts/...")`. Same risk profile as `shell=True`: no user input in arguments, but `subprocess.run` with `check=True` would be more robust. |
| MEDIUM | `requirements.txt` | **Dependency audit recommended** — `urllib3==1.26.20` (pinned for alpaca-trade-api compatibility) should be checked against known CVEs. `flask==3.0.0` and `requests==2.31.0` are current but should be periodically audited with `pip-audit`. No `pip-audit` or `safety` step detected in CI. |
| LOW | `deploy_dashboard_via_ssh.py`, `deploy_dashboard_ssh_direct.py`, `deploy_dashboard_fixes_ssh.py` | **Droplet IP in print statements** — Public IP `104.236.102.57` is hardcoded in user-facing print output. Not a credential leak but reduces operational security. Consider using a hostname or env var. |
| LOW | `force_cycle_run.py` (line 15) | **`exec(f.read())`** — Reads and executes a virtualenv activation script. Standard Python venv pattern, but worth noting. |
| LOW | All `http://127.0.0.1:*` and `http://localhost:*` references | **HTTP on loopback only** — Dozens of references to local dashboard endpoints over HTTP. These are localhost-only and acceptable for internal dashboards behind SSH, but worth flagging for completeness. |

---

### Recommendations

1. **No action required for this push** — the commit is clean.
2. **Add `pip-audit` to CI** — Run `pip-audit -r requirements.txt` in a CI step to catch known dependency CVEs automatically.
3. **Migrate droplet exec scripts from base64+exec to file-based invocation** — Ship helper scripts as tracked files and invoke directly via SSH. This improves auditability and eliminates the fragile base64 encoding pattern.
4. **Replace `os.system()` and `shell=True` with `subprocess.run([...], check=True)`** — Especially in `scripts/run_uw_intel_on_droplet.py`. No immediate security risk, but follows defense-in-depth best practice.
5. **Remove hardcoded droplet IP from print statements** — Use an env var or hostname alias.

---

**Verdict: PASS** — No HIGH or CRITICAL findings. No GitHub issue required.
