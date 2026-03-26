## Security Review (push to main)

**Commit / ref:** `10d3dd05d2f1e346ebe1dfe42b98f553baab772d` — `docs: link permanentize proof to follow-up commit SHA`
**Pushed by:** mlevitan96-crypto
**Date:** 2026-03-26
**Changed files:** 2 (documentation only — `reports/audit/` markdown files)

---

### Summary

The push itself contains only documentation changes (two audit report markdown files) with no code modifications and no secrets. A full-tree scan of the repository was performed for all four security categories. **No CRITICAL or HIGH findings.** Several MEDIUM and LOW findings are noted below as best-practice improvements.

---

### Findings

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| 1 | **MEDIUM** | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_inspect_droplet_exit.py`, `scripts/governance/_run_compare_on_droplet.py`, `scripts/governance/_fetch_three_run_metrics.py` | **`exec(base64.b64decode(…))` pattern for remote code execution on droplet.** Local Python payload files are base64-encoded and sent to the droplet via SSH for execution. The payloads originate from checked-in source files (not user input), so this is not exploitable externally, but the pattern bypasses code review visibility on what actually runs remotely. |
| 2 | **MEDIUM** | `force_cycle_run.py:15`, `complete_droplet_verification.py:85` | **`exec()` used for virtualenv activation and dynamic import testing.** `force_cycle_run.py` uses `exec(f.read())` to activate a virtualenv. `complete_droplet_verification.py` uses `exec(import_stmt)` to test imports dynamically. Both are internally controlled strings, but `exec()` should be avoided where alternatives exist. |
| 3 | **MEDIUM** | `droplet_client.py:149`, `report_data_fetcher.py:107`, `fetch_droplet_data_and_generate_report.py:103` | **SSH `AutoAddPolicy()` accepts unknown host keys** without verification, making these connections susceptible to MITM attacks on first connect. Acceptable for a known single-droplet environment but not best practice. |
| 4 | **MEDIUM** | `requirements.txt` | **Dependency audit recommended.** `flask==3.0.0` and `requests==2.31.0` should be checked against `pip-audit` for known CVEs. `urllib3==1.26.20` is in the 1.x line — consider upgrading to 2.x when `alpaca-trade-api` compatibility allows. |
| 5 | **LOW** | ~20 files across `*.py` | **`subprocess.run(..., shell=True)` used extensively** in diagnostic, deployment, and audit scripts. Commands are constructed from hardcoded strings or config — not from user input — so injection risk is minimal. However, `shell=True` is a broad pattern that should be reviewed if any of these scripts ever accept external arguments. |
| 6 | **LOW** | `deploy_supervisor.py:383-384` | **Sentinel credentials `INVALID_KEY` / `INVALID_SECRET` set in environment** during dry-run mode. These are intentionally non-functional sentinel values used to prevent real trading during dry runs. No real secret exposure, but the pattern should be documented clearly. |
| 7 | **LOW** | Various `*.py` files | **HTTP (not HTTPS) used for localhost health checks** (e.g., `http://localhost:5000/health`, `http://localhost:8081/health`). This is standard for local/loopback health endpoints and is not a vulnerability. No external-facing HTTP calls to sensitive endpoints were found. |

---

### Non-Findings (Positive)

- **No hardcoded API keys, passwords, tokens, or private keys** found anywhere in the repository. All Alpaca credentials are loaded from environment variables via `os.getenv()` or the `Config` class.
- **`.env` files are properly gitignored** (`.gitignore` includes `.env` and `*.env`). No `.env` or `.pem` files are committed.
- **No `verify=False`** (disabled TLS certificate verification) found in any Python code.
- **No `pickle.load()` / `yaml.unsafe_load()`** or other unsafe deserialization found.
- **No `eval()` calls** found.
- **No `NODE_TLS_REJECT_UNAUTHORIZED=0`** found.
- **No SQL string concatenation** patterns found.

---

### Recommendations

1. **Consider replacing `exec(base64.b64decode(…))` remote execution pattern** with a proper remote script deployment (e.g., `scp` the payload file to droplet, then `ssh python /path/to/script.py`). This improves auditability and eliminates shell-escaping risks.

2. **Replace `AutoAddPolicy()`** with `RejectPolicy()` + a known-hosts file for the droplet, or at minimum `WarningPolicy()`. This protects against MITM on SSH connections.

3. **Run `pip-audit`** against `requirements.txt` in CI to catch known CVEs in pinned dependencies. Consider adding a GitHub Actions workflow or pre-commit hook.

4. **Audit `shell=True` usage** — where possible, pass command lists instead of shell strings to `subprocess.run()`. This is especially important if any diagnostic script is ever exposed to external input.

5. **Replace `exec(f.read())` virtualenv activation** in `force_cycle_run.py` with standard subprocess-based venv activation or direct path manipulation.

---

### Verdict

**No CRITICAL or HIGH findings. No GitHub issue required.**

The push (`10d3dd0`) is documentation-only and introduces no new security concerns. The repository-wide scan surfaces several MEDIUM best-practice improvements that should be addressed incrementally.
