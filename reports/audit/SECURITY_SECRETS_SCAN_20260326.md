# Security Secrets Scan Report

**Date:** 2026-03-26  
**Scope:** Full repository tree at `/workspace`  
**Branch:** `cursor/stock-bot-security-review-e08b`  
**Exclusions:** `.env.example`, `node_modules/`, `.git/`, `__pycache__/`, documentation that only describes env var names without actual values  

---

## Executive Summary

**No CRITICAL hardcoded secrets (API keys, passwords, tokens) were found in the current codebase.** All credential access uses proper `os.getenv()` / `os.environ.get()` patterns. The `.gitignore` correctly excludes `.env` and `droplet_config.json`.

However, several **HIGH** and **MEDIUM** severity information-disclosure findings were identified, primarily involving exposed server IP addresses, a personal email address in committed scripts, and historical git commits that triggered GitHub's secret scanning (PAT tokens in old commits).

---

## Findings

### HIGH Severity

| # | File | Line(s) | Pattern | Description | Classification |
|---|------|---------|---------|-------------|----------------|
| H-1 | `droplet_config.example.json` | 9 | IP address | Production server IP `104.236.102.57` hardcoded in example config file committed to repo. Reveals attack surface. | Confirmed info leak |
| H-2 | `MEMORY_BANK.md` | 1142, 1160, 1165, 1177-1178, 1187, 1346 | IP address | Production droplet IP `104.236.102.57` documented in committed memory bank. Also mentions forbidden IP `147.182.255.165` (different server). Dashboard URL `http://104.236.102.57:5000/` exposed. | Confirmed info leak |
| H-3 | `reports/audit/ALPACA_DROPLET_SERVICE_HEALTH_20260327_0200Z.md` | 425, 468, 474 | IP address | Production IP in committed service health logs showing Flask binding to `http://104.236.102.57:5000` and `:5001`. | Confirmed info leak |
| H-4 | `reports/audit/ALPACA_SERVICE_HEALTH_20260326_1707Z.md` | 22, 68 | IP address | Same production IP in committed audit reports. | Confirmed info leak |
| H-5 | Multiple report JSON files | Various | IP addresses | Client IP `75.167.147.249` appears in committed dashboard access logs within report JSON files (4+ files). Leaks client/operator IP. | Confirmed info leak |
| H-6 | `PUSH_TO_GITHUB.md` | 16 | Secret scanning alert | References GitHub secret-scanning unblock URL, confirming a real GitHub PAT was detected in historical commits. | Historical secret in git history |
| H-7 | `PUSH_STATUS.md` | 18 | Secret scanning alert | Confirms GitHub PAT detected in commits `3e269ec`, `a94d48c`, `a534153`, `b83738a`. Token may still be in git history. | Historical secret in git history |
| H-8 | `archive/documentation/completion_summaries/FIXES_SUMMARY.md` | 42 | Secret scanning alert | Third reference to unblock URL for secrets in commit history. | Historical secret in git history |
| H-9 | `NEXT_STEPS_DEPLOYMENT.md` | 17 | Secret scanning alert | Fourth reference to unblock URL for secrets in commit history. | Historical secret in git history |

### MEDIUM Severity

| # | File | Line(s) | Pattern | Description | Classification |
|---|------|---------|---------|-------------|----------------|
| M-1 | `archive/scripts/deployment_scripts/push_to_github.sh` | 17 | Email | Personal email `mlevitan96@gmail.com` hardcoded in deployment script. | Info disclosure |
| M-2 | `archive/scripts/deployment_scripts/push_to_github_clean.sh` | 14 | Email | Same personal email hardcoded. | Info disclosure |
| M-3 | `archive/scripts/deployment_scripts/setup_github_export.sh` | 56-57 | Email | Personal email + username hardcoded in git config setup. | Info disclosure |
| M-4 | `archive/scripts/deployment_scripts/resolve_and_setup.sh` | 85-91 | Email | Personal email + username hardcoded. | Info disclosure |
| M-5 | `archive/scripts/deployment_scripts/setup_droplet_git.sh` | 29 | Token pattern | `https://YOUR_GITHUB_TOKEN@github.com/...` - placeholder in git remote URL. If filled with real token on droplet, token persists in `.git/config`. | Unsafe credential pattern |
| M-6 | `archive/scripts/deployment_scripts/push_to_github.sh` | 98 | Token pattern | `https://${GITHUB_TOKEN}@github.com/...` - embeds token in git remote URL, which persists in `.git/config` and can be read by any process. | Unsafe credential pattern |
| M-7 | `archive/scripts/deployment_scripts/push_to_github_clean.sh` | 81 | Token pattern | Same pattern as M-6 — token embedded in remote URL. | Unsafe credential pattern |
| M-8 | `deploy_supervisor.py` | 383-384 | Hardcoded test creds | Chaos mode sets `ALPACA_KEY = "INVALID_KEY"` and `ALPACA_SECRET = "INVALID_SECRET"` in env. Obviously fake, but pattern of overriding env vars in code is risky. | Test/fake value |
| M-9 | `DROPLET_GIT_SETUP.md` | 7-8, 48, 339 | IP + token pattern | Documents droplet IP `104.236.102.57` and `https://YOUR_GITHUB_TOKEN@github.com/...` setup instructions. | Info disclosure + unsafe pattern |
| M-10 | `archive/scripts/deployment_scripts/push_to_github.sh` | 10 | Source .env broadly | `export $(cat .env \| grep -v '^#' \| xargs)` exports ALL .env vars into shell environment, which can leak secrets to child processes. | Unsafe secret handling |

