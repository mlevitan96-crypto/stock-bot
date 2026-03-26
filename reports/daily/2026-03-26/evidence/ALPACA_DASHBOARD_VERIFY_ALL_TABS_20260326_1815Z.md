# Alpaca dashboard — tab verifier (hard gate)

**Timestamp:** 20260326_1815Z  
**Host:** droplet `/root/stock-bot`

## Command

```bash
cd /root/stock-bot
set -a && source .env && set +a
python3 -u scripts/dashboard_verify_all_tabs.py \
  --json-out /tmp/ALPACA_DASHBOARD_VERIFY_ALL_TABS_20260326_1815Z.json
```

## Exit code

**0** — **23 / 23** endpoints returned HTTP **200**.

## Stdout (summary)

All lines showed `200 OK` for:

`/api/alpaca_operational_activity?hours=72`, `/api/version`, `/api/versions`, `/api/ping`, `/api/direction_banner`, `/api/situation`, `/api/positions`, `/api/stockbot/closed_trades`, `/api/stockbot/fast_lane_ledger`, `/api/sre/health`, `/api/sre/self_heal_events?limit=5`, `/api/executive_summary`, `/api/failure_points`, `/api/signal_history`, `/api/learning_readiness`, `/api/profitability_learning`, `/api/dashboard/data_integrity`, `/api/telemetry/latest/index`, `/api/telemetry/latest/health`, `/api/telemetry/latest/computed?name=live_vs_shadow_pnl`, `/api/paper-mode-intel-state`, `/api/xai/auditor`, `/api/xai/health`

## Machine-readable

`reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_20260326_1815Z.json` (`all_pass`: true).
