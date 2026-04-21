## Security Review (push to main)

**Commit / ref:** `4b21ac6fa1ea92acb7ef938bd484f2f18ff6a672` — "Add hyper-confluence engine for cohort GUT and SHAP triad/quartet scan"
**Pushed by:** mlevitan96-crypto
**Date:** 2026-04-21
**Files changed:** `scripts/ml/hyper_confluence_engine.py` (new), `requirements.txt` (added `shap>=0.44.0`)

---

### Findings

| Severity | Location | Description |
|----------|----------|-------------|
| **NONE** | `scripts/ml/hyper_confluence_engine.py` | New file is clean: no secrets, no `eval`/`exec`, no network calls, no subprocess, no deserialization of untrusted data. Reads local CSV, writes local artifacts only. |
| **NONE** | `requirements.txt` | Added `shap>=0.44.0` — well-known SHAP library for ML explainability. No known critical CVEs at time of review. |
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py` (pre-existing, 5 files) | `exec(base64.b64decode(...))` pattern used to ship Python payloads to the droplet via SSH. The payloads originate from checked-in repo files (not external input), so this is controlled code execution — but the `exec` pattern is inherently risky and should be monitored. |
| MEDIUM | Multiple files (pre-existing, ~20 files) | `subprocess.run(..., shell=True, ...)` used in deployment/diagnostic scripts. Commands are constructed from controlled inputs (no external/user input flows into the shell string), but `shell=True` expands the attack surface if any input becomes tainted in the future. |
| MEDIUM | `src/ml/alpha10_inference.py`, `src/ml/alpaca_shadow_scorer.py` (pre-existing) | `joblib.load()` on model files from disk. Models are loaded from repo-controlled paths (`models/paper_ml_gate/`). Risk is low since the files are not user-supplied, but joblib deserialization can execute arbitrary code if a model file is tampered with. |
| LOW | `dashboard.py`, `sre_monitoring.py`, etc. (pre-existing) | HTTP (not HTTPS) used for localhost service-to-service calls (`http://localhost:5000`, `http://localhost:8081`). Acceptable for same-host loopback communication; no sensitive data transits non-loopback HTTP. |
| LOW | `requirements.txt` (pre-existing) | `paramiko==3.4.0` — SSH library. Ensure periodic `pip-audit` runs in CI to catch future CVEs in pinned dependencies. |

---

### Recommendations

1. **No action required for this push.** The changed files (`hyper_confluence_engine.py`, `requirements.txt`) are clean with no security concerns.

2. **(Pre-existing, MEDIUM) `exec(base64.b64decode(...))` in droplet runners:** Consider migrating these to a dedicated `ssh <host> python3 /path/to/script.py` invocation pattern instead of base64-encoding code and executing it via `exec`. This would improve auditability and eliminate the exec pathway.

3. **(Pre-existing, MEDIUM) `shell=True` in subprocess calls:** Where possible, convert to `shell=False` with explicit argument lists. This is particularly important for any scripts that may evolve to accept external inputs.

4. **(Pre-existing, MEDIUM) `joblib.load()` model deserialization:** Consider adding checksum validation (e.g., SHA-256 hash check) before loading model files to detect tampering. The `.gitignore` excludes `.joblib` files from git, so the model provenance chain should be documented.

5. **(Pre-existing, LOW) Dependency audit:** Run `pip-audit` periodically (or add to CI) to catch CVEs in pinned dependencies such as `paramiko`, `urllib3`, `flask`, `requests`, etc.

---

### Verdict

**PASS** — No HIGH or CRITICAL findings. The pushed commit introduces a pure-compute ML analysis script with no security concerns. Pre-existing MEDIUM patterns are documented above for backlog tracking.
