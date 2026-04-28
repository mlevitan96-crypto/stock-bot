## Security Review (push to main)

**Commit / ref:** `7f27493a81852aff351433f64d52f22e5900818b`
**Author:** Mark (mlevitan96@gmail.com)
**Message:** fix(alpaca): Alpha11 default flow floor 0.75, fix metadata lock imports
**Date:** 2026-04-28
**Files changed:** `main.py`, `src/alpha11_gate.py`
**Scope:** Full repository tree + commit diff

---

### Pushed Commit Assessment

The commit is **clean from a security perspective**:
- Changes default `ALPHA11_MIN_FLOW_STRENGTH` from 0.90/0.985 to 0.75
- Removes invalid `load_metadata_with_lock` imports (function is already in scope in `main.py`)
- No secrets, no new unsafe patterns, no dependency changes introduced

---

### Findings (Full Repository Scan)

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_*.py` | Remote code execution via `exec(base64.b64decode(...))` pattern — sends base64-encoded Python to droplet for execution. Code is developer-controlled, but the pattern is inherently fragile and would be dangerous if any input were user-influenced. |
| MEDIUM | ~25 files (`check_droplet_trading_now.py`, `scripts/alpaca_*.py`, `run_droplet_*.py`, etc.) | `subprocess.run(..., shell=True)` used extensively for SSH and droplet commands. All inputs appear developer-controlled, but `shell=True` increases blast radius if any string interpolation is compromised. |
| MEDIUM | `scripts/run_uw_intel_on_droplet.py` | `os.system()` called ~12 times with f-string commands. Developer-controlled paths using `os.sys.executable`, but `os.system` does not raise on failure and is less safe than `subprocess.run`. |
| MEDIUM | `requirements.txt` | `requests==2.31.0` — CVE-2024-35195 (cookies leaking on redirect to different host). Fixed in 2.32.0. Not exploitable in this codebase's usage pattern (no cross-domain cookie-sensitive redirects), but should be updated. |
| MEDIUM | `deploy_dashboard_ssh_direct.py`, `deploy_dashboard_fixes_ssh.py`, `deploy_dashboard_via_ssh.py` | Dashboard URLs printed/accessed over plain HTTP on public IP `104.236.102.57:5000`. Dashboard should be behind TLS or firewall/VPN for production. |
| LOW | `complete_droplet_verification.py:85` | `exec(import_stmt)` for import testing — controlled strings, minimal risk. |
| LOW | `force_cycle_run.py:15` | `exec(f.read(), ...)` for virtualenv activation — standard Python venv pattern. |
| LOW | `unusual_whales_api/api_spec.yaml:11937,15207` | Placeholder tokens (`Bearer abc123`, `Bearer YOUR_TOKEN`) in API spec examples — not real credentials, documentation only. |
| LOW | 7+ Python files | Hardcoded infrastructure IP `104.236.102.57` — consider centralizing to config/env to reduce drift risk. |

---

### What Was NOT Found (Positive)

- **No hardcoded API keys or secrets** — all credential access uses `os.getenv()` or `Config.*` references
- **`.env` is properly gitignored** (`.gitignore` contains `.env` and `*.env`)
- **No `verify=False`** (TLS certificate verification) anywhere in the codebase
- **No `pickle.load`** or unsafe deserialization
- **No `yaml.load` without Loader**
- **No SQL injection patterns** (no SQL string concatenation)
- **All `requests.*` calls have `timeout=` set** — no missing timeout risk
- **HTTP usage is localhost/loopback only** for health checks (acceptable)

---

### Recommendations

1. **Dependency update (MEDIUM priority):** Bump `requests` from 2.31.0 to >=2.32.0 to resolve CVE-2024-35195. Run `pip-audit` in CI for ongoing vulnerability detection.
2. **Remote exec pattern (MEDIUM priority):** Consider replacing the `exec(base64.b64decode(...))` pattern in droplet scripts with a proper script deployment mechanism (e.g., `scp` + `python script.py`) to reduce code injection surface area.
3. **shell=True reduction (LOW priority):** Where feasible, prefer `subprocess.run(["cmd", "arg1", ...])` list form over `shell=True` string form to prevent shell injection if command strings ever incorporate external input.
4. **os.system replacement (LOW priority):** Replace `os.system()` calls in `scripts/run_uw_intel_on_droplet.py` with `subprocess.run()` for better error handling and security.
5. **Dashboard TLS (ops-level):** Ensure production dashboard at `104.236.102.57:5000` is behind a reverse proxy with TLS or restricted via firewall rules.
6. **Centralize infrastructure config (LOW):** Move hardcoded droplet IP to an env var or config constant.

---

### Verdict

**No CRITICAL or HIGH findings.** No GitHub issue required. The pushed commit (`7f27493a`) introduces no security regressions. The repository-wide MEDIUM findings are pre-existing best-practice items tracked above for future hardening.
