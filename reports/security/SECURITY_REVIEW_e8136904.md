## Security Review (push to main)

**Commit / ref:** `e8136904986af68f1379430fcec73d333d88e435`
**Message:** fix(dashboard): serve DASHBOARD_HTML from / instead of legacy static/index.html
**Pushed by:** mlevitan96-crypto
**Review date:** 2026-05-02T03:55Z

---

### Push Commit Analysis

The commit removes file-system-based serving of `static/index.html` and replaces it with an inline `Response(DASHBOARD_HTML, ...)`. No new secrets, no new unsafe patterns introduced. The change is benign from a security perspective.

---

### Full-Tree Scan Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_run_compare_on_droplet.py`, `scripts/governance/_fetch_three_run_metrics.py`, `scripts/governance/_inspect_droplet_exit.py` | `exec(base64.b64decode(...))` pattern — encodes local repo source files and executes on remote droplet. Input is repo-controlled (not user/external), but the pattern itself is high-surface-area if the transport is ever compromised. |
| MEDIUM | Multiple scripts (`comprehensive_no_positions_investigation.py`, `scripts/audit/run_exec_mode_*.py`, `scripts/alpaca_telemetry_forward_proof.py`, etc.) | `subprocess.run(cmd, shell=True, ...)` — all observed instances use hardcoded or locally-constructed commands (no user input interpolation). Standard `shell=True` caution applies. |
| MEDIUM | `scripts/run_uw_intel_on_droplet.py` | Multiple `os.system(...)` calls with f-string interpolation of local variables (`date`, `os.sys.executable`). Inputs are locally derived, not user-controlled, but `os.system` is less safe than `subprocess.run` with explicit args. |
| LOW | `dashboard.py` (line 7560), `main.py` (line 18705) | Both bind to `0.0.0.0`. Dashboard has HTTP Basic Auth gating (`DASHBOARD_ALLOW_PUBLIC_HTML` env toggle). Ensure firewall rules restrict access on the production droplet. |
| LOW | `force_cycle_run.py` (line 15) | `exec(f.read(), {'__file__': activate_this})` for venv activation — standard Python virtualenv activation pattern, not a vulnerability. |
| LOW | N/A (dependency audit) | No `pip-audit` or `safety` scan was run in this review. Recommend adding automated dependency vulnerability scanning to CI. |

---

### Secrets & Credentials

**No hardcoded secrets found.** All API credentials (`ALPACA_KEY`, `ALPACA_SECRET`, `UW_API_KEY`, Telegram tokens) are read from environment variables via `os.getenv()`. The `.gitignore` correctly excludes `.env`, `droplet_config.json`, and state directories. Only `.env.example` and `deploy/alpaca_post_repair.env.sample` are tracked (contain placeholder names, not values).

### TLS / Certificate Verification

**No instances of `verify=False` found.** All `requests.*` calls include explicit timeouts (good). No disabled TLS rejection (`NODE_TLS_REJECT_UNAUTHORIZED`) detected.

### SQL Injection / Deserialization

**No SQL string concatenation found.** No `pickle.loads` with untrusted input. No unsafe `yaml.load()` calls detected.

---

### Recommendations

1. **CI Dependency Scanning:** Add `pip-audit` (or `safety`) to CI pipeline for automated vulnerability detection on each push.
2. **Reduce `shell=True` usage:** Where feasible, refactor `subprocess.run(cmd, shell=True, ...)` to use list-form arguments (`subprocess.run([...])`) to eliminate shell injection surface area, even though current inputs are locally controlled.
3. **Replace `os.system()`:** In `scripts/run_uw_intel_on_droplet.py`, migrate from `os.system()` to `subprocess.run()` for better error handling and reduced injection surface.
4. **Firewall audit:** Verify that `0.0.0.0` bindings on port 5000 (dashboard) and 8080 (API) are protected by OS-level firewall rules (e.g., `ufw`) on the production droplet, allowing only expected source IPs.
5. **Base64-exec pattern:** Consider replacing the `exec(base64.b64decode(...))` remote execution pattern with a proper deployment script or SSH command dispatch that doesn't embed full source as base64 — reduces attack surface if SSH transport or the DropletClient is ever compromised.

---

### Verdict

**No CRITICAL or HIGH findings.** All findings are MEDIUM (architectural patterns that are controlled but warrant hardening) or LOW (best-practice suggestions). No GitHub issue required.
