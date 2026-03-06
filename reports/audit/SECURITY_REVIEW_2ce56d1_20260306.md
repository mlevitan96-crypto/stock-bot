## Security Review (push to main)

**Commit / ref:** `2ce56d1cbd54a061ed897420458739f3e930a453`  
**Branch:** `main`  
**Pushed by:** mlevitan96-crypto  
**Date:** 2026-03-06  
**Changed files:**
- `reports/audit/AUTOMATION_TEST_REPORT_20260305-165820.md` (added)
- `reports/audit/AUTOMATION_TEST_RUN_20260305-165820.md` (added)
- `scripts/github_close_pr.py` (added)

---

### Changed-Files Review

All three added files were reviewed:

| File | Assessment |
|------|------------|
| `reports/audit/AUTOMATION_TEST_REPORT_20260305-165820.md` | Clean — documentation only, no secrets or code |
| `reports/audit/AUTOMATION_TEST_RUN_20260305-165820.md` | Clean — documentation only, no secrets or code |
| `scripts/github_close_pr.py` | Clean — reads `GITHUB_TOKEN`/`GH_TOKEN` from environment via `os.environ.get()`. No hardcoded tokens. Uses HTTPS for GitHub API. |

---

### Full-Tree Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `scripts/governance/_inspect_droplet_exit.py:17`, `_run_compare_on_droplet.py:17`, `_fetch_three_run_metrics.py:43`, and 5 files in `reports/_daily_review_tools/` | **exec(base64.b64decode(...))** pattern used to send code to remote droplet via SSH. Payloads are generated from local scripts (not user input), but this pattern bypasses static analysis and code review for what actually runs on the droplet. |
| MEDIUM | `execute_droplet_audit.py:24`, `deep_trading_diagnosis.py:13`, `comprehensive_no_positions_investigation.py:16`, `scripts/replay_week_multi_scenario.py:17`, plus ~10 archive scripts | **subprocess.run(shell=True)** — commands are hardcoded strings (not user input), but `shell=True` prevents argument injection defenses if any future change introduces variable interpolation. |
| MEDIUM | `scripts/run_uw_intel_on_droplet.py:141-176` | **os.system()** used for ~15 subprocess calls. `os.system()` provides no return-code checking or output capture and invokes a shell. Should migrate to `subprocess.run()`. |
| MEDIUM | `force_cycle_run.py:15`, `complete_droplet_verification.py:85` | **exec()** used for venv activation and dynamic import testing. Low risk (hardcoded local file reads) but reduces auditability. |
| MEDIUM | `requirements.txt` | **Dependency audit not automated.** `urllib3==1.26.20` is on the legacy 1.x branch. `pip-audit` should be added to CI to flag known CVEs. No critical CVEs are known for the currently pinned versions at this time, but the 1.x urllib3 line is in maintenance mode. |
| LOW | Multiple files (localhost only) | **HTTP used for local service calls** (`http://localhost:5000`, `http://localhost:8081`). All HTTP endpoints are local (dashboard, bot health). No sensitive data traverses external HTTP. Acceptable for local service mesh. |
| LOW | `scripts/github_close_pr.py:10-22` | **Custom .env loader** parses `.env` files manually. Consider using `python-dotenv` for more robust handling (e.g., multiline values, export prefix). Minor robustness concern, not a security vulnerability. |

---

### Positive Findings (no issues)

- **No hardcoded secrets**: All credentials (`ALPACA_KEY`, `ALPACA_SECRET`, `UW_API_KEY`, `GITHUB_TOKEN`, `DASHBOARD_USER`, `DASHBOARD_PASS`) are read from environment variables or `.env` files.
- **`.env` and `droplet_config.json` are gitignored**: Confirmed in `.gitignore`.
- **No `.env` file committed**: Verified — no `.env` file exists in the repository tree.
- **No `.pem` files**: No private key files found in the repository.
- **No `verify=False`**: No TLS certificate verification is disabled anywhere in production code.
- **No `NODE_TLS_REJECT_UNAUTHORIZED`**: Not set anywhere.
- **No `pickle.loads()`**: No unsafe deserialization found.
- **No SQL string concatenation**: No SQL injection patterns found.
- **All `requests.*()` calls include timeouts**: Checked all HTTP client calls across the codebase — all include explicit `timeout=` parameters.
- **HTTPS used for external APIs**: GitHub API, Alpaca API, UnusualWhales API all use HTTPS.

---

### Recommendations

1. **Add `pip-audit` to CI** — Automate dependency vulnerability scanning. Pin or upgrade `urllib3` to 2.x when `alpaca-trade-api` compatibility allows.
2. **Refactor exec(base64) droplet pattern** — Consider using `scp` + `python3 script.py` instead of encoding scripts as base64 and executing via `exec()`. This makes code reviewable and auditable on the droplet.
3. **Migrate os.system() to subprocess.run()** — In `scripts/run_uw_intel_on_droplet.py` and similar scripts, replace `os.system()` with `subprocess.run()` for proper error handling and to avoid shell injection surface.
4. **Audit shell=True usage** — For `subprocess.run(cmd, shell=True, ...)` calls, ensure the command string never includes untrusted input. Consider passing command as a list (`shell=False`) where possible.
5. **Consider pre-commit secret scanning** — Add a tool like `detect-secrets` or `trufflehog` as a pre-commit hook to prevent accidental credential commits.

---

### Verdict

**No HIGH or CRITICAL findings.** All MEDIUM findings are defense-in-depth concerns related to code execution patterns (exec, shell=True, os.system) where the inputs are currently hardcoded/locally-generated. No secrets are exposed. No GitHub issue required.
