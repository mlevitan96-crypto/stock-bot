## Security Review (push to main)

**Commit / ref:** `b63423d85c185c45a39689ec4b1a86e1c8719568` — `fix(alpaca): advance STRICT_EPOCH_START to April 24 for V2 Vanguard cohort`
**Pushed by:** mlevitan96-crypto
**Date:** 2026-04-25

### Changed files in this push

| File | Change |
|------|--------|
| `telemetry/alpaca_strict_completeness_gate.py` | Epoch constant advanced to 2026-04-24T23:59:59Z |
| `scripts/extract_gemini_telemetry.py` | Fallback `STRICT_EPOCH_START` synced |
| `scripts/telemetry_milestone_watcher.py` | Fallback epoch + docstring synced |
| `reports/Gemini/telemetry_overview.md` | Extraction window updated |
| `reports/Gemini/alpaca_ml_cohort_flat.csv` | CSV data trimmed |

### Findings

**No CRITICAL or HIGH severity findings.**

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_weight_tuning_summary.py:36`, `run_droplet_weight_impact.py:34`, `run_droplet_shadow_confirmation.py:36`, `run_droplet_end_of_day_review.py:36`, `run_droplet_refresh_symbol_risk_features.py:27`, `scripts/governance/_run_compare_on_droplet.py:17`, `scripts/governance/_inspect_droplet_exit.py:17`, `scripts/governance/_fetch_three_run_metrics.py:43` | `exec(base64.b64decode(...))` pattern used to ship code to remote droplet. The payloads are developer-authored files read from the local repo (not user input), so this is not an RCE risk from untrusted input. However, `exec()` on decoded payloads is inherently fragile and should remain limited to trusted-operator tooling. |
| MEDIUM | `complete_droplet_verification.py:85` | `exec(import_stmt)` where `import_stmt` is a hardcoded dict value — low risk but worth noting. |
| MEDIUM | `force_cycle_run.py:15` | `exec(f.read(), ...)` to activate a Python venv — standard pattern but uses `exec`. |
| MEDIUM | ~30 files (scripts, archive, diagnostics) | `subprocess.run(..., shell=True, ...)` used extensively in diagnostic/deployment scripts. Commands are developer-defined strings (not user input), so injection risk is low. Best practice: prefer `shell=False` with list args where feasible. |
| MEDIUM | `requirements.txt` | `flask==3.0.0` — Flask 3.0.0 was released Dec 2023. Consider updating to latest 3.x for security patches. `requests==2.31.0` — pinned; later 2.32.x releases include security fixes. `paramiko==3.4.0` — check for known CVEs. Recommend running `pip-audit` in CI. |
| LOW | `deploy_dashboard_ssh_direct.py`, `deploy_dashboard_fixes_ssh.py`, `deploy_dashboard_via_ssh.py`, + 4 others | Droplet IP address `104.236.102.57` hardcoded in print statements / deploy scripts. Not a secret, but reduces operational flexibility and exposes infrastructure details in the repo. |
| LOW | `dashboard.py:2614-2615` | Client-side JS fetches `http://localhost:8081/...` — acceptable for same-host dashboard communication but note plain HTTP. |
| LOW | Various localhost HTTP calls | All `http://` calls in the codebase target `localhost` / `127.0.0.1` / `0.0.0.0` — no sensitive data sent over plain HTTP to external hosts. |

### Secrets & Credentials

- **No hardcoded API keys, tokens, passwords, or private keys found** in source code.
- All Alpaca credentials (`ALPACA_KEY`, `ALPACA_SECRET`) are loaded from environment variables via `get_alpaca_trading_credentials()` / `os.getenv()`.
- `.env` files are properly gitignored (`.gitignore` contains `.env` and `*.env`).
- No `.pem` files found in the repository.
- No `.env` files tracked in git.

### Unsafe Deserialization

- **No `pickle.load/loads`, `yaml.load` (unsafe), or `marshal.loads`** found.

### TLS / Certificate Verification

- **No `verify=False`** found in any Python file.
- **No `NODE_TLS_REJECT_UNAUTHORIZED=0`** found.

### Push-specific Assessment

The commit `b63423d8` only modifies epoch constants and CSV data. No new code paths, no new dependencies, no security-relevant logic changes. **Clean from a security perspective.**

### Recommendations

1. **CI integration:** Add `pip-audit` to CI pipeline to catch dependency CVEs automatically.
2. **Dependency freshness:** Consider bumping `flask`, `requests`, and `paramiko` to latest patch releases.
3. **`exec()` hygiene:** The base64-exec pattern for remote droplet execution is contained to trusted operator scripts. Document this pattern explicitly so future contributors understand the trust boundary.
4. **`shell=True` reduction:** Where feasible, convert `subprocess.run(..., shell=True)` calls to use list-form arguments (`shell=False`) to reduce shell injection surface.
5. **IP hardcoding:** Move the droplet IP to configuration or environment variables rather than hardcoding in deploy scripts.
