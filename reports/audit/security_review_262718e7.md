## Security Review (push to main)

**Commit / ref:** `262718e78b62660ea3b639dbd9aae845632d4a56`  
**Message:** fix(alpaca): wire run_wheel into main loop and add liquidation script  
**Author:** Mark (mlevitan96@gmail.com)  
**Date:** 2026-05-04  
**Files changed:** `main.py`, `scripts/liquidate_legacy_equities.py`

---

### Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_run_compare_on_droplet.py`, `scripts/governance/_fetch_three_run_metrics.py`, `scripts/governance/_inspect_droplet_exit.py` | **Remote code execution via base64+exec over SSH.** Local Python scripts are base64-encoded and sent as `python3 -c 'exec(base64.b64decode(...))'` to the droplet. The payload is derived from tracked repo files (not user input), so the risk is supply-chain (a malicious commit to those scripts would run arbitrary code on the droplet). Mitigated by immutable-gitops policy but worth noting. |
| MEDIUM | `comprehensive_no_positions_investigation.py`, `check_droplet_trading_now.py`, `scripts/audit/run_exec_mode_*.py`, `run_diagnostic_via_ssh.py`, ~30 files in scripts/archive | **`subprocess.run(..., shell=True)` usage.** Commands are constructed from hardcoded strings or SSH wrappers, not from direct user input. No injection vector was identified, but shell=True adds implicit risk if any path includes externally-controlled data in the future. |
| MEDIUM | `complete_droplet_verification.py:85` | **`exec(import_stmt)` with hardcoded string dict.** Import statements are exec'd from a dictionary literal. Low practical risk (values are static), but using `importlib.import_module()` would be safer and more auditable. |
| LOW | All `requests.*()` calls observed | **All HTTP calls include explicit timeouts.** No missing-timeout violations found. Good practice already in place. |
| LOW | Network calls | **No `verify=False` or disabled TLS found.** All outbound calls use default certificate verification. |
| LOW | Secrets management | **No hardcoded secrets detected.** All API keys (`ALPACA_KEY`, `ALPACA_SECRET`, UW tokens) are loaded from environment variables or `.env` files. `.env` is properly gitignored. |
| LOW | Dependencies | **No `requirements.txt` lock file with pinned hashes found.** Consider running `pip-audit` in CI to catch known CVEs in dependencies. |

---

### Changed Files Assessment (this push)

| File | Assessment |
|------|-----------|
| `main.py` (diff: +29 lines) | **Clean.** Imports `run_wheel` from `src.wheel_manager`, uses `Config.*` for credentials (env-backed). No new unsafe patterns. Properly wrapped in try/except. |
| `scripts/liquidate_legacy_equities.py` (new, 190 lines) | **Clean.** No hardcoded secrets. Uses `tradeapi.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, ...)`. Has confirmation gate, systemd active check, and dry-run mode. No shell=True, no eval/exec. |

---

### Recommendations

1. **No action required for this push.** The changed files introduce no new security concerns.
2. **(Existing, pre-existing)** Consider replacing `base64+exec` SSH patterns with a proper remote-execution framework (e.g., Fabric/Invoke with explicit task definitions) to reduce supply-chain blast radius.
3. **(Existing, pre-existing)** Audit and minimize `shell=True` usage in subprocess calls — prefer passing command arrays where possible.
4. **(CI improvement)** Add `pip-audit` or `safety` to CI pipeline for automated dependency vulnerability scanning.

---

### Verdict

**No HIGH or CRITICAL findings.** All findings are MEDIUM (pre-existing patterns, not introduced by this push) or LOW (best-practice observations). No GitHub issue required.
