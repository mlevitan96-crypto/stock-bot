## Security Review (push to main)

**Commit / ref:** `d00a1dd7df1b137e43990d9b3b3e9ed14cf58817`
**Message:** `fix(ml): omnibus RF anti-leakage and report target line`
**Author:** Mark (mlevitan96@gmail.com)
**Changed file:** `scripts/ml/omnibus_discovery_lab.py` (21 insertions, 15 deletions)
**Date:** 2026-04-21

---

### Findings

| Severity | Location | Description |
|----------|----------|-------------|
| **CLEAN** | `scripts/ml/omnibus_discovery_lab.py` | Changed file contains no secrets, no `eval`/`exec`, no unsafe patterns, no network calls. Pure offline ML lab script. |
| MEDIUM | `reports/_daily_review_tools/run_droplet_weight_tuning_summary.py:36` (and 5 similar files) | Uses `base64 + exec()` pattern to execute Python on remote droplet via SSH. The payloads are generated from local tracked scripts (not user/external input), so this is **not RCE from untrusted sources**, but the pattern warrants awareness. |
| MEDIUM | `execute_droplet_audit.py:24`, `deep_trading_diagnosis.py:13`, `comprehensive_no_positions_investigation.py:16`, and ~12 more in `scripts/audit/`, `archive/` | `subprocess.run(..., shell=True, ...)` — commands are hardcoded/operator-controlled strings with timeouts, not constructed from external input. Low exploitability but shell injection surface exists if inputs change. |
| MEDIUM | `force_cycle_run.py:15` | `exec(f.read(), ...)` to activate a virtualenv. Standard venv activation pattern; file path is hardcoded. |
| MEDIUM | `complete_droplet_verification.py:85` | `exec(import_stmt)` where `import_stmt` values are hardcoded in a dict literal. No external input path. |
| LOW | `requirements.txt` | `flask==3.0.0`, `requests==2.31.0`, `urllib3==1.26.20`, `paramiko==3.4.0` — consider running `pip-audit` in CI to check for CVEs in pinned versions. `urllib3<2` is pinned for `alpaca-trade-api` compat. |
| **CLEAN** | Full tree — secrets scan | No hardcoded API keys, tokens, private keys, or credential values found in tracked files. `.env` is gitignored and no `.env` files are committed. All credential access uses `os.getenv()` / `os.environ.get()`. |
| **CLEAN** | Full tree — TLS/cert verification | No `verify=False` found. No `NODE_TLS_REJECT_UNAUTHORIZED=0`. |
| **CLEAN** | Full tree — network calls | All `requests.*()` calls include explicit `timeout=` parameters. No sensitive endpoints called over plain HTTP (only localhost health checks). |
| **CLEAN** | Full tree — SQL injection | No raw SQL string concatenation found. Only file reference is `off_leash_alpaca_hunt.py` matching "sqlite" as a log-grep keyword. |

### Summary

**The pushed commit (`d00a1dd7`) is clean.** It modifies a single offline ML lab script (`omnibus_discovery_lab.py`) to fix Random Forest anti-leakage by excluding sibling PnL columns and simulation outputs from the feature matrix. No secrets, no unsafe patterns, no network code.

**Repository-wide observations (pre-existing, not introduced by this push):**

1. **`exec()` + base64 pattern for droplet scripts** — ~8 files use `base64.b64encode` + `exec(base64.b64decode(...))` to run local Python on a remote droplet via SSH. The payloads originate from tracked scripts, not user input, so this is controlled remote execution rather than arbitrary RCE. Recommend documenting this pattern for future auditors.

2. **`shell=True` in subprocess calls** — ~15 files use `subprocess.run(..., shell=True, ...)`. All have hardcoded commands and timeouts. No user-controlled input flows into these commands currently.

3. **Dependency versions** — Pinned versions in `requirements.txt` should be periodically audited via `pip-audit`. No known critical CVEs flagged by pattern alone, but automated scanning in CI is recommended.

### Recommendations

1. **No action required for this push** — the commit is safe.
2. **CI Enhancement (MEDIUM):** Add `pip-audit` to CI pipeline for automated dependency vulnerability scanning.
3. **Documentation (LOW):** Document the base64+exec droplet execution pattern in `MEMORY_BANK_ALPACA.md` or an ops runbook so future reviewers understand the trust boundary.
4. **Housekeeping (LOW):** Consider replacing `shell=True` with explicit argument lists in subprocess calls where practical, to reduce shell injection surface area.
