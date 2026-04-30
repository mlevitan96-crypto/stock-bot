## Security Review (push to main)

**Commit / ref:** `d5e237b8f82d5910520bc8254cb2eac1fd800a1a` — `chore(debug): v2_sparse_row_dna_smoke for droplet PYTHONPATH checks`  
**Base compare:** `bac5aece877d..d5e237b8f82d`  
**Files changed in push:** `scripts/debug/v2_sparse_row_dna_smoke.py` (new file, 39 lines)  
**Scan scope:** Full repository tree  
**Date:** 2026-04-30

---

### Changed-File Review

The single file added (`scripts/debug/v2_sparse_row_dna_smoke.py`) is a read-only diagnostic smoke test. It imports `shadow_evaluator` and `v2_row_quality_metrics`, builds a hardcoded feature map for symbol `XLF`, and prints quality metrics. **No secrets, no network calls, no unsafe patterns.**

---

### Full-Tree Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_run_compare_on_droplet.py`, `scripts/governance/_inspect_droplet_exit.py`, `scripts/governance/_fetch_three_run_metrics.py` | `exec(base64.b64decode(...))` pattern used to ship local Python scripts to the droplet via SSH. The base64 payload originates from files read at runtime from the local repo — not from user input or network data. Risk is limited to local-repo integrity, but the pattern bypasses standard code review visibility on the remote side. |
| MEDIUM | `complete_droplet_verification.py:85` | `exec(import_stmt)` where `import_stmt` is a hardcoded string from a local dict. No external input vector. |
| MEDIUM | `force_cycle_run.py:15` | `exec(f.read(), {'__file__': activate_this})` — standard virtualenv activation pattern (`activate_this.py`). Low risk. |
| MEDIUM | ~30 files (scripts, archive, deploy utilities) | `subprocess.run(..., shell=True, ...)` and `os.system(...)` calls. All observed invocations use hardcoded command strings or strings built from `os.sys.executable` / local paths — **none accept user or network input**. Best practice: prefer `subprocess.run([...], shell=False)` where feasible to reduce injection surface. |
| LOW | `dashboard.py:2615-2616` | Client-side JS `fetch('http://localhost:8081/...')` — browser-only, no server-side credential exposure. |
| LOW | Various localhost HTTP URLs (e.g., `sre_monitoring.py`, `zero_downtime_deploy.py`, `dashboard.py`) | HTTP used for localhost health-check endpoints. Acceptable for same-host loopback; would be a finding if exposed to WAN. |
| LOW | `requirements.txt` | `requests==2.31.0`, `flask==3.0.0`, `paramiko==3.4.0` — no known critical CVEs at time of review, but periodic `pip-audit` in CI is recommended. |

---

### Category Summary

| Category | Result |
|----------|--------|
| **Secrets / Credential Leaks** | **PASS** — No hardcoded API keys, tokens, passwords, or private keys found. All Alpaca credentials loaded via `os.getenv()` / `Config` class from environment. `.env` files properly gitignored. No `.pem` or `.key` files in the repo. |
| **Unsafe Patterns** | **MEDIUM** — `exec()` is used in ~10 deployment/diagnostic scripts but always with locally-sourced payloads (file reads from the repo, hardcoded strings). `shell=True` appears in ~30 scripts with hardcoded commands. No `pickle.loads`, `yaml.load` (without SafeLoader), or SQL string concatenation with external input detected. |
| **Dependency Vulnerabilities** | **LOW** — No known critical CVEs in pinned deps. Recommend adding `pip-audit` to CI. |
| **Insecure Network Calls** | **PASS** — No `verify=False`, no `NODE_TLS_REJECT_UNAUTHORIZED=0`, no disabled TLS verification. All HTTP URLs target localhost/loopback. |

---

### Recommendations

1. **`exec()` + base64 droplet pattern:** Consider replacing with `scp` + `python3 script.py` on the remote to improve auditability and avoid the `exec(base64.b64decode(...))` anti-pattern. This would make remote execution more transparent in process lists and logs.

2. **`shell=True` hygiene:** Where subprocess commands are simple single-program invocations, switch to list-form `subprocess.run(["cmd", "arg1", ...])` to eliminate shell-injection surface area. Priority: any script that might run on the droplet where env vars could be influenced.

3. **CI dependency audit:** Add `pip-audit` (or equivalent) as a CI step to catch future dependency CVEs automatically.

4. **Periodic secret scanning:** Consider adding a pre-commit hook or CI step with a tool like `detect-secrets` or `trufflehog` to prevent accidental secret commits.

---

### Verdict

**No CRITICAL or HIGH findings.** All findings are MEDIUM (operational hygiene) or LOW (best-practice suggestions). No GitHub issue required for this push.
