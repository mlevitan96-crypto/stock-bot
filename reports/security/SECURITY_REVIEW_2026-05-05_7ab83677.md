## Security Review (push to main)

**Commit / ref:** `7ab83677de07110862ba14d45e51899f9358a349` — `fix(exits): hard isolate OCC options from equity exit logic`  
**Pushed by:** mlevitan96-crypto  
**Date:** 2026-05-05  
**Scope:** Changed file: `main.py` (+29 lines — new `_equity_exit_skip_option_leg` function and its invocation in `AlpacaExecutor.evaluate_exits`).

---

### Summary

The push commit is **clean**. It adds a defensive regex-based filter function and integrates it into the equity exit evaluation loop. No secrets, no unsafe dynamic execution, no network calls introduced.

Full-tree scan of the repository also found **no CRITICAL or HIGH** findings. Several **MEDIUM** and **LOW** observations are noted below for ongoing hygiene.

---

### Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_run_compare_on_droplet.py`, `scripts/governance/_fetch_three_run_metrics.py`, `scripts/governance/_inspect_droplet_exit.py` | `exec(base64.b64decode(...))` pattern used to run local Python payloads on droplet via SSH. The payloads are constructed from repo-local source (not user input), but the pattern is inherently risky — a supply-chain compromise of these scripts could achieve RCE on the droplet. |
| MEDIUM | `complete_droplet_verification.py:85` | `exec(import_stmt)` where `import_stmt` is a string literal from a hardcoded dict. Low actual risk but flagged as exec usage. |
| MEDIUM | Multiple `scripts/` files | `subprocess.run(..., shell=True, ...)` used extensively in audit/diagnostic scripts. All commands are constructed from hardcoded strings or repo-controlled variables (not external user input). Acceptable for operator tooling but worth noting. |
| LOW | `archive/scripts/deployment_scripts/*.sh`, `SETUP_NEW_LAPTOP.md`, `SETUP_VENV_AND_DEPLOY.md`, `FIX_ALL_ISSUES_NOW.md` | Placeholder credential patterns like `ALPACA_KEY=your_alpaca_key_here`. These are documentation-only placeholders, not real secrets. Confirmed `.env` is in `.gitignore`. |
| LOW | Various `scripts/audit/*.py`, `zero_downtime_deploy.py`, `sre_monitoring.py` | HTTP (not HTTPS) used for `localhost`/`127.0.0.1` health-check endpoints. These are loopback-only calls on the droplet — acceptable for internal service health probes. |
| LOW | `requirements.txt` | `requests==2.31.0` and `flask==3.0.0` are ~2 years old. Recommend running `pip-audit` in CI to catch any disclosed CVEs. No known critical vulnerabilities at time of review but version freshness is a hygiene concern. |

---

### Commit-Specific Assessment

The diff in `7ab83677`:
- **No secrets introduced** — only a compiled regex constant and a pure function.
- **No network calls** — purely in-memory symbol classification.
- **No eval/exec** — uses `re.compile` (safe).
- **No deserialization** — reads only object attributes via `getattr`.
- **Verdict:** ✅ PASS — no security issues.

---

### Recommendations

1. **Consider removing `exec(base64.b64decode(...))` pattern** in droplet-interaction scripts. Alternatives: ship the script file via SCP and execute it, or use `paramiko`'s `exec_command` with the script path directly. This reduces the blast radius of any accidental code-injection in the payload-construction logic.

2. **Pin a CI step for `pip-audit`** to continuously scan for dependency CVEs. Current pinned versions are stable but aging.

3. **No `.env` file is tracked** (confirmed by `.gitignore` and absence from git tree). Maintain this discipline.

4. **No `verify=False`** found anywhere in the codebase — good. TLS verification is not disabled.

5. **No private keys or PEM files** found in the repository.

---

### Verdict

**No CRITICAL or HIGH findings. No GitHub issue required.**
