# Monday Market Open Readiness

**Date:** 2026-03-08 **Time (UTC):** 2026-03-08_2155

**Verdict:** PASS

## Evidence

- Proof folder: `C:\Dev\stock-bot\reports\audit\MONDAY_OPEN_READINESS_PROOF_2026-03-08_2155`

## Phases

- **0_authority:** {"hostname": "ubuntu-s-1vcpu-2gb-nyc3-01-alpaca", "commit": "25f5df1ae6fe", "raw": "ubuntu-s-1vcpu-2gb-nyc3-01-alpaca\n25f5df1ae6fed9090f755a54f8b51a52ffc6eca0\n2026-03-08T21:55:25Z\nPython 3.12.3\n"}...
- **1_sre:** {"disk_ok": true, "services_raw": "active\n789863 /root/stock-bot/venv/bin/python -u dashboard.py\n790063 bash -c cd /root/stock-bot && systemctl is-active stock-bot 2>/dev/null || echo 'inactive'; pg...
- **2_paper:** {"paper_only_verified": true, "snippet_redacted": "TRADING_MODE and ALPACA_BASE_URL checked (values not logged)."}...
- **3_config:** {"b2_mode": "live_paper", "b2_live_paper_enabled": true, "b2_live_enabled": false}...
- **4_data:** {"append_ok": true}...
- **5_alpaca:** {"account_ok": true, "clock_ok": true}...
- **6_smoke:** {"exit_code": 0, "output_tail": "MONDAY_SMOKE_TEST wrote /root/stock-bot/reports/audit/MONDAY_SMOKE_TEST_2026-03-08_2155.json (2 symbols, 0.0s)\n"}...
- **7_dashboard:** {"key_endpoints_ok": true}...
- **8_csa:** {"parse_warning": true, "cockpit_updated": true}...
- **9_cron:** {"cron_listed": true}...

## Monday 9:29am operator steps (30s runbook)

1. Confirm PAPER mode: `grep TRADING_MODE .env` on droplet → PAPER
2. Confirm Alpaca paper: `curl -s https://paper-api.alpaca.markets/...` or dashboard SRE health
3. Confirm dashboard last update: check Telemetry Health / Profitability tab freshness
4. Kill switch: set TRADING_MODE=HALT or stop stock-bot service; document in runbook.

## Adverse review (CSA + SRE)

- **Stock-bot alive:** Phase 1 proof shows `active` and dashboard.py process; heartbeat/cockpit proof in `MONDAY_OPEN_READINESS_PROOF_2026-03-08_2155/adverse_review_heartbeat_cockpit.txt`.
- **Smoke test no submit:** `run_monday_open_smoke_test.py` outputs `no_submit_assertion` and `submit_attempted: []` in MONDAY_SMOKE_TEST_*.json; does not import alpaca_client for submit.
- **Dashboard no 500s:** phase7_key_endpoints.txt: learning_readiness:200, telemetry_health:200, profitability_learning:200.
- **Cockpit updated:** phase8_cockpit_update.txt shows "Profitability Cockpit updated" and cockpit_updated: true in results.
