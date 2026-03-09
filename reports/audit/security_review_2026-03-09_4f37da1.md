# Security Review (push to main)

**Commit / ref:** `4f37da1c1b5fd3c61239ef1cc22218f3d276f9b4`
**Author:** Mark (mlevitan96@gmail.com)
**Message:** Add WHY WE DIDN'T WIN forensic: 6 artifacts, run on droplet
**Date:** 2026-03-09
**Changed files:**
- `scripts/audit/run_why_we_didnt_win_forensic.py` (added)
- `scripts/audit/run_why_we_didnt_win_on_droplet.py` (added)

---

## Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `scripts/audit/run_why_we_didnt_win_on_droplet.py:37` | **Unsanitized CLI arg in remote command.** `date_str` from argparse is interpolated directly into a shell command (`f"python3 ... --date {date_str}"`) executed on the remote droplet via `DropletClient._execute_with_cd()`. A malicious `--date` value with shell metacharacters (e.g. `; rm -rf /`) would be injected into the remote shell. Mitigated by: only run by trusted operators locally, not exposed to external input. |
| MEDIUM | `scripts/governance/_fetch_three_run_metrics.py:43`, `scripts/governance/_run_compare_on_droplet.py:17`, `scripts/governance/_inspect_droplet_exit.py:17`, `reports/_daily_review_tools/run_droplet_*.py` (5 files) | **`exec(base64.b64decode(...))` pattern for remote code execution.** Multiple scripts encode Python source as base64 and execute it on the droplet. Payloads are locally-authored hardcoded strings (not user input), but the pattern obscures code review and is inherently risky. |
| LOW | `execute_droplet_audit.py:24`, `deep_trading_diagnosis.py:13`, `deploy_dashboard_fixes_ssh.py:20`, `check_droplet_trading_now.py:17`, `scripts/replay_week_multi_scenario.py:17`, and ~10 archive scripts | **`subprocess.run(..., shell=True)` usage.** Commands are generally hardcoded or locally-constructed (not from untrusted input), but best practice is to use list-form arguments to avoid accidental shell injection. |
| LOW | `force_cycle_run.py:15` | **`exec(f.read())` to activate virtualenv.** Reads and executes a local virtualenv activation script. Path is hardcoded (`/root/stock-bot/venv/bin/activate_this.py`). Low risk but `exec()` should be used sparingly. |

---

## Detailed Analysis of Changed Files

### `scripts/audit/run_why_we_didnt_win_forensic.py` — CLEAN
- Pure data-analysis script: reads JSONL files, computes portfolio curve, exit lag, blocked-trade counterfactuals, and writes 6 JSON/Markdown artifacts.
- No network calls, no `exec()`/`eval()`, no secrets, no `shell=True`, no deserialization of untrusted data.
- Uses `json.loads()` on local JSONL files with proper error handling (`try/except json.JSONDecodeError`).
- File paths are all relative to the repo root, no path traversal risk.

### `scripts/audit/run_why_we_didnt_win_on_droplet.py` — ONE MEDIUM FINDING
- Uses `DropletClient()` to run the forensic script remotely and fetch artifacts.
- **Line 37:** `cmd = f"python3 scripts/audit/run_why_we_didnt_win_forensic.py --date {date_str}"` — the `date_str` is user-controllable via `--date` CLI flag and is not validated as a YYYY-MM-DD format before shell interpolation.
- Line 62: Uses `cat {remote}` with constructed paths — `remote` is built from constants and `date_str`, same injection surface.
- No hardcoded secrets; `DropletClient` presumably uses SSH keys/config from the environment.

---

## Secrets & Credentials Scan — PASS
- All Alpaca credentials (`ALPACA_KEY`, `ALPACA_SECRET`, `ALPACA_BASE_URL`) loaded via `os.getenv()` / `get_env()` — no hardcoded values.
- `UW_API_KEY` loaded via `get_env()`.
- No `.env` file committed to the repository.
- No private keys, `.pem` files, or Bearer tokens found in source.

## Insecure Network Calls — PASS
- No `verify=False` in any Python file.
- No `NODE_TLS_REJECT_UNAUTHORIZED=0`.
- HTTP URL references in `src/uw/uw_client.py` and `src/uw/uw_spec_loader.py` are URL validation/parsing logic, not insecure connections.

## Dependency Vulnerabilities — NOT ASSESSED
- No `pip-audit` or equivalent ran in this review. Recommend adding `pip-audit` to CI pipeline.

---

## Recommendations

1. **Validate `date_str` format** in `run_why_we_didnt_win_on_droplet.py` before interpolating into shell commands. Add a regex check: `re.fullmatch(r'\d{4}-\d{2}-\d{2}', date_str)` or use `shlex.quote()`.

2. **Consider replacing base64+exec pattern** in governance/daily-review scripts with a proper remote script execution model — e.g., `scp` the script to the droplet and run it, or maintain the scripts on the droplet and invoke by name. This would improve auditability and reduce the exec() surface.

3. **Prefer `subprocess.run(cmd_list)` over `shell=True`** in diagnostic scripts. Even for trusted commands, list-form invocation avoids accidental injection if commands are ever refactored to accept parameters.

4. **Add `pip-audit` to CI** to catch known dependency vulnerabilities on every push.

---

**Overall assessment: NO CRITICAL or HIGH findings. Two MEDIUM, several LOW. No action required beyond best-practice improvements.**
