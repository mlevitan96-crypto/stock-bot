# Security Review — Full Repository Scan

**Date:** 2026-03-26
**Scope:** All Python files in `/workspace` (1,245 files). No JavaScript files found.
**Excluded:** `node_modules/`, `.git/`, `__pycache__/`

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 3     |
| HIGH     | 5     |
| MEDIUM   | 7     |
| LOW      | 5     |

---

## CRITICAL Findings

### C1. Remote Code Execution via `exec(base64.b64decode(...))` on Droplet

**Pattern:** `exec()` with base64-encoded payloads sent over SSH to a remote server.

| File | Line | Code |
|------|------|------|
| `reports/_daily_review_tools/run_droplet_weight_tuning_summary.py` | 36 | `exec(base64.b64decode("..." + b64 + "..."))` |
| `reports/_daily_review_tools/run_droplet_refresh_symbol_risk_features.py` | 27 | Same pattern |
| `reports/_daily_review_tools/run_droplet_shadow_confirmation.py` | 36 | Same pattern |
| `reports/_daily_review_tools/run_droplet_weight_impact.py` | 34 | Same pattern |
| `reports/_daily_review_tools/run_droplet_end_of_day_review.py` | 36 | Same pattern |
| `scripts/governance/_inspect_droplet_exit.py` | 17 | `exec(base64.b64decode("%s").decode())` via SSH |
| `scripts/governance/_run_compare_on_droplet.py` | 17 | Same pattern |
| `scripts/governance/_fetch_three_run_metrics.py` | 43 | Same pattern |

**Exploitability:** These scripts read a local Python file, base64-encode it, and execute it on a remote droplet via SSH. The payload comes from files within the repo, so under normal operation an external attacker cannot inject code. **However**, if an attacker can modify the payload source files (e.g., via a compromised dependency, supply-chain attack, or repo write access), they gain arbitrary code execution on the production droplet. The base64-encoding also defeats code review — the actual code run on the droplet is opaque in the SSH command.

**Severity:** CRITICAL — Arbitrary remote code execution pathway. Payload files are not signed or integrity-checked.

**Recommendation:** Replace base64-encoded exec with SFTP upload + explicit `python3 <script>` invocation. Sign or checksum payload scripts before execution.

---

### C2. `exec()` with hardcoded import statements

| File | Line | Code |
|------|------|------|
| `complete_droplet_verification.py` | 85 | `exec(import_stmt)` where `import_stmt` comes from a dict of import strings |

**Exploitability:** The import statements are hardcoded in the same file (not user-controlled), so this is not directly exploitable by external input. However, `exec()` of string-based imports is a dangerous pattern — if any element of the dict were ever sourced from external input or config, it would be RCE.

**Severity:** CRITICAL — RCE pattern (exec of string). Currently uses hardcoded input only.

**Recommendation:** Replace `exec(import_stmt)` with `importlib.import_module()` for programmatic imports.

---

### C3. `exec(f.read())` for virtualenv activation

| File | Line | Code |
|------|------|------|
| `force_cycle_run.py` | 15 | `exec(f.read(), {'__file__': activate_this})` |

**Exploitability:** Reads and executes the virtualenv `activate_this.py` file. If an attacker can write to the venv directory (e.g., compromised pip package, local file write), they achieve arbitrary code execution. This is a known pattern from older virtualenv versions.

**Severity:** CRITICAL — Executes arbitrary file contents. Relies on filesystem integrity.

**Recommendation:** Use `subprocess` to invoke the venv Python binary directly instead of exec-ing activation scripts.

---

## HIGH Findings

### H1. Path Traversal in Dashboard Telemetry API

| File | Line | Code |
|------|------|------|
| `dashboard.py` | 6505–6538 | `name = request.args.get("name")` → `fn = _TELEMETRY_COMPUTED_MAP.get(name) or name` → `fp = comp_dir / str(fn)` |

**Exploitability:** The `/api/telemetry/latest/computed` endpoint accepts a `name` query parameter from the HTTP request. If the name is not found in `_TELEMETRY_COMPUTED_MAP`, it falls through to use the raw user input as a filename. The only check is `.endswith(".json")`. An attacker can read arbitrary `.json` files on the server by sending `name=../../../etc/something.json` or `name=../../.env.json`. While the endpoint is behind HTTP Basic Auth, any authenticated user can exploit this.

**Severity:** HIGH — Arbitrary file read (limited to `.json` files) by authenticated users.

