# Security Review: Insecure Network Call Patterns

**Date:** 2026-03-26  
**Scope:** Full repository scan (`/workspace`), excluding `node_modules/`, `.git/`, `__pycache__/`  
**Reviewer:** Automated Security Scan (Cursor Cloud Agent)

---

## Executive Summary

Scanned **2,080 source files** across the repository. Found **0 HIGH-severity** issues (no disabled TLS verification in production code), but identified multiple **MEDIUM** and **LOW** severity findings related to plaintext HTTP to production IPs, missing timeouts on `urllib` calls, hardcoded production IP addresses, and `AutoAddPolicy` usage in SSH clients. No `ws://` websocket issues found. No CI dependency audit tooling detected.

---

## Findings

### CATEGORY 1: HTTP (Not HTTPS) for Sensitive API Endpoints

No instances of `http://` used for external API calls (Alpaca, Unusual Whales, Telegram, FRED). All external API traffic uses HTTPS. Local inter-service calls (`http://localhost`, `http://127.0.0.1`) are acceptable.

**However**, plaintext HTTP is used to access the **production dashboard** over the public internet:

| # | Severity | File | Line(s) | Description | Prod/Dev |
|---|----------|------|---------|-------------|----------|
| 1.1 | **MEDIUM** | `deploy_dashboard_ssh_direct.py` | 164, 167-169 | Prints `http://104.236.102.57:5000/` URLs directing users to access production dashboard over plaintext HTTP | Deploy tooling (but directs to prod) |
| 1.2 | **MEDIUM** | `deploy_dashboard_via_ssh.py` | 137, 141-143 | Same: prints `http://104.236.102.57:5000/` for dashboard access | Deploy tooling |
| 1.3 | **MEDIUM** | `deploy_dashboard_fixes_ssh.py` | 154, 157-159 | Same: prints `http://104.236.102.57:5000/` URLs | Deploy tooling |
| 1.4 | **MEDIUM** | `DEPLOY_DASHBOARD_NOW.sh` | 64, 67-69 | Same: echoes `http://104.236.102.57:5000/` URLs | Deploy script |
| 1.5 | **LOW** | `main.py` | 14582 | `app.run(host="0.0.0.0", ...)` — Flask API bound to all interfaces without TLS. Acceptable if behind a reverse proxy; risky if directly exposed. | Production |
| 1.6 | **LOW** | `dashboard.py` | 6716 | `app.run(host="0.0.0.0", ...)` — Dashboard bound to all interfaces without TLS. Same concern. | Production |

**Recommendation:** Add TLS termination via a reverse proxy (nginx/caddy) in front of both Flask services on the droplet. Update deploy scripts to print `https://` URLs.

---

### CATEGORY 2: Disabled Certificate Verification

| # | Severity | File | Line(s) | Description | Prod/Dev |
|---|----------|------|---------|-------------|----------|
| — | — | — | — | **No findings.** No instances of `verify=False`, `NODE_TLS_REJECT_UNAUTHORIZED=0`, `ssl._create_unverified_context`, `CERT_NONE`, or `check_hostname=False` found in any source file. | — |

**Status:** PASS — No disabled TLS verification anywhere in the codebase.

---

### CATEGORY 3: Missing Timeouts on Network Calls

All `requests.get/post` calls in the codebase include explicit `timeout=` parameters. Good practice.

One `urllib` call is missing a timeout:

| # | Severity | File | Line(s) | Description | Prod/Dev |
|---|----------|------|---------|-------------|----------|
| 3.1 | **MEDIUM** | `scripts/github_close_pr.py` | 41 | `urllib.request.urlopen(req)` — no timeout. Could hang indefinitely if GitHub API is unresponsive. | Script/dev tooling |

All other `urllib.request.urlopen` calls include timeouts (10s, 15s, 60s).

**Recommendation:** Add `timeout=30` to the `urlopen` call in `scripts/github_close_pr.py` line 41.

---

### CATEGORY 4: urllib/urllib2/urllib3 Calls Without Proper SSL Verification