### LOW Severity (Env var references only — SAFE)

| # | Pattern | File Count | Description |
|---|---------|------------|-------------|
| L-1 | `os.getenv("ALPACA_KEY")` | 30+ files | Proper env var reference. No hardcoded values. |
| L-2 | `os.getenv("ALPACA_SECRET")` | 30+ files | Proper env var reference. |
| L-3 | `os.getenv("UW_API_KEY")` | 20+ files | Proper env var reference. |
| L-4 | `os.getenv("TELEGRAM_BOT_TOKEN")` | 10+ files | Proper env var reference. |
| L-5 | `os.getenv("TELEGRAM_CHAT_ID")` | 10+ files | Proper env var reference. |
| L-6 | `os.getenv("GITHUB_TOKEN")` | 3+ files | Proper env var reference. |
| L-7 | `os.getenv("FRED_API_KEY")` | 1 file | Proper env var reference (default empty string). |
| L-8 | `os.getenv("DROPLET_PASSWORD")` | 1 file | Proper env var reference in droplet_client.py. |
| L-9 | `get_env("ALPACA_BASE_URL", ...)` | config/registry.py | Proper env var with safe default URL. |

---

## Positive Security Findings

1. **`.gitignore` is properly configured:**
   - `.env` and `*.env` are excluded (line 1-3)
   - `droplet_config.json` is excluded (line 6)
   - State files, logs, and `.jsonl` files are excluded

2. **No hardcoded API keys or tokens:** All 60+ credential-access sites use `os.getenv()` or the `get_env()` wrapper.

3. **No private keys or PEM content:** No `PRIVATE KEY` blocks, `.pem` files with key content, or SSH keys found in the repository.

4. **No connection strings with embedded credentials:** No `mongodb://user:pass@`, `postgres://`, etc.

5. **No Slack tokens, AWS keys, or Stripe keys:** Searched for `xoxb-`, `AKIA`, `sk-live_`, `pk_live_` — none found.

6. **No Telegram bot tokens hardcoded:** All Telegram access uses `os.environ.get("TELEGRAM_BOT_TOKEN")`.

7. **No webhook URLs with secrets:** No hardcoded webhook endpoints found.

---

## Recommendations

### Immediate (address now)

1. **Rotate the GitHub PAT** that was detected in historical commits (H-6 through H-9). Even if allowed via GitHub's unblock URL, the token is in git history forever.

2. **Redact server IP from `droplet_config.example.json`** (H-1). Replace `104.236.102.57` with `YOUR_DROPLET_IP` or `192.0.2.1` (documentation IP).

3. **Redact production IPs from committed report/audit files** (H-3, H-4, H-5). Consider adding `reports/audit/*.md` and `reports/*.json` to `.gitignore` if they contain operational data, or scrub IPs before committing.

### Short-term

4. **Redact IP from `MEMORY_BANK.md`** (H-2) or accept the risk given it's an operational reference doc. At minimum, remove the dashboard URL with port.

5. **Remove personal email from deployment scripts** (M-1 through M-4). Use `mlevitan96-crypto@users.noreply.github.com` consistently instead of the personal Gmail.

6. **Stop embedding tokens in git remote URLs** (M-5 through M-7). Use `git credential.helper` or SSH keys instead of `https://TOKEN@github.com` patterns, which persist tokens in `.git/config`.

7. **Replace broad `.env` export** in `push_to_github.sh` (M-10) with targeted variable loading.

### Long-term

8. **Run `git filter-repo`** to remove PAT tokens from git history entirely, then force-push.

9. **Add a pre-commit hook** (e.g., `detect-secrets` or `gitleaks`) to prevent future secret commits.

10. **Consider IP allowlisting** for the dashboard instead of exposing it on `0.0.0.0:5000`.

---

## Scan Methodology

- **Files scanned:** ~2,046 code and configuration files (`.py`, `.json`, `.yaml`, `.yml`, `.toml`, `.cfg`, `.ini`, `.conf`, `.env`, `.sh`, `.bash`, `.js`, `.ts`, `.md`, `.txt`)
- **Patterns searched:**
  - API keys: `ALPACA_`, `SECRET_`, `api_key=`, `apikey=`, `api-key`, `AKIA`, `sk-`, `pk_live_`
  - Passwords: `PASSWORD=`, `password=`, `passwd=`
  - Tokens: `token=`, `Bearer`, `AUTH_TOKEN`, `access_token=`, `ghp_`, `github_pat_`, `xoxb-`, `bot[0-9]+:`
  - Private keys: `PRIVATE KEY`, `.pem` references, `ssh-rsa`, `ssh-ed25519`
  - Connection strings: `mongodb://`, `postgres://`, `mysql://`, `redis://`, `amqp://` with embedded credentials
  - Long random strings: Base64 patterns (40+ chars) assigned to sensitive variables
  - Webhook URLs with embedded secrets
- **Exclusions applied:** `.env.example`, `node_modules/`, `.git/`, `__pycache__/`, placeholder values (`your_key_here`, `YOUR_TOKEN`, etc.)