**Recommendation:** Validate that the resolved path stays within `comp_dir` (e.g., `fp.resolve().is_relative_to(comp_dir.resolve())`), or reject any name not in the allowlist map.

---

### H2. SSH Host Key Verification Disabled (`AutoAddPolicy`)

| File | Line | Code |
|------|------|------|
| `droplet_client.py` | 149 | `ssh.set_missing_host_key_policy(AutoAddPolicy())` |
| `report_data_fetcher.py` | 107 | `ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())` |
| `fetch_droplet_data_and_generate_report.py` | 103 | `ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())` |

**Exploitability:** `AutoAddPolicy` accepts any SSH host key without verification, making the connection vulnerable to man-in-the-middle attacks. An attacker who can intercept the network between the CI/dev machine and the droplet can impersonate the server, steal credentials, and execute commands.

**Severity:** HIGH — MITM attack vector on SSH connections to the production droplet.

**Recommendation:** Use `RejectPolicy` (default) or `WarningPolicy` and pin known host keys. Load from `~/.ssh/known_hosts` or a committed known-hosts file.

---

### H3. `os.system()` with f-string interpolation (command injection surface)

| File | Lines | Code |
|------|-------|------|
| `scripts/run_uw_intel_on_droplet.py` | 141, 159–178 | `os.system(f"{os.sys.executable} scripts/... --date {date}")` |

**Exploitability:** The `date` variable originates from `argparse` CLI input (`args.date.strip()`). While this is a command-line tool (not web-facing), if the `--date` argument contains shell metacharacters (e.g., `; rm -rf /`), it will be executed. `os.system()` invokes a shell and does not sanitize arguments.

**Severity:** HIGH — Command injection via CLI argument. Attacker needs local CLI access.

**Recommendation:** Replace `os.system()` with `subprocess.run([...], shell=False)` using list-based argument passing to avoid shell interpretation.

---

### H4. `subprocess.run(cmd, shell=True)` across 20 files

| Files (selected) | Pattern |
|-------------------|---------|
| `execute_droplet_audit.py:24` | `subprocess.run(cmd, shell=True, ...)` |
| `deploy_dashboard_fixes_ssh.py:20` | Same |
| `deep_trading_diagnosis.py:13` | Same |
| `comprehensive_no_positions_investigation.py:16` | Same |
| `check_droplet_trading_now.py:17` | Same |
| `run_diagnostic_via_ssh.py:26` | Same |
| `run_droplet_trading_audit.py:31` | Same |
| `scripts/alpaca_telemetry_inventory_droplet.py:64` | Same |
| `scripts/alpaca_telemetry_forward_proof.py:171` | Same |
| `scripts/alpaca_loss_forensics_droplet.py:287` | Same |
| `scripts/replay_week_multi_scenario.py:17` | Same |
| `COMPREHENSIVE_DIAGNOSTIC_AND_FIX.py:32` | Same |
| `COMPLETE_STRUCTURAL_INTELLIGENCE_DEPLOYMENT.py:17` | Same |
| Plus 7 files in `archive/` | Same |

**Exploitability:** Most of these construct the `cmd` string from hardcoded or internally-generated values, not direct user input. The risk is when `cmd` includes any interpolated value (e.g., SSH remote command strings, file paths from environment). The `shell=True` flag enables shell expansion, making any string interpolation a potential injection point.

**Severity:** HIGH — Systemic use of `shell=True` across 20+ files. Individually low risk (hardcoded commands), but creates a broad injection surface if any input source changes.

**Recommendation:** Audit each call to ensure no user/external input flows into `cmd`. Migrate to `subprocess.run([...], shell=False)` where possible.

---

### H5. Dashboard Auth Bypass for Selected GET Endpoints

| File | Line | Code |
|------|------|------|
| `dashboard.py` | 107–121 | `if request.method == "GET" and (request.path == "/" or request.path in (...))` → `return None` |

**Exploitability:** Seven endpoints are explicitly exempted from HTTP Basic Auth: `/`, `/api/direction_banner`, `/api/situation`, `/api/telemetry_health`, `/api/dashboard/data_integrity`, `/api/learning_readiness`, `/api/profitability_learning`, `/api/alpaca_operational_activity`. Any unauthenticated user can access these. If these endpoints leak sensitive trading data, P&L, or internal state, this is an information disclosure risk.

**Severity:** HIGH — Intentional auth bypass on endpoints that may expose trading intelligence to unauthenticated users.

**Recommendation:** Review whether each exempted endpoint actually needs to be public. Consider restricting to only the HTML root `/` if the others contain sensitive data.

---

## MEDIUM Findings

