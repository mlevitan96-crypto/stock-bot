## Security Review (push to main)

**Commit / ref:** `ff95b892d56d248311432da0a12b2c61d7647fb1` (feat: latency interrupt, epoch reset, and strict telegram milestones)  
**Push by:** mlevitan96-crypto  
**Base compare:** `453b8952d9c4..ff95b892d56d`  
**Reviewed:** 2026-05-01T22:30Z  
**Changed files:** `config/registry.py`, `main.py`, `scripts/alpaca_telegram.py`, `scripts/reset_epoch.py`, `src/telemetry/alpaca_attribution_emitter.py`, `src/telemetry/alpaca_exit_decision_made_emit.py`, `src/telemetry/epoch_manager.py`, `src/telemetry/post_epoch_milestone_tracker.py`, `src/telemetry/tier1_wake_bridge.py`, `tests/test_epoch_manager.py`, `tests/test_post_epoch_milestone_tracker.py`, `tests/test_tier1_wake_bridge.py`, `uw_flow_daemon.py`

---

### Findings

| Severity | Location | Description |
|----------|----------|-------------|
| **MEDIUM** | `reports/_daily_review_tools/run_droplet_weight_impact.py:34`, `run_droplet_end_of_day_review.py:36`, `run_droplet_shadow_confirmation.py:36`, `run_droplet_weight_tuning_summary.py:36`, `run_droplet_refresh_symbol_risk_features.py:27`, `scripts/governance/_run_compare_on_droplet.py:17`, `scripts/governance/_fetch_three_run_metrics.py:43`, `scripts/governance/_inspect_droplet_exit.py:17` | **`exec(base64.b64decode(...))`** — Multiple droplet-remote execution scripts encode a local Python file as base64 and `exec()` the decoded payload on the remote host. The payload originates from repository-tracked files (not user input), so this is not remotely exploitable, but the pattern obscures what code runs on the droplet and would be flagged by any static analysis tool. |
| **MEDIUM** | `scripts/run_uw_intel_on_droplet.py:141–176` | **`os.system()` with f-string interpolation** — 15 calls to `os.system(f"{os.sys.executable} ...")`. The arguments are derived from `argparse` (operator-controlled, not external user input), so injection risk is low in practice, but `subprocess.run([...])` with a list would be safer. |
| **MEDIUM** | 25+ files across `scripts/`, `archive/`, root | **`subprocess.run(..., shell=True)`** — Widespread use of `shell=True` in diagnostic/audit/deploy scripts. Commands are string-interpolated but arguments come from internal constants or operator CLI args, not untrusted external input. Still, list-form `subprocess.run` would eliminate shell injection surface entirely. |
| **LOW** | `force_cycle_run.py:15` | **`exec(f.read())` on virtualenv activate script** — Reads and execs `venv/bin/activate_this.py`. Standard virtualenv bootstrap pattern; not externally exploitable. |
| **LOW** | `complete_droplet_verification.py:85` | **`exec(import_stmt)` for import testing** — The `import_stmt` values are hardcoded strings in the same file, not user input. Functionally safe; could be replaced with `importlib`. |
| **LOW** | `zero_downtime_deploy.py:224–320`, `sre_monitoring.py:599`, `archive/scripts/diagnostic_scripts/verify_bot_status_complete.py:165` | **HTTP (non-TLS) requests to `localhost`** — Health-check calls to `http://localhost:5000/health` and similar. Acceptable for loopback health probes; no sensitive data transits the wire. |
| **LOW** | `requirements.txt` | **Dependency versions are pinned but no automated audit** — `requests==2.31.0`, `flask==3.0.0`, `paramiko==3.4.0`, `urllib3==1.26.20`. No known critical CVEs at time of review, but `pip-audit` should be integrated into CI for ongoing monitoring. |

---

### Positive Observations (no findings)

- **No hardcoded secrets or credentials in the repository.** All API keys (`ALPACA_KEY`, `ALPACA_SECRET`, `UW_API_KEY`, `DASHBOARD_USER`, `DASHBOARD_PASS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) are loaded exclusively from environment variables. `.env` is correctly listed in `.gitignore` and no `.env` file is committed.
- **No `verify=False` or disabled TLS verification anywhere in the codebase.**
- **No pickle/unpickle, `yaml.load()` without SafeLoader, or unsafe deserialization.**
- **No SQL string concatenation** (project doesn't appear to use a SQL database).
- **All `requests.*()` calls in production code include explicit `timeout=` parameters.**
- **Changed files in this push** (`epoch_manager.py`, `tier1_wake_bridge.py`, `post_epoch_milestone_tracker.py`, `alpaca_exit_decision_made_emit.py`, `reset_epoch.py`, etc.) are clean — no secrets, no unsafe patterns, no network calls without timeouts. The new code follows existing security conventions.

---

### Recommendations

1. **`exec(base64.b64decode(...))` droplet scripts** (MEDIUM): Consider replacing the base64-exec pattern with `scp` + `python script.py` on the remote, or a paramiko-based `exec_command` that sends the file and runs it directly. This improves auditability and eliminates exec.

2. **`os.system()` and `shell=True`** (MEDIUM): Migrate `os.system(f"...")` calls in `scripts/run_uw_intel_on_droplet.py` to `subprocess.run([sys.executable, ...])` list form. For the ~25 `shell=True` sites, convert to list-form `subprocess.run` where practical (especially any that interpolate variables).

3. **Dependency auditing** (LOW): Add `pip-audit` to CI pipeline (e.g., GitHub Actions step). Current versions have no known critical vulnerabilities, but automated scanning ensures ongoing coverage.

4. **No action required for this push.** All findings are pre-existing patterns, not introduced by commit `ff95b89`. No HIGH or CRITICAL issues detected.

---

**Verdict: PASS — no HIGH or CRITICAL findings. No GitHub issue required.**
