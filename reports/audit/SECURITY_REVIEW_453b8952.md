# Security Review (push to main)

**Commit / ref:** `453b8952d9c40ea3a49bfb04deec208b2a82a02c`  
**Message:** `feat: offensive pivot - inversion engine, profit ladders, removed streak shield`  
**Pushed by:** mlevitan96-crypto  
**Scan date:** 2026-05-01T22:19Z  

## Changed Files in Push

| File | Status |
|------|--------|
| `config/alpaca_risk_profile.json` | CLEAN |
| `main.py` | CLEAN |
| `src/alpaca/flow_toxicity_gate.py` | CLEAN |
| `src/ml/alpaca_inversion_engine.py` | CLEAN |
| `src/offense/streak_breaker.py` | CLEAN |
| `src/uw/uw_client.py` | CLEAN |
| `tests/test_alpaca_inversion_engine.py` | CLEAN |
| `tests/test_flow_toxicity_gate.py` | CLEAN |
| `tests/test_streak_breaker_env.py` | CLEAN |
| `tests/test_strict_completeness_live_entry_decision_made.py` | CLEAN |
| `tests/test_uw_flow_ws.py` | CLEAN |
| `tests/test_vanguard_v2_vpin_gate.py` | CLEAN |

## Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py` (5 files) | `exec(base64.b64decode(...))` pattern for remote code execution on droplet. Payload is locally-sourced Python (not user input) but the pattern is inherently risky if file contents are ever tainted. |
| MEDIUM | Multiple scripts (`scripts/audit/`, `scripts/alpaca_*`) | `subprocess.run(..., shell=True)` with string commands. All observed instances use hardcoded or internally-constructed commands (not user-controlled), but `shell=True` remains a latent injection surface. |
| MEDIUM | `requirements.txt` | `urllib3==1.26.20` pinned to 1.x; the 2.x branch is current. No known critical CVE at scan time, but continuous pip-audit in CI is recommended. |
| LOW | `deploy_dashboard_fixes_ssh.py`, `deploy_dashboard_via_ssh.py`, `deploy_dashboard_ssh_direct.py` | Hardcoded droplet IP (`104.236.102.57`) in print output — minor information disclosure in tracked source. |
| LOW | Dashboard/internal scripts | HTTP (not HTTPS) used for localhost health-check calls (`http://127.0.0.1:5000`). Acceptable for loopback but ensure port 5000 is not exposed to public networks without TLS termination. |
| LOW | `scripts/run_uw_intel_on_droplet.py` | Uses `os.system(f"{os.sys.executable} scripts/...")` — hardcoded paths only; safe but prefer `subprocess.run` for better error handling. |

## Positive Observations

- **No hardcoded secrets found.** All API key / secret access uses `os.getenv()`.
- **No `verify=False`** anywhere in the codebase — TLS verification is never disabled.
- **`src/uw/uw_client.py`** applies proper timeouts (`timeout=12s`) on all HTTP calls.
- **`.env.example`** contains no real credentials (only variable names).
- **Changed files** in this push are cleanly written with defensive patterns (type/value error guards, env-gated feature flags).

## Recommendations

1. **CI pip-audit:** Add `pip-audit` to the CI pipeline for continuous dependency vulnerability scanning.
2. **Eliminate `exec(base64...)`:** Consider replacing the base64-exec remote execution pattern with a proper deployment mechanism (e.g., ship scripts to droplet via SCP then execute, or use a task runner).
3. **Reduce `shell=True`:** Refactor internal scripts to use list-form `subprocess.run(["cmd", "arg"])` where feasible to eliminate shell injection surface.
4. **Remove hardcoded IPs:** Move droplet IP to configuration/env rather than tracked source files.
5. **urllib3 upgrade path:** Plan migration to urllib3 2.x when alpaca-trade-api drops its `<2` pin.

## Verdict

**No HIGH or CRITICAL findings.** All changed files in commit `453b8952` are clean. Pre-existing MEDIUM findings are internal tooling patterns with no user-controlled input vectors. No GitHub issue filed.