### M1. `__import__()` used for inline imports

| File | Line | Code |
|------|------|------|
| `scripts/audit/alpaca_replay_lab_strict_gate.py` | 26 | `__import__("re").compile(...)` |
| `scripts/verify_all_signals_on_droplet.py` | 105 | `__import__("time").time()` |
| `scripts/run_daily_signal_map_on_droplet.py` | 13 | `__import__("argparse").ArgumentParser()` |
| `scripts/ops/apply_paper_overlay.py` | 45 | `__import__("datetime").datetime.now(...)` |
| `scripts/replay/run_equity_replay_campaign.py` | 21 | `__import__("argparse").ArgumentParser()` |
| `scripts/governance/_droplet_run3_and_compare.py` | 11 | `__import__("base64").b64encode(...)` |
| Multiple `validation/scenarios/test_*.py` files | Various | `__import__("sys").path.insert(...)` |
| Multiple `tests/test_*.py` files | Various | `__import__("shutil").rmtree(...)` |

**Exploitability:** All arguments to `__import__()` are string literals (hardcoded), not user-controlled. No exploitation path exists.

**Severity:** MEDIUM — Code smell / maintainability issue. Not a security risk as currently used.

**Recommendation:** Replace with standard `import` statements for clarity.

---

### M2. `compile()` used for syntax checking

| File | Line | Code |
|------|------|------|
| `archive/investigation_scripts/regression_test_architecture_fixes.py` | 41 | `compile(code, "main.py", "exec")` |
| `archive/investigation_scripts/FULL_AUDIT_AND_VERIFICATION.py` | 183 | `compile(f.read(), file, "exec")` |
| `FINAL_END_TO_END_VERIFICATION.py` | 238 | `compile(content, file_path, "exec")` |

**Exploitability:** `compile()` is used for syntax validation of Python files (not followed by `exec()`). The input is read from local files, not user input. Safe as used.

**Severity:** MEDIUM — Benign use for syntax checking. Not a security risk.

**Recommendation:** No action needed. Pattern is safe.

---

### M3. `setattr()` with config dict input

| File | Line | Code |
|------|------|------|
| `trade_guard.py` | 60 | `setattr(self, key, value)` — iterating over `config.items()` |
| `adaptive_signal_optimizer.py` | 353, 611 | `setattr(self.weight_bands[k], field_name, field_val)` — from JSON config |

**Exploitability:** Both use `hasattr()` guard before `setattr()`, limiting attribute names to those already defined on the object. However, if `config` comes from a user-editable JSON file and the object has sensitive attributes (e.g., `max_position_size`), a malicious config could override safety guardrails.

**Severity:** MEDIUM — Config-driven attribute override. Bounded by `hasattr()` check, but could bypass intended limits via config manipulation.

**Recommendation:** Use an explicit allowlist of permitted config keys instead of `hasattr()`.

---

### M4. `setattr()` for stub module creation

| File | Line | Code |
|------|------|------|
| `main.py` | 32–34, 48, 60 | `setattr(requests, "get", _missing_requests)` etc. |

**Exploitability:** Used to create stub modules when dependencies are missing. All attribute names are hardcoded string literals. Not exploitable.

**Severity:** MEDIUM — Defensive stub pattern. Safe as used.

---

### M5. `__import__()` for dynamic module testing

| File | Line | Code |
|------|------|------|
| `test_dashboard_comprehensive.py` | 126 | `__import__(module)` — module name from hardcoded list |
| `archive/investigation_scripts/FULL_AUDIT_AND_VERIFICATION.py` | 152 | `module = __import__(module_name)` — from hardcoded list |
| `archive/investigation_scripts/COMPREHENSIVE_END_TO_END_AUDIT.py` | 556 | `__import__(module_name)` — from hardcoded list |
| `archive/investigation_scripts/deploy_and_verify_complete.py` | 52 | `__import__(m)` — remote execution in SSH string |

**Exploitability:** Module names are hardcoded lists; not user-controlled. Safe as used.

**Severity:** MEDIUM — Standard import testing pattern with hardcoded inputs.

---

### M6. Unvalidated `date` parameter in `request.args`

| File | Line | Code |
|------|------|------|
| `dashboard.py` | 4402 | `date_str = request.args.get("date")` |

**Exploitability:** The `date` parameter from the HTTP request is used in string comparisons against stored data (`str(data.get("date", "")) == str(date_str)`). It does not flow into file paths, shell commands, or SQL queries. Low risk.

**Severity:** MEDIUM — Unvalidated input used in comparison only. Not directly exploitable.

