## Security Review (push to main)

**Commit / ref:** `b4859e885a3e1555ce34dfc4ac573599ef34c140`
**Message:** fix(alpaca): expand wheel to macro ETFs and fix root cause of options pricing API fetch
**Pushed by:** mlevitan96-crypto
**Reviewed:** 2026-05-04T15:52Z (automated scan)

---

### Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py` | `exec(base64.b64decode(...))` pattern used to run local repo scripts on the droplet via SSH. The decoded payload originates from tracked repo files (not user input), reducing exploitation risk. However, any repo compromise could inject arbitrary code into the execution path. |
| MEDIUM | `comprehensive_no_positions_investigation.py:16`, `scripts/audit/run_exec_mode_*.py`, `scripts/alpaca_*.py` | `subprocess.run(cmd, shell=True, ...)` with hardcoded/operator-controlled command strings. No user-supplied input is interpolated into these commands. Risk is limited to operator misuse or repo compromise. |
| LOW | `check_positions_simple.py:7` | `Config.ALPACA_KEY` / `Config.ALPACA_SECRET` passed directly from environment-backed Config class. No secret leak, but the script lacks `.env` guard—running outside the intended env could produce confusing errors. |
| LOW | `requirements.txt` | `flask==3.0.0` — consider updating (known medium-severity CVEs in older Flask releases). `paramiko==3.4.0` — check for known advisory updates. `requests==2.31.0` — generally stable but newer patch releases available. Recommend running `pip-audit` in CI. |
| LOW | `deploy_to_droplet.py:104`, `RESTART_DASHBOARD_AND_VERIFY.py:166` | Instructions reference `http://` URLs for local dashboard access (localhost/droplet). Acceptable for private network tooling but not for public endpoints. |

---

### Scan Summary

| Category | Result |
|----------|--------|
| Hardcoded secrets / API keys | **PASS** — No hardcoded secrets found. All credentials sourced from `os.getenv()` or env-backed Config class. No `.env` files committed. |
| Private keys / certificates | **PASS** — No PEM files or private key material in tracked files. |
| `verify=False` / disabled TLS | **PASS** — Not present in any Python source. |
| Request timeouts | **PASS** — All `requests.*()` calls include explicit `timeout=` parameter. |
| YAML deserialization | **PASS** — All usage is `yaml.safe_load()`. |
| Pickle / unsafe deserialization | **PASS** — No `pickle.loads()` or `pickle.load()` found. |
| SQL injection / string concat | **PASS** — No raw SQL detected. |
| Path traversal | **PASS** — No dynamic path construction from user input found. |

---

### Changed Files in This Push

| File | Security Notes |
|------|---------------|
| `scripts/diagnostic_options_pricing.py` (new) | Clean. Uses env vars for credentials, explicit timeouts on all requests, no shell commands. |
| `src/options_engine.py` | Clean. No new unsafe patterns. All UW HTTP calls have cache policies and existing uw_client timeout handling. |
| `strategies/wheel_strategy.py` | Clean. New `_fetch_alpaca_option_quote_via_data_rest` uses env vars, has `timeout=20`, no shell. |
| `strategies/wheel_universe_selector.py` | Minimal change (4 lines). No new security surface. |
| `tests/test_options_wheel_engine.py` | Test file. No security concerns. |

---

### Recommendations

1. **CI dependency audit**: Add `pip-audit` to CI pipeline to catch known CVEs in pinned dependencies (Flask, paramiko, requests, urllib3).
2. **Base64 exec pattern**: Consider replacing the `exec(base64.b64decode(...))` droplet runner pattern with a more auditable approach (e.g., `scp` + `python script.py`) to make code review easier and reduce the attack surface if repo files are ever tampered with.
3. **Subprocess shell=True**: While currently safe (hardcoded commands), prefer `shell=False` with explicit argument lists where possible to eliminate injection surface entirely.
4. **No action required for this push**: The changed files introduce no new security risks.

---

**Verdict: PASS — No HIGH or CRITICAL findings. No issue opened.**
