# ALPACA Memory Bank Canonical Update — `20260325_0205`

- **TRADING_ROOT:** `/root/stock-bot`
- **Generated (UTC):** 2026-03-25T00:09:27.957193+00:00

## Phase 0 — Baseline snapshot (SRE + CSA)

- **git HEAD:** `28abc2a33e365caa58736b99a175ae360f9d1447` (exit 0)
```
M data/dashboard_panel_inventory.json
 M data/uw_flow_cache.json
 M deploy/systemd/uw-flow-daemon.service
 M main.py
 M profiles.json
 M reports/DASHBOARD_ENDPOINT_AUDIT.md
 M reports/DASHBOARD_PANEL_INVENTORY.md
 M reports/DASHBOARD_TELEMETRY_DIAGNOSIS.md
 M reports/audit/CSA_SUMMARY_LATEST.md
 M reports/audit/CSA_VERDICT_LATEST.json
 M reports/board/PROFITABILITY_COCKPIT.md
 M reports/dashboard_audits/index.md
 M src/exit/exit_score_v2.py
 M uw_flow_daemon.py
 M weights.json
?? TELEGRAM_NOTIFICATION_LOG.md
?? config/tuning/active.json
?? docs/DATA_RETENTION_POLICY.md
?? replay/
?? reports/ALPACA_BLOCKER_CLOSURE_PROOF_20260325_0105.md
?? reports/ALPACA_BLOCKER_CLOSURE_PROOF_20260325_0112.md
?? reports/ALPACA_BOARD_REVIEW_20260316_0306/
?? reports/ALPACA_BOARD_REVIEW_20260316_0308/
?? reports/ALPACA_BOARD_REVIEW_20260316_0336/
?? reports/ALPACA_CONNECTIVITY_AUDIT_20260324_2206.md
?? reports/ALPACA_CONNECTIVITY_AUDIT_20260324_2213.md
?? reports/ALPACA_CONNECTIVITY_AUDIT_20260324_2216.md
?? reports/ALPACA_CONNECTIVITY_AUDIT_20260324_2220.md
?? reports/ALPACA_DATA_PATH_WIRING_PROOF_20260324_2301.md
?? reports/ALPACA_DATA_PATH_WIRING_PROOF_20260324_2303.md
?? reports/ALPACA_DATA_PATH_WIRING_PROOF_20260324_2304.md
?? reports/ALPACA_DATA_PATH_WIRING_PROOF_20260324_2305.md
?? reports/ALPACA_DATA_PATH_WIRING_PROOF_20260324_2306.md
?? reports/ALPACA_DATA_PATH_WIRING_PROOF_20260324_2307.md
?? reports/ALPACA_DATA_PATH_WIRING_PROOF_20260324_2310.md
?? reports/ALPACA_EXECUTION_COVERAGE_20260324_2119.md
?? reports/ALPACA_EXECUTION_COVERAGE_20260324_2121.md
?? reports/ALPACA_EXECUTION_COVERAGE_20260324_2122.md
?? reports/ALPACA_EXECUTION_COVERAGE_20260324_2123.md
?? reports/ALPACA_EXECUTION_COVERAGE_20260324_2124.md
```
### stock-bot.service (excerpt)
```
● stock-bot.service - Algorithmic Trading Bot
     Loaded: loaded (/etc/systemd/system/stock-bot.service; enabled; preset: enabled)
    Drop-In: /etc/systemd/system/stock-bot.service.d
             └─override.conf, paper-overlay.conf, truth.conf
     Active: active (running) since Tue 2026-03-24 23:55:21 UTC; 14min ago
   Main PID: 1498001 (systemd_start.s)
      Tasks: 33 (limit: 9483)
     Memory: 1.1G (peak: 1.6G)
        CPU: 39.928s
     CGroup: /system.slice/stock-bot.service
             ├─1498001 /bin/bash /root/stock-bot/systemd_start.sh
             ├─1498004 /root/stock-bot/venv/bin/python deploy_supervisor.py
             ├─1498014 /root/stock-bot/venv/bin/python -u dashboard.py
             ├─1498148 /root/stock-bot/venv/bin/python -u main.py
             └─1498165 /root/stock-bot/venv/bin/python heartbeat_keeper.py

Mar 25 00:09:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1498004]: [trading-bot] ERROR EXITS: Failed to close AMD (attempt 3/3): close_position_api_once returned None
Mar 25 00:09:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1498004]: [trading-bot] ERROR EXITS: All 3 attempts to close AMD failed
Mar 25 00:09:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1498004]: [trading-bot] WARNING EXITS: AMD could not be verified as closed after 3 attempts - keeping in tracking for retry
Mar 25 00:09:08 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1498004]: [trading-bot] DEBUG EXITS: Closing NVDA (decision_px=176.94, entry=175.29, hold=275.7min)
Mar 25 00:09:09 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1498004]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 1/3): close_position_api_once returned None
Mar 25 00:09:13 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1498004]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 2/3): close_position_api_once returned None
Mar 25 00:09:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1498004]: [trading-bot] ERROR EXITS: Failed to close NVDA (attempt 3/3): close_position_api_once returned None
Mar 25 00:09:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1498004]: [trading-bot] ERROR EXITS: All 3 attempts to close NVDA failed
Mar 25 00:09:18 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca systemd_start.sh[1498004]: [trading-bot] WARNING EXITS: NVDA could not be verified as closed after 3 attempts - keeping in tracking for retry

```
### uw-flow-daemon.service (excerpt)
```
● uw-flow-daemon.service - Unusual Whales Flow Daemon (single instance)
     Loaded: loaded (/etc/systemd/system/uw-flow-daemon.service; enabled; preset: enabled)
     Active: active (running) since Tue 2026-03-24 22:20:54 UTC; 1h 48min ago
   Main PID: 1491472 (python)
      Tasks: 1 (limit: 9483)
     Memory: 37.3M (peak: 50.5M)
        CPU: 3min 38.678s
     CGroup: /system.slice/uw-flow-daemon.service
             └─1491472 /root/stock-bot/venv/bin/python /root/stock-bot/uw_flow_daemon.py

Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [UW-DAEMON] Market is CLOSED (ET time: 20:09) - will use longer polling intervals
Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "insider:HOOD", "time_remaining": 72362.39325261116}
Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [UW-DAEMON] Market is CLOSED (ET time: 20:09) - will use longer polling intervals
Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "calendar:HOOD", "base_endpoint": "calendar", "force_first": false, "last": 1774381181.214821, "interval": 604800, "time_since_last": 16182.047539710999}
Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [UW-DAEMON] Market is CLOSED (ET time: 20:09) - will use longer polling intervals
Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "calendar:HOOD", "time_remaining": 588617.952460289}
Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [UW-DAEMON] Market is CLOSED (ET time: 20:09) - will use longer polling intervals
Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [DEBUG] uw_flow_daemon.py:should_poll: Polling decision {"endpoint": "institutional_ownership:HOOD", "base_endpoint": "institutional_ownership", "force_first": false, "last": 1774383325.981555, "interval": 86400, "time_since_last": 14037.281330823898}
Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [UW-DAEMON] Market is CLOSED (ET time: 20:09) - will use longer polling intervals
Mar 25 00:09:23 ubuntu-s-1vcpu-2gb-nyc3-01-alpaca python[1491472]: [DEBUG] uw_flow_daemon.py:should_poll: Polling skipped - interval not elapsed {"endpoint": "institutional_ownership:HOOD", "time_remaining": 72362.7186691761}
```

## Phase 1 — Memory Bank canonization

- **File updated:** `/root/stock-bot/MEMORY_BANK.md`
- **Section title (exact):** `Alpaca attribution truth contract (canonical)`

### Unified diff summary (key inserted lines)
```
- ## Alpaca attribution truth contract (canonical)
- 1. **Deterministic join keys** on decision and execution records: `decision_event_id`, `canonical_trade_id`, `symbol_nor
- 4. **Economics explicit:** `main.py` `log_order` → `telemetry/attribution_emit_keys.attach_paper_economics_defaults` — `
```

### CSA canonization statement

**This section is holy material.** Any change to Alpaca attribution paths, join keys, economics schema, or snapshot parity without updating this subsection and re-running the offline CSA audit is a governance incident. Promotions, profit-contributor claims, and board readiness narratives MUST cite current artifact paths and audit verdict A.

