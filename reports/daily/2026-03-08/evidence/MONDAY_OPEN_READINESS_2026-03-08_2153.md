# Monday Market Open Readiness

**Date:** 2026-03-08 **Time (UTC):** 2026-03-08_2153

**Verdict:** FAIL

## Evidence

- Proof folder: `C:\Dev\stock-bot\reports\audit\MONDAY_OPEN_READINESS_PROOF_2026-03-08_2153`

## Phases

- **0_authority:** {"hostname": "ubuntu-s-1vcpu-2gb-nyc3-01-alpaca", "commit": "7b9cf1de545a", "raw": "ubuntu-s-1vcpu-2gb-nyc3-01-alpaca\n7b9cf1de545a2da54a57cdbd88f46cfef9df9028\n2026-03-08T21:53:04Z\nPython 3.12.3\n"}...
- **1_sre:** {"disk_ok": true, "services_raw": "active\n693469 /root/stock-bot/venv/bin/python -u dashboard.py\n789531 bash -c cd /root/stock-bot && systemctl is-active stock-bot 2>/dev/null || echo 'inactive'; pg...
- **2_paper:** {"paper_only_verified": true, "snippet_redacted": "TRADING_MODE and ALPACA_BASE_URL checked (values not logged)."}...
- **3_config:** {"b2_mode": "live_paper", "b2_live_paper_enabled": true, "b2_live_enabled": false}...
- **4_data:** {"append_ok": true}...

## Monday 9:29am operator steps (30s runbook)

1. Confirm PAPER mode: `grep TRADING_MODE .env` on droplet → PAPER
2. Confirm Alpaca paper: `curl -s https://paper-api.alpaca.markets/...` or dashboard SRE health
3. Confirm dashboard last update: check Telemetry Health / Profitability tab freshness
4. Kill switch: set TRADING_MODE=HALT or stop stock-bot service; document in runbook.
