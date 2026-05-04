# Security Review (push to main)

**Commit / ref:** `f764c2258401c74dd1058292716e328ff01bd387` — `chore(config): disable legacy equity strategy and lock to Wheel-only mode`  
**Changed files:** `config/strategies.yaml`  
**Scan scope:** Full repository tree  
**Date:** 2026-05-04  

---

## Findings

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| 1 | MEDIUM | `reports/_daily_review_tools/run_droplet_*.py` (5 files) | `exec(base64.b64decode(...))` used to run local Python payloads on the remote droplet via SSH. The base64-encoded content is read from committed `.py` files in the repo, not from user input, so there is no RCE from external sources. However, this pattern is fragile — if any of the source scripts were tampered with via supply-chain compromise, the base64+exec pipeline would amplify the blast radius. |
| 2 | MEDIUM | `complete_droplet_verification.py:85` | `exec(import_stmt)` with hardcoded import strings from a dict literal. Not user-controlled, but using `importlib.import_module()` would be more auditable and less likely to mask injection if refactored. |
| 3 | MEDIUM | `force_cycle_run.py:15` | `exec(f.read(), {'__file__': activate_this})` to activate a virtualenv. Standard `venv` bootstrap pattern; low risk since the file path is a hardcoded literal (`/root/stock-bot/venv/bin/activate_this.py`). |
| 4 | MEDIUM | `comprehensive_no_positions_investigation.py:16`, `scripts/audit/run_exec_mode_*.py`, `scripts/alpaca_blocker_closure_mission.py:31`, `scripts/alpaca_rampant_analysis_mission.py:40`, + ~10 archive scripts | `subprocess.run(cmd, shell=True, ...)` with string commands. In all scanned cases the commands are internally constructed (no external/user input concatenation). `shell=True` with hardcoded strings is an elevated-privilege anti-pattern but not exploitable as-is. |
| 5 | LOW | `requirements.txt` | `flask==3.0.0` — Flask 3.0.0 was released Dec 2023. Recommend running `pip-audit` in CI to flag any known CVEs. `urllib3==1.26.20` is pinned to the 1.x line (by `alpaca-trade-api` constraint); upstream support for 1.x is in maintenance mode. `requests==2.31.0` and `paramiko==3.4.0` should also be checked via `pip-audit`. |
| 6 | LOW | `check_positions_simple.py:7` | Directly accesses `Config.ALPACA_KEY` / `Config.ALPACA_SECRET` — these are loaded from env vars (via `get_alpaca_trading_credentials()` in `main.py`), not hardcoded. Correct pattern. Noted for completeness. |
| 7 | LOW | `zero_downtime_deploy.py`, `comprehensive_system_check.py`, archive scripts | HTTP calls to `localhost` / `127.0.0.1` for health checks. These are internal-only, not sensitive-data endpoints. No external HTTP found for credential-bearing calls. |

---

## Secrets & Credential Leak Scan

- **No hardcoded API keys, tokens, or passwords found** in source code (`.py`, `.yaml`, `.json`, `.toml`, `.cfg`, `.sh`).
- All Alpaca credentials are loaded from environment variables via `Config` class (`main.py:402`), which calls `get_alpaca_trading_credentials()` → `os.getenv(...)`.
- `.gitignore` correctly excludes `.env` and `*.env`. No `.env` file is committed. `.env.example` contains only placeholder variable names (no values).
- No `.pem` files or private key material committed.

## Unsafe Pattern Scan

- **No `pickle.loads()`** usage found.
- **No SQL string concatenation** found.
- **No `verify=False`** or disabled TLS verification found.
- **`eval()` not used** anywhere in the repository.
- `exec()` and `shell=True` usage (findings #1–4 above) are all internal/operator-tooling with hardcoded inputs, not user-facing.
- `__import__()` used in several test/utility scripts for sys.path manipulation and lazy stdlib imports — no security concern (no external input).

## Insecure Network Calls

- All `requests.get/post` calls include explicit `timeout` parameters (verified across 20+ call sites).
- No `verify=False` in any `requests` call.
- No `NODE_TLS_REJECT_UNAUTHORIZED=0` found.
- External HTTPS endpoints (Alpaca API, Unusual Whales API, Telegram API) all use HTTPS.

## Dependency Notes

- **Recommend adding `pip-audit` to CI** to catch CVEs in `flask`, `urllib3`, `requests`, `paramiko`, `alpaca-trade-api`.
- `urllib3` is pinned to `1.26.20` (legacy line) due to `alpaca-trade-api==3.2.0` constraint. When `alpaca-trade-api` updates, migrate to `urllib3>=2`.

---

## Recommendations

1. **CI: Add `pip-audit`** — Automate dependency vulnerability scanning in the CI pipeline.
2. **Replace `exec()` with `importlib`** — In `complete_droplet_verification.py`, use `importlib.import_module()` instead of `exec()` for import testing.
3. **Replace `shell=True`** — Where feasible, pass command lists to `subprocess.run()` instead of `shell=True` with string commands.
4. **Audit droplet exec pipeline** — The base64+exec pattern in `reports/_daily_review_tools/` works but couples code integrity to the committed script files. Consider a more transparent remote-execution method (e.g., `rsync` + direct Python invocation).
5. **Pin and audit `paramiko`** — Paramiko handles SSH; keep it updated and audit for any CVEs.

---

**Verdict:** No CRITICAL or HIGH findings. The push (`f764c225`) only changed `config/strategies.yaml` (strategy toggle), introducing no new security concerns. Pre-existing patterns are MEDIUM/LOW and documented above for ongoing hygiene.
