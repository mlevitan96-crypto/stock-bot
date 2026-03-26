# Dashboard Full Validation

**Timestamp:** 2026-03-08_2155 UTC
**Environment:** Droplet (localhost:5000)

## Summary

- **Endpoints checked:** 17
- **200 OK:** 6
- **Non-200:** 11

## Per-endpoint

| Endpoint | HTTP | Tab/Surface |
|----------|------|-------------|
| `/` | 200 | Page (all tabs) |
| `/api/direction_banner` | 200 | Direction banner |
| `/api/situation` | 200 | Situation strip |
| `/api/learning_readiness` | 200 | Learning & Readiness |
| `/api/profitability_learning` | 200 | Profitability & Learning |
| `/api/sre/health` | 401 | SRE Monitoring |
| `/api/telemetry_health` | 200 | Telemetry Health |
| `/api/executive_summary?timeframe=24h` | 401 | Executive Summary |
| `/api/stockbot/closed_trades` | 401 | Closed Trades |
| `/api/stockbot/wheel_analytics` | 401 | Wheel Strategy |
| `/api/wheel/universe_health` | 401 | Wheel Universe |
| `/api/strategy/comparison` | 401 | Strategy Comparison |
| `/api/signal_history` | 401 | Signal Review |
| `/api/failure_points` | 401 | Trading Readiness |
| `/api/telemetry/latest/index` | 401 | Telemetry |
| `/api/positions` | 401 | Positions |
| `/api/version` | 401 | Version |

## Exit criteria

- [x] Deploy completed (git pull + restart)
- [x] Dashboard listening on 5000
- [x] All key endpoints hit (no 500): See non-200 above

## Non-200 endpoints

- `/api/sre/health`
- `/api/executive_summary?timeframe=24h`
- `/api/stockbot/closed_trades`
- `/api/stockbot/wheel_analytics`
- `/api/wheel/universe_health`
- `/api/strategy/comparison`
- `/api/signal_history`
- `/api/failure_points`
- `/api/telemetry/latest/index`
- `/api/positions`
- `/api/version`
