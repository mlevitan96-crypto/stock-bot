## Security Review (push to main)

**Commit / ref:** `a7be89bcaf6edbb388209559109347fdb06c8a82`
**Message:** `fix(supervisor): bind Command Desk on fixed port 5005; drop 5006 fallback`
**Author:** Mark (mlevitan96@gmail.com) — 2026-05-05
**Files changed:** `dashboard.py`, `deploy/stock-bot-dashboard.service`, `deploy_supervisor.py`
**Scan scope:** Full repository tree + commit diff

---

### Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_*.py` (8 files) | `exec(base64.b64decode(...))` pattern used to ship Python payloads to the droplet via SSH. The base64-encoded code is constructed from local file reads / hardcoded strings — **not** from user or external input. Risk is limited to operator-trust boundary (SSH session to the droplet). No user-facing RCE vector, but the pattern reduces auditability of what runs remotely. |
| MEDIUM | `scripts/run_uw_intel_on_droplet.py` (lines 141–178), `scripts/alpaca_rampant_analysis_mission.py`, `scripts/alpaca_canonical_memory_bank_and_edge_mission.py`, and ~15 other scripts | `subprocess.run(..., shell=True)` and `os.system(f"...")` with f-string interpolation. All interpolated values are internally-controlled (e.g. `os.sys.executable`, CLI `--date` arg, hardcoded script paths). No injection from external/untrusted data detected. Best practice: prefer `subprocess.run([...], shell=False)` where feasible. |
| MEDIUM | `requirements.txt` — `requests==2.31.0` | `requests` 2.31.0 is affected by CVE-2024-35195 (session headers leak on redirect to a different host). Moderate severity — relevant if any HTTP client follows cross-origin redirects with auth headers. Recommend upgrading to `requests>=2.32.0`. |
| LOW | `force_cycle_run.py:15` | `exec(f.read(), {'__file__': activate_this})` to activate a virtualenv. Standard pattern (`activate_this.py`); file is local and operator-controlled. No external input. |
| LOW | `complete_droplet_verification.py:85` | `exec(import_stmt)` where `import_stmt` is a hardcoded string literal from a dict 3 lines above. No external input. |

---

### Commit-Specific Review (a7be89bc)

The pushed commit removes dynamic port-scanning logic (socket probing ports 5006–5009) and hardcodes port 5005 for the dashboard. **No security concerns introduced:**

- No new secrets, credentials, or env vars exposed.
- No new `eval`/`exec`/`shell=True` patterns.
- No changes to authentication, TLS, or network call patterns.
- Simplified control flow (removed `socket` import and port-probing loop) reduces attack surface marginally.

---

### Secrets & Credential Leak Scan

- **No hardcoded API keys, passwords, tokens, or private keys found** in the repository.
- All Alpaca credentials (`ALPACA_KEY`, `ALPACA_SECRET`, etc.) are loaded via `os.getenv()` / `dotenv`.
- `.env.example` contains only empty placeholder variables — no real values.
- No `.pem`, `.key`, or `PRIVATE KEY` files in the tracked tree.
- `.gitignore` covers `.env`, `*.pem`, and state/data directories.

### Insecure Network Calls

- **No `verify=False`** detected anywhere in the codebase.
- **No `NODE_TLS_REJECT_UNAUTHORIZED=0`** in code (only mentioned in this automation's own runbook doc).
- **No `pickle.loads`** on untrusted data.
- Alpaca API base URLs default to `https://` endpoints.

### Dependency Notes

| Package | Pinned Version | Note |
|---------|---------------|------|
| `requests` | `2.31.0` | CVE-2024-35195 (moderate) — upgrade recommended |
| `urllib3` | `1.26.20` | 1.x branch; monitor for EOL. Compatible with requests pin. |
| `paramiko` | `3.4.0` | Current stable; no known critical CVEs at time of scan. |
| `flask` | `3.0.0` | Current major; no known critical CVEs. |

---

### Recommendations

1. **Upgrade `requests` to ≥2.32.0** to remediate CVE-2024-35195 (session header leak on cross-origin redirect). Verify `alpaca-trade-api==3.2.0` compatibility first.
2. **Consider replacing `os.system()` calls with `subprocess.run([...], shell=False)`** in `scripts/run_uw_intel_on_droplet.py` and similar scripts. While current usage is safe (no external input), `shell=False` is defense-in-depth.
3. **Add `pip-audit` to CI** to catch dependency CVEs automatically on every push.
4. **Document the `exec(base64.b64decode(...))` remote-execution pattern** — it's intentional for droplet deployment, but a new contributor could inadvertently introduce an injection vector if they interpolate user input into the encoded payload.

---

**Verdict:** No HIGH or CRITICAL findings. No GitHub issue required.