---

### M7. DropletClient `_execute()` accepts arbitrary command strings

| File | Line | Code |
|------|------|------|
| `droplet_client.py` | 235–284 | `def _execute(self, command: str, ...)` → `ssh.exec_command(command)` |

**Exploitability:** The `_execute` method runs any string as a shell command over SSH. Throughout the codebase, many scripts compose commands with f-strings that interpolate file paths, dates, and remote directory names (see `scripts/run_*_on_droplet.py` files). While the interpolated values are generally from internal sources (argparse, config), there is no sanitization layer. Any future change that passes external input through this method creates an SSH command injection.

**Severity:** MEDIUM — Broad injection surface; currently safe because inputs are internal. No defensive layer.

**Recommendation:** Add an `execute_script(path, args_list)` helper that avoids shell interpretation, or validate/escape all interpolated values.

---

## LOW Findings

### L1. `subprocess.Popen` and `subprocess.call` without `shell=True` (safe usage)

| Files | Count |
|-------|-------|
| `heartbeat_keeper.py`, `deploy_supervisor.py`, `zero_downtime_deploy.py`, `scripts/shadow_integrity_check.py`, many `scripts/*.py` | 15+ files |

**Exploitability:** These use list-based argument passing without `shell=True`. This is the secure pattern. No risk.

**Severity:** LOW — Best practice. Noted for completeness.

---

### L2. `re.compile()` usage (false positive for `compile()`)

**Exploitability:** All `re.compile()` calls compile hardcoded regex patterns. No risk.

**Severity:** LOW — Not a security concern.

---

### L3. Broad exception handling with bare `except:`

| Files | Pattern |
|-------|---------|
| Multiple files across the codebase | `except:` (bare) or `except Exception:` swallowing errors |

**Exploitability:** Bare `except:` can mask security-relevant errors (e.g., permission denied, authentication failures). Not directly exploitable but can hide attack indicators.

**Severity:** LOW — Operational risk, not a direct vulnerability.

**Recommendation:** Use specific exception types and log caught exceptions.

---

### L4. Dashboard binds to `0.0.0.0`

| File | Line | Code |
|------|------|------|
| `dashboard.py` | 6716 | `app.run(host="0.0.0.0", port=port, debug=False, threaded=True)` |

**Exploitability:** The dashboard binds to all interfaces. This is intentional for a server deployment, but means the service is accessible from any network interface. Combined with the auth bypass on some GET endpoints (H5), this expands the attack surface.

**Severity:** LOW — Expected for a deployed service, but worth noting in combination with H5.

---

### L5. No CSRF protection on dashboard

| File | Pattern |
|-------|---------|
| `dashboard.py` | Flask app with no CSRF token validation |

**Exploitability:** The dashboard uses HTTP Basic Auth but does not implement CSRF protection. A cross-site request from a malicious page could trigger authenticated API calls if the browser has cached credentials. The risk is limited because the dashboard appears to be read-only (no state-changing POST endpoints exposed to the browser).

**Severity:** LOW — Mitigated by read-only nature of most endpoints and Basic Auth.

---

## Patterns NOT Found (Clean)

| Pattern | Status |
|---------|--------|
| `pickle.loads()` / `cPickle` | **Not found** — No pickle deserialization anywhere |
| SQL injection (string-concatenated queries) | **Not found** — No SQL database usage detected |
| `yaml.load()` without `SafeLoader` | **Not found** — No unsafe YAML loading |
| `eval()` in Python | **Not found** — No `eval()` calls |
| `eval()` in JavaScript | **Not found** — No `.js` files in repo |
| `requests.get(..., verify=False)` | **Not found** — No SSL verification bypass |
| `debug=True` in Flask | **Not found** — `debug=False` confirmed |
| Hardcoded secrets/API keys in source | **Not found** — Secrets use `.env` (gitignored) |
| Committed `.env` or `droplet_config.json` | **Not found** — Properly gitignored |

---

## Top 3 Recommended Actions

1. **Replace base64+exec remote execution pattern** (C1) — Upload scripts via SFTP and invoke with `python3 <script>`, eliminating the RCE-via-payload-file risk entirely.

2. **Fix path traversal in `/api/telemetry/latest/computed`** (H1) — Add `fp.resolve().is_relative_to(comp_dir.resolve())` check or restrict to the allowlist map only.

3. **Replace `AutoAddPolicy` with known-hosts verification** (H2) — Pin the droplet's SSH host key to prevent MITM attacks on the production SSH connection.
