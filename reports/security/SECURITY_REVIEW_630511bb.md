## Security Review (push to main)

**Commit / ref:** `630511bb0be3ff274b271e7308fd2c66c4f5773b`
**Message:** `fix(ml): exit sim verdict when VWAP/ATR columns mostly NaN`
**Changed file:** `scripts/ml/deep_correlation_matrix.py`
**Date:** 2026-04-21
**Pushed by:** mlevitan96-crypto

---

### Changed-File Scan

The single changed file (`scripts/ml/deep_correlation_matrix.py`) is **CLEAN**:
- No hardcoded secrets, API keys, tokens, or passwords.
- No `eval()`, `exec()`, `pickle`, `shell=True`, or unsafe deserialization.
- No network calls of any kind (pure offline data-processing script).
- No path-traversal risks (all paths derived from `--root` arg or `__file__`).

---

### Full-Tree Findings

| Severity | Location | Description |
|----------|----------|-------------|
| MEDIUM | `reports/_daily_review_tools/run_droplet_*.py`, `scripts/governance/_run_compare_on_droplet.py`, `scripts/governance/_inspect_droplet_exit.py`, `scripts/governance/_fetch_three_run_metrics.py` | `exec(base64.b64decode(...))` pattern for remote droplet execution over SSH. Payload is generated from local trusted scripts, not user input, but the pattern is inherently high-risk if the SSH channel or code generation were compromised. |
| MEDIUM | `execute_droplet_audit.py`, `deep_trading_diagnosis.py`, `comprehensive_no_positions_investigation.py`, `scripts/alpaca_telemetry_forward_proof.py`, `scripts/replay_week_multi_scenario.py`, `scripts/audit/run_*.py`, + ~10 archive scripts | `subprocess.run(..., shell=True, ...)` — all with hardcoded or operator-controlled command strings, not external user input. Acceptable for ops tooling but increases blast radius if any input becomes attacker-controlled. |
| MEDIUM | `complete_droplet_verification.py:85` | Bare `exec(import_stmt)` — dynamically executes import statements. Low risk (module names are hardcoded strings). |
| MEDIUM | `force_cycle_run.py:15` | `exec(f.read(), ...)` for virtualenv activation — standard pattern but executes file contents. |
| MEDIUM | `src/ml/alpha10_inference.py:86`, `src/ml/alpaca_shadow_scorer.py:107` | `joblib.load()` deserializes model files from local disk. Safe if model files are trusted; vulnerable to arbitrary code execution if an attacker replaces model files on disk. |
| MEDIUM | `dashboard.py:7548` | Dashboard binds `host="0.0.0.0"` on plain HTTP. Authenticated with HTTP Basic Auth (credentials from `.env`), but traffic is unencrypted. Acceptable for internal/VPN use; not suitable for public internet without a TLS reverse proxy. |
| MEDIUM | `requirements.txt` | `urllib3==1.26.20` — the 1.x line has known CVEs (e.g., CVE-2023-45803, CVE-2023-43804). Pinned for `alpaca-trade-api` compatibility. Consider upgrading when `alpaca-trade-api` supports urllib3 2.x. |
| LOW | Multiple scripts/docs | `http://127.0.0.1:*` loopback calls — acceptable for localhost-to-localhost service communication. |
| LOW | `scripts/run_uw_intel_on_droplet.py` | Multiple `os.system()` calls with `sys.executable` — controlled command strings, low risk. |

---

### Recommendations

1. **No immediate action required** — no CRITICAL or HIGH findings in this push or in the full tree.
2. **exec/base64 droplet pattern**: Consider migrating droplet remote execution to a structured RPC or dedicated deployment script rather than base64-encoding Python and executing over SSH. This reduces the attack surface if SSH credentials are compromised.
3. **joblib model loading**: Ensure model files (`models/paper_ml_gate/`) are integrity-checked (e.g., SHA256 hash verification) before loading to prevent arbitrary code execution via tampered `.joblib` files.
4. **Dashboard TLS**: Confirm a TLS termination proxy (nginx, Caddy, etc.) is in front of the dashboard on the production droplet. If not, add one to encrypt credentials and data in transit.
5. **urllib3 upgrade**: Track `alpaca-trade-api` releases for urllib3 2.x support and upgrade when available.
6. **Dependency audit**: Run `pip-audit` in CI to catch new CVEs in pinned dependencies automatically.

---

### Verdict

**PASS** — No HIGH or CRITICAL findings. No GitHub issue opened.
