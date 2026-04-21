## Security Review (push to main)

**Commit / ref:** `db4522422995` — `chore(ml): droplet-safe apex sweep runner sourcing repo .env`
**Changed file:** `scripts/ml/run_apex_omni_sweep_with_dotenv.sh`
**Scan scope:** Full repository tree + changed file

---

### Findings

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| 1 | **MEDIUM** | `reports/_daily_review_tools/run_droplet_weight_tuning_summary.py:36`, `run_droplet_shadow_confirmation.py:36`, `run_droplet_end_of_day_review.py:36`, `run_droplet_refresh_symbol_risk_features.py:27`, `scripts/governance/_run_compare_on_droplet.py:17`, `_inspect_droplet_exit.py:17`, `_fetch_three_run_metrics.py:43` | **Remote code execution via `exec(base64.b64decode(...))` over SSH.** Several scripts encode a local Python payload as base64, send it to the droplet via SSH, and execute it with `exec()`. While the payload is read from a local repo file (not user input), this pattern is fragile: a compromised local file or injection into the command string could escalate to arbitrary execution on the droplet. |
| 2 | **MEDIUM** | `complete_droplet_verification.py:85` | **`exec(import_stmt)` with dynamically constructed string.** Used to dynamically import modules. If `import_stmt` is ever influenced by external input, this becomes an RCE vector. |
| 3 | **MEDIUM** | `force_cycle_run.py:15` | **`exec(f.read())` to activate a virtualenv.** Reads and executes the contents of a virtualenv `activate_this.py` file. Standard pattern for venv activation but still an `exec()` of file contents. |
| 4 | **MEDIUM** | 24 files (see shell=True scan) | **`subprocess.run(..., shell=True)` widespread.** Many scripts pass `shell=True` to subprocess calls. While most use hardcoded or internally-constructed commands (not external user input), this expands the attack surface if any argument is ever tainted. Notable files: `execute_droplet_audit.py`, `deploy_dashboard_fixes_ssh.py`, `deep_trading_diagnosis.py`, `scripts/alpaca_telemetry_forward_proof.py`, `scripts/replay_week_multi_scenario.py`, and others. |
| 5 | **MEDIUM** | `FIX_ALL_ISSUES_NOW.md:22-24` | **Placeholder secrets in documentation.** Contains `export UW_API_KEY="your_uw_key_here"` / `ALPACA_KEY="your_alpaca_key_here"` / `ALPACA_SECRET="your_alpaca_secret_here"`. These are placeholder values (not real secrets), but could train operators to paste real credentials into tracked files. |
| 6 | **MEDIUM** | `deploy_dashboard_fixes_ssh.py:154-159`, `deploy_dashboard_via_ssh.py:137-143`, `deploy_dashboard_ssh_direct.py:164-167`, and 30+ other files | **Hardcoded droplet IP address `104.236.102.57`** in source code and documentation. Exposes infrastructure topology. Should be abstracted to an environment variable or config. |
| 7 | **LOW** | `dashboard.py:2614-2615`, `comprehensive_system_check.py:56`, `harden_xai_system.py:108`, `sre_monitoring.py:599`, `zero_downtime_deploy.py` | **HTTP (not HTTPS) for localhost service calls.** All observed HTTP calls target `localhost` / `127.0.0.1` for health checks and internal APIs. This is acceptable for loopback traffic but noted for completeness. No HTTP calls to external sensitive endpoints were found. |
| 8 | **LOW** | `requirements.txt` | **Dependency audit recommended.** Key pinned versions: `requests==2.31.0`, `flask==3.0.0`, `paramiko==3.4.0`, `urllib3==1.26.20`, `alpaca-trade-api==3.2.0`. A `pip-audit` or `safety check` should be run in CI to detect known CVEs. No confirmed critical CVEs at scan time, but `urllib3<2` is pinned for compatibility and may lag security patches. |
| 9 | **LOW** | Repository-wide | **No `verify=False` or disabled TLS found.** All `requests` calls use default certificate verification. No `NODE_TLS_REJECT_UNAUTHORIZED=0` found. Good. |
| 10 | **LOW** | Repository-wide | **No hardcoded API keys, tokens, or private keys found.** All credential access goes through `os.getenv()` / `os.environ`. `.env` and `*.env` are properly gitignored. `.env.example` contains only variable names, not values. |

---

### Changed File Analysis: `scripts/ml/run_apex_omni_sweep_with_dotenv.sh`

The pushed file sources `.env` via `. ./.env` with `set -a` / `set +a` to export variables. This is a standard shell pattern and does not leak secrets into the repository. The script prints a boolean confirmation (`ALPACA creds loaded: True/False`) rather than the credential values themselves. **No security issues in the changed file.**

---

### Recommendations

1. **Reduce `exec()` + base64 remote execution pattern (MEDIUM).** Consider replacing the `exec(base64.b64decode(...))` SSH pattern with a proper deployment of helper scripts to the droplet, then invoking them by path. This eliminates the code-injection surface.

2. **Audit `shell=True` usage (MEDIUM).** Inventory all `subprocess` calls with `shell=True` and convert to list-form (`shell=False`) where possible. Where shell features are genuinely needed, validate or quote arguments defensively.

3. **Extract hardcoded IP to config (MEDIUM).** Move `104.236.102.57` to an environment variable (e.g., `DROPLET_IP`) or a config file excluded from version control.

4. **Add `pip-audit` to CI (LOW).** Run `pip-audit -r requirements.txt` in a CI step to catch known CVEs in pinned dependencies, especially `urllib3==1.26.20` and `paramiko==3.4.0`.

5. **Remove placeholder credential examples from tracked docs (LOW).** In `FIX_ALL_ISSUES_NOW.md`, replace `export ALPACA_KEY="your_alpaca_key_here"` with `export ALPACA_KEY="$ALPACA_KEY"` or reference `.env.example` instead.

---

**Overall assessment:** No CRITICAL or HIGH findings. The repository follows good practices for secret management (`.env` gitignored, `os.getenv()` for credentials, no `verify=False`). The primary areas for hardening are the `exec()`/base64 remote execution pattern and widespread `shell=True` usage, both MEDIUM severity.