| # | Severity | File | Line(s) | Description | Prod/Dev |
|---|----------|------|---------|-------------|----------|
| — | — | — | — | **No findings.** All `urllib.request` calls use default SSL verification (Python's default verifies certificates). No `ssl._create_unverified_context` or `CERT_NONE` usage found. | — |

**Status:** PASS — All urllib calls use default (verified) SSL contexts.

---

### CATEGORY 5: Insecure WebSocket Connections (ws:// vs wss://)

| # | Severity | File | Line(s) | Description | Prod/Dev |
|---|----------|------|---------|-------------|----------|
| — | — | — | — | **No findings.** No `ws://` or `wss://` WebSocket URLs found in any source file. | — |

**Status:** PASS — No WebSocket usage detected in the codebase.

---

### CATEGORY 6: Hardcoded IP Addresses for Production Services

| # | Severity | File | Line(s) | Description | Prod/Dev |
|---|----------|------|---------|-------------|----------|
| 6.1 | **MEDIUM** | `deploy_dashboard_fixes_ssh.py` | 39 | `deploy_target = "root@104.236.102.57"` — hardcoded production droplet IP | Deploy tooling |
| 6.2 | **MEDIUM** | `deploy_supervisor.py` | 96 | `expected_ip = "104.236.102.57"` — hardcoded expected IP for deployment verification | Deploy tooling |
| 6.3 | **MEDIUM** | `DEPLOY_WEIGHTS_FIX.py` | 16 | `DEPLOY_TARGET = "104.236.102.57"` — hardcoded production droplet IP | Deploy tooling |
| 6.4 | **MEDIUM** | `scripts/audit/ethos_enforcement.py` | 19, 47 | `STOCK_BOT_IP = "104.236.102.57"` — hardcoded in enforcement script | Audit script |
| 6.5 | **LOW** | `deploy_dashboard_ssh_direct.py` | 164-169 | References `104.236.102.57` in print statements | Deploy tooling |
| 6.6 | **LOW** | `deploy_dashboard_via_ssh.py` | 137-143 | References `104.236.102.57` in print statements | Deploy tooling |
| 6.7 | **LOW** | `DEPLOY_DASHBOARD_NOW.sh` | 64-69 | References `104.236.102.57` in echo statements | Deploy script |
| 6.8 | **LOW** | `droplet_config.example.json` | 9-10 | Comments reference `104.236.102.57` (documentation only) | Config template |

**Total:** IP `104.236.102.57` appears in **17+ files** across deploy scripts, audit tools, and documentation.

**Recommendation:** Centralize the production droplet IP in a single config file (e.g., `droplet_config.json`) or environment variable (`DROPLET_HOST`). All scripts should read from that source. The `droplet_client.py` already supports this pattern — extend it to all deploy scripts.

---

### CATEGORY 7: SSH Client Security (paramiko AutoAddPolicy)

| # | Severity | File | Line(s) | Description | Prod/Dev |
|---|----------|------|---------|-------------|----------|
| 7.1 | **MEDIUM** | `droplet_client.py` | 149 | `ssh.set_missing_host_key_policy(AutoAddPolicy())` — accepts any SSH host key without verification. Vulnerable to MITM on first connection. | Production tooling |
| 7.2 | **MEDIUM** | `report_data_fetcher.py` | 107 | `ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())` — same issue | Production tooling |
| 7.3 | **MEDIUM** | `fetch_droplet_data_and_generate_report.py` | 103 | `ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())` — same issue | Production tooling |

**Recommendation:** Use `paramiko.RejectPolicy()` (default) or `paramiko.WarningPolicy()` instead. Pre-populate `known_hosts` with the droplet's host key fingerprint.

---

### CATEGORY 8: Dependency Audit Tooling

| # | Severity | File | Line(s) | Description | Prod/Dev |
|---|----------|------|---------|-------------|----------|
| 8.1 | **LOW** | `requirements.txt` | — | No `pip-audit`, `safety`, or equivalent dependency scanning tool in requirements or CI pipeline | Project-wide |
| 8.2 | **LOW** | (none) | — | No `.github/workflows/` CI pipeline exists. No automated dependency auditing. | Project-wide |

**Current dependencies of note** (from `requirements.txt`):
- `requests==2.31.0` — pinned, should be checked for CVEs periodically
- `urllib3==1.26.20` — pinned to 1.x branch (forced by alpaca-trade-api compatibility). urllib3 1.x is in maintenance mode.
- `paramiko==3.4.0` — pinned, should be audited
- `flask==3.0.0` — pinned

**Recommendation:**
1. Add `pip-audit` to development dependencies and run it in CI/pre-commit.
2. Create a GitHub Actions workflow (`.github/workflows/security.yml`) that runs `pip-audit` on every PR.
3. Consider upgrading `urllib3` to 2.x when `alpaca-trade-api` supports it.

---

## Summary Table

| Severity | Count | Categories |
|----------|-------|------------|
| **HIGH** | 0 | — |
| **MEDIUM** | 10 | HTTP to prod IP (4), missing timeout (1), hardcoded IPs (4), SSH AutoAddPolicy (3) |
| **LOW** | 8 | Flask bind 0.0.0.0 (2), hardcoded IP in output (4), no dep auditing (2) |
| **PASS** | 4 categories | No disabled TLS verification, no insecure urllib SSL, no ws:// websockets, all requests calls have timeouts |

---

## Top 3 Recommended Actions

1. **Add TLS termination** (nginx/caddy reverse proxy) in front of Flask services on the droplet. The dashboard currently serves over plaintext HTTP on a public IP.

2. **Fix SSH host key verification** — Replace `AutoAddPolicy()` with `RejectPolicy()` or `WarningPolicy()` in `droplet_client.py`, `report_data_fetcher.py`, and `fetch_droplet_data_and_generate_report.py`. Pre-distribute the droplet's host key.

3. **Add dependency auditing to CI** — Install `pip-audit`, create a GitHub Actions workflow, and add it to pre-commit hooks. The pinned `urllib3==1.26.20` should be monitored for EOL/CVE status.

---

## Files Scanned

- **Total files examined:** 2,080
- **Python files:** ~1,800+
- **Shell scripts:** ~50+
- **YAML/JSON config:** ~200+
- **Patterns searched:** `http://` (non-localhost), `verify=False`, `NODE_TLS_REJECT_UNAUTHORIZED`, `requests.(get|post|put|delete)` without timeout, `urllib.request.urlopen` without timeout, `ssl._create_unverified_context`, `CERT_NONE`, `check_hostname=False`, `ws://`, hardcoded IP patterns, `AutoAddPolicy`, `shell=True` in subprocess, `debug=True` in Flask.
