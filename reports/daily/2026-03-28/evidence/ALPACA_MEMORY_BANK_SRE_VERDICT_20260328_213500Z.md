# SRE verdict — Alpaca MEMORY_BANK hardening (`20260328_213500Z`)

**Scope:** Operational accuracy of MEMORY_BANK against **live** `ubuntu-s-1vcpu-2gb-nyc3-01-alpaca` (read-only).

## Operational accuracy

| Check | Result |
|-------|--------|
| **stock-bot.service** `ExecStart` matches live (`systemd_start.sh` → venv → `deploy_supervisor.py`) | **PASS** |
| **`trading-bot.service`** documented as **not-found** on verified host | **PASS** |
| **Dashboard :5000** owner documented as **`stock-bot-dashboard.service`** + `/usr/bin/python3` | **PASS** |
| Dual **dashboard** / dual **UW** possibilities called out (supervisor vs standalone units) | **PASS** |
| **Failed units** listed as observational SRE signals (no auto-remediation implied in MEMORY text) | **PASS** |
| Telegram split **`.alpaca_env` / `.env`** matches inspection | **PASS** |
| Canonical path **`/root/stock-bot`** only on verify; alternate roots labeled script portability | **PASS** |

## Recovery / completeness

| Check | Result |
|-------|--------|
| Existing deploy hygiene (**`pkill` dashboard**, restart patterns) retained and reconciled with dual-unit reality | **PASS** |
| Operators directed to re-audit when host changes | **PASS** |

## Verdict token

**`SRE_MEMORY_BANK_HARDENING_OK`**
