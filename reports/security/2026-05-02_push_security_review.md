## Security Review (push to main)

**Commit / ref:** `520e3be94fc8d31cb8862819480d206781dfd2d1`  
**Message:** `feat: OPA dashboard integration and risk-engine hardening`  
**Pushed by:** mlevitan96-crypto  
**Review date:** 2026-05-02T02:00:00Z  

---

### Push Commit Files Scanned (12 files, +813 lines)

| File | Status |
|------|--------|
| `config/registry.py` | CLEAN |
| `config/strategies.yaml` | CLEAN |
| `dashboard.py` | CLEAN (new endpoint) |
| `deploy/systemd/wheel-broker-reconcile.service` | CLEAN |
| `deploy/systemd/wheel-broker-reconcile.timer` | CLEAN |
| `scripts/wheel_broker_reconcile.py` | CLEAN |
| `src/wheel_dashboard_sink.py` | CLEAN |
| `src/wheel_manager.py` | CLEAN |
| `src/wheel_risk_gates.py` | CLEAN |
| `strategies/wheel_strategy.py` | CLEAN |
| `tests/test_wheel_dashboard_sink.py` | CLEAN |
| `tests/test_wheel_risk_gates.py` | CLEAN |

---

### Findings

| Severity | Location | Description |
|----------|----------|-------------|
| CLEAN | Push commit (520e3be9) | **No secrets, unsafe patterns, or insecure network calls in the pushed code.** All credentials sourced from env vars via `os.getenv()`. API requests use HTTPS with timeouts. |
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py` (pre-existing) | Multiple scripts use `exec(base64.b64decode(...))` to run payloads on remote droplet via SSH. The payloads are generated from local source files, not from external/user input. Risk: code injection if payload generation is compromised. |
| MEDIUM | `deploy_dashboard_fixes_ssh.py`, `deploy_dashboard_via_ssh.py`, `deploy_dashboard_ssh_direct.py` (pre-existing) | Dashboard exposed externally at `http://104.236.102.57:5000/` over plain HTTP. While Basic Auth is enforced, credentials are transmitted without TLS encryption on the public internet. |
| LOW | Multiple scripts (pre-existing) | `subprocess.run(..., shell=True)` used in ~20 diagnostic/audit scripts. All commands are hardcoded strings (not user input), but `shell=True` is a defense-in-depth concern. |
| LOW | `force_cycle_run.py` (pre-existing) | `exec(f.read())` used to activate virtualenv. The path is hardcoded to a local file (`/root/stock-bot/venv/bin/activate_this.py`), so exploitation requires filesystem access. |
| LOW | `scripts/run_uw_intel_on_droplet.py` (pre-existing) | Multiple `os.system()` calls with f-string interpolation. Arguments are internally generated (dates, flags), not from external input. |

---

### Positive Security Observations

- **No hardcoded secrets found.** All API keys (Alpaca, UW, Dashboard) are loaded from environment variables or `.env` files.
- **`.env` is properly gitignored** (`.gitignore` contains `.env` and `*.env`).
- **No `verify=False`** (TLS cert bypass) found anywhere in the codebase.
- **No pickle deserialization** of untrusted data.
- **No SQL string concatenation** (no SQL database used).
- **API requests include timeouts** (15s for Alpaca options API, 10s for UW client, 2s for localhost health checks).
- **Dashboard enforces HTTP Basic Auth** with fail-closed behavior when credentials are missing.
- **New wheel code (this push) follows secure patterns:** env-based credentials, timeouts on all HTTP calls, no `eval`/`exec`, proper error handling.

---

### Recommendations

1. **[MEDIUM] Enable TLS for external dashboard access.** The dashboard at `104.236.102.57:5000` transmits Basic Auth credentials over unencrypted HTTP. Deploy behind a reverse proxy (nginx/caddy) with TLS, or use a firewall + SSH tunnel for access.
2. **[LOW] Audit `exec(base64.b64decode(...))` SSH payload pattern.** While currently safe (payloads from local files), this pattern is fragile. Consider using `scp` + direct script execution instead of base64-encoded `exec()`.
3. **[LOW] Replace `shell=True` with explicit argument lists** in diagnostic scripts where feasible, to reduce injection surface if future changes introduce variable inputs.
4. **[LOW] Run `pip-audit` in CI** to monitor Python dependency vulnerabilities (not currently configured).

---

### Verdict

**No HIGH or CRITICAL findings.** The pushed commit (520e3be9) introduces no security regressions. Pre-existing MEDIUM findings are documented above for tracking. No GitHub issue required.
