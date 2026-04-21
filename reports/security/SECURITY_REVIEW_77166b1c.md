# Security Review (push to main)

**Commit / ref:** `77166b1cbbf6c7cf3eca0ee440a82ac47a2735d3`
**Message:** `fix(telemetry): JSON-safe UW attribution and toxicity fields; regime stub with hysteresis; quarantine reset intent`
**Pushed by:** mlevitan96-crypto
**Date:** 2026-04-21
**Changed files:** `config/strict_completeness_quarantine.json`, `main.py`, `src/alpha11_gate.py`, `src/regime/__init__.py`, `src/regime/continuous_regime_classifier.py`, `telemetry/score_telemetry.py`, `uw_composite_v2.py`

---

## Findings

### Changed Files (this push)

No security issues found in the files changed by this push. The changed files involve:
- Regime classification logic (pure computation, no I/O or auth)
- Telemetry scoring (local JSON file read/write, no network)
- Alpha 11 gate (env-var config, no secrets)
- Quarantine config (static JSON)

All credential access in `main.py` continues to use `os.getenv()` / `get_alpaca_trading_credentials()` (env-var based, no hardcoded secrets).

---

### Full Repository Scan

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `requirements.txt` — `requests==2.31.0` | `requests` 2.31.0 has two known medium-severity CVEs: **CVE-2024-35195** (cert verification bypass in Session after `verify=False`, CVSS 5.6) and **CVE-2024-35196** (`.netrc` credential leak via crafted URL). Fixed in `requests>=2.32.4`. |
| MEDIUM | `requirements.txt` — `urllib3==1.26.20` | `urllib3` 1.x is end-of-life; the 2.x series is current. While 1.26.20 has no critical CVEs, staying on an EOL branch means slower security patches. |
| MEDIUM | Multiple scripts in `reports/_daily_review_tools/`, `scripts/governance/` | Pattern: `exec(base64.b64decode(...))` used to run local Python scripts on the droplet via SSH. The base64 payloads are built from local files (not user input), so this is not RCE from external input, but the pattern is fragile — any future change that accepts external input into these payloads would be critical. |
| MEDIUM | `complete_droplet_verification.py:85` | `exec(import_stmt)` with hardcoded strings. Not exploitable as-is (strings are compile-time constants), but `exec` should be replaced with `importlib.import_module()`. |
| MEDIUM | `force_cycle_run.py:15` | `exec(f.read(), ...)` to activate virtualenv. Standard Python venv bootstrap pattern but could be replaced with subprocess activation. |
| LOW | ~20 files (diagnostic/deploy scripts) | `subprocess.run(..., shell=True)` with string commands. Commands are locally constructed (no user/external input injection), but `shell=True` is a code-smell. Prefer `shell=False` with argument lists where feasible. |
| LOW | `dashboard.py`, `sre_monitoring.py`, `harden_xai_system.py`, etc. | HTTP (not HTTPS) used for `localhost` / `127.0.0.1` health checks and internal API calls. Acceptable for loopback-only traffic, but note that `dashboard.py:2614` fetches `http://localhost:8081/api/cockpit` from client-side JavaScript, which would fail or leak if the dashboard is exposed without a reverse proxy enforcing HTTPS. |
| LOW | `deploy_dashboard_via_ssh.py`, `deploy_dashboard_ssh_direct.py`, etc. | Hardcoded droplet IP `104.236.102.57` in print statements and curl commands. Not a secret leak (public IP), but centralizing this into config would reduce drift. |

---

### Categories with No Findings

- **Hardcoded secrets / API keys / tokens / private keys:** None found. All credentials are loaded from environment variables (`.env` is gitignored). No `.pem` files, no `PRIVATE KEY` blocks, no hardcoded bearer tokens in source.
- **SQL injection:** No SQL usage detected in the codebase.
- **Unsafe deserialization:** No `pickle.load`, `yaml.unsafe_load`, or `marshal.load` found.
- **Disabled TLS verification:** No `verify=False` or `NODE_TLS_REJECT_UNAUTHORIZED=0` found.
- **Missing timeouts on network calls:** All `requests.get`/`requests.post` calls reviewed have explicit `timeout=` parameters.

---

## Recommendations

1. **Upgrade `requests` to `>=2.32.4`** — Resolves CVE-2024-35195 and CVE-2024-35196. Verify compatibility with `alpaca-trade-api==3.2.0` (which pins `urllib3<2`). Consider upgrading `urllib3` to 2.x simultaneously if the Alpaca SDK supports it.

2. **Replace `exec()` with `importlib`** in `complete_droplet_verification.py` for import testing. Use `importlib.import_module(name)` instead of `exec(import_stmt)`.

3. **Audit `base64 + exec` droplet scripts** — While currently safe (payloads are local file content), add a comment/assertion documenting that the base64 source is trusted. Consider switching to `scp` + `python script.py` instead of inline exec.

4. **Add `pip-audit` to CI** — Automate dependency vulnerability scanning on every push/PR.

5. **Prefer `shell=False`** in `subprocess.run` calls where the command can be expressed as an argument list.

---

## Verdict

**No CRITICAL or HIGH findings.** All findings are MEDIUM (dependency CVEs, `exec` patterns with trusted input) or LOW (best-practice suggestions). No GitHub issue required for this push.
