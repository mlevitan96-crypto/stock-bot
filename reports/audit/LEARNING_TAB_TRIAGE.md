# Learning Tab Triage
**Triage time (UTC):** 2026-03-04T20:36:21.790340+00:00

## /api/learning_readiness

- **HTTP:** 200
- **Keys (sample):** ['deployed_commit', 'error', 'error_code', 'features_reviewed', 'fresh', 'last_cron_run_iso', 'min_pct_telemetry', 'ok', 'pct_telemetry', 'promotion_close_missing', 'promotion_reasons', 'promotion_recommendation', 'promotion_score', 'ready', 'replay_status', 'review_continues_after_100', 'run_ts', 'still_reviewing', 'target_trades', 'telemetry_total']
- telemetry_trades: 346
- visibility_matrix length: 7
- **Body (first 500 chars):**
```
{"deployed_commit":"18b53be522d2","error":null,"error_code":null,"features_reviewed":["Entry intel (premarket, futures, sector, regime at position open)","Exit intel (same at close)","Direction, side, position_side","Sizing (qty or notional)","Join key: symbol + entry_ts"],"fresh":true,"last_cron_run_iso":"2026-03-04T20:35:01.211174+00:00","min_pct_telemetry":90.0,"ok":true,"pct_telemetry":17.25,"promotion_close_missing":["Need 90% telemetry coverage (have 17.2%)"],"promotion_reasons":[],"promot
```

## /api/telemetry_health

- **HTTP:** 200
- **Keys (sample):** ['direction_coverage', 'direction_ready', 'direction_telemetry_trades', 'direction_total_trades', 'gate_status', 'last_droplet_analysis', 'log_status']
- **Body (first 500 chars):**
```
{"direction_coverage":"346/100","direction_ready":false,"direction_telemetry_trades":346,"direction_total_trades":2006,"gate_status":null,"last_droplet_analysis":null,"log_status":[{"exists":true,"last_write":"2026-03-04T20:35:43.023638+00:00","log":"master_trade_log"},{"exists":true,"last_write":"2026-03-04T20:35:43.131642+00:00","log":"attribution"},{"exists":true,"last_write":"2026-03-04T20:35:43.156643+00:00","log":"exit_attribution"},{"exists":true,"last_write":"2026-03-03T23:01:15.764369+0
```

## /api/situation

- **HTTP:** 200
- **Keys (sample):** ['closed_trades_count', 'governance_joined_count', 'open_positions_count', 'promotion_reasons', 'promotion_recommendation', 'promotion_score', 'trades_reviewed', 'trades_reviewed_target', 'trades_reviewed_total']
- **Body (first 500 chars):**
```
{"closed_trades_count":500,"governance_joined_count":100,"open_positions_count":28,"promotion_reasons":[],"promotion_recommendation":"WAIT","promotion_score":null,"trades_reviewed":346,"trades_reviewed_target":100,"trades_reviewed_total":2006}

```

