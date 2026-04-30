# Security Review (push to main)

**Commit / ref:** `ee6880a712cf9bdf0cb770d7b1dd5285fe2e90af` — `fix(debug): syntax error in v2_killchain_last10 REPO path`
**Pushed by:** mlevitan96-crypto
**Date:** 2026-04-30
**Scope:** Full repository tree scan (triggered by push to main)

---

## Changed File

| File | Change |
|------|--------|
| `scripts/debug/v2_killchain_last10.py` | Removed stray `)` in `Path(__file__).resolve().parents[2]` assignment — pure syntax fix, no security implications. |

---

## Full-Tree Security Scan Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_run_compare_on_droplet.py`, `scripts/governance/_inspect_droplet_exit.py`, `scripts/governance/_fetch_three_run_metrics.py` | `exec(base64.b64decode(...))` used to ship local Python payloads to the remote droplet via SSH. The base64 content is read from **tracked repo files** (e.g. `droplet_weight_tuning_summary_payload.py`), not from user input. Risk is limited to the SSH trust boundary, but `exec` of decoded blobs is an inherently fragile pattern. |
| MEDIUM | `complete_droplet_verification.py:85` | `exec(import_stmt)` where `import_stmt` iterates a hardcoded dict of import statements. Not externally controllable. |
| MEDIUM | `force_cycle_run.py:15` | `exec(f.read(), ...)` to activate a virtualenv's `activate_this.py`. Standard pattern, but hardcoded path (`/root/stock-bot/venv/bin/activate_this.py`). |
| MEDIUM | ~30 files across `scripts/`, `archive/`, root | `subprocess.run(..., shell=True, ...)` — all instances use locally-constructed or hardcoded command strings (SSH commands, droplet diagnostics). None accept direct user/external input. Low exploitability but `shell=True` remains a best-practice concern. |
| LOW | `main.py:1551-1557` | `urllib.request.urlopen(req, timeout=10)` — WEBHOOK_URL is env-sourced. If the env var were set to an HTTP (non-TLS) URL, the webhook payload would travel unencrypted. No validation that the URL is HTTPS. |
| LOW | `requirements.txt` | `flask==3.0.0` — Flask 3.0.0 was the initial 3.x release; consider updating to latest 3.x for security patches. `paramiko==3.4.0` and `requests==2.31.0` should be audited via `pip-audit` in CI. |

---

## Negative Findings (No Issues)

| Category | Result |
|----------|--------|
| **Hardcoded secrets / API keys** | None found. All Alpaca, Telegram, and UW credentials are loaded via `os.getenv()` or `Config.*` backed by environment variables. |
| **`.env` file committed** | No `.env` file in the repository. |
| **`verify=False` (disabled TLS)** | Not found anywhere in Python files. |
| **`NODE_TLS_REJECT_UNAUTHORIZED=0`** | Not found. |
| **`pickle.load` / `shelve.open` / unsafe `yaml.load`** | Not found. |
| **`.pem` / private key files** | Not found. |
| **Hardcoded tokens (sk-*, ghp_*, Bearer + literal)** | Not found. |
| **Missing request timeouts** | All `requests.*()` calls inspected include explicit `timeout=` parameters. |
| **HTTP for sensitive API endpoints** | Alpaca API URLs are configured via env and default to `https://` paper/live endpoints. No hardcoded `http://` for broker or data APIs. |

---

## Recommendations

1. **CI dependency audit:** Add `pip-audit` to CI pipeline to catch CVEs in pinned dependencies (`flask`, `paramiko`, `requests`, `urllib3`, etc.) on every push.
2. **Reduce `exec()` surface:** The droplet-payload pattern (`base64 → exec`) works but is brittle. Consider writing the payload to a temp file on the remote and running it with `python3 /tmp/payload.py` instead of `exec(base64.b64decode(...))`. This makes remote debugging easier and reduces the `exec` footprint.
3. **Reduce `shell=True` surface:** Where feasible, convert `subprocess.run(cmd, shell=True, ...)` to list-form invocation (`subprocess.run([...])`) to eliminate shell-injection risk entirely, even for locally-constructed commands.
4. **Enforce HTTPS on webhook URL:** Add a startup validation in `Config` or `send_webhook` that rejects non-`https://` WEBHOOK_URL values (or at minimum logs a warning).
5. **Pin and update Flask:** Upgrade `flask==3.0.0` to latest 3.x patch release.

---

## Verdict

**No CRITICAL or HIGH findings.** All secrets are environment-sourced. The `exec`/`shell=True` patterns are internal-only (no external input) and represent MEDIUM best-practice concerns. No GitHub issue required for this push.
