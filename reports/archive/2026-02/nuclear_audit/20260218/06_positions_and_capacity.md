# 06 Positions and capacity

## state/*.json (positions from state)
```
{
  "timestamp": "2026-02-18T19:49:18.850771Z",
  "positions": [],
  "cash": 49661.48,
  "portfolio_value": 49661.48,
  "equity": 49661.48,
  "buying_power": 99322.96
}{
  "profiles": {},
  "total_fills": 117,
  "system_stage": "bootstrap",
  "last_updated": "2025-12-22T18:42:26.083839"
}{
  "last_heartbeat_ts": 1771444158,
  "last_heartbeat_dt": "2026-02-18 19:49:18 UTC",
  "iter_count": 0,
  "running": true,
  "metrics": {
    "clusters": 0,
    "orders": 0
  }
}{
  "trade_contexts": {
    "scale_RDDT_2026-01-05T15:25:28.344909+00:00": {
      "context": {
        "market_regime": "unknown",
        "volatility_regime": "NORMAL_VOL",
        "time_of_day": "CLOSE",
        "day_of_week": "MONDAY",
        "sector": "UNKNOWN",
        "market_trend": "SIDEWAYS",
        "iv_rank": "MEDIUM",
        "flow_magnitude": "LOW",
        "signal_strength": "WEAK",
        "entry_score": 0.0,
        "hour": 15
      },
      "pnl_usd": 5.09,
      "pnl_pct": 0.6193,
      "win": true,
      "components": {},
      "ts": "2026-01-05T15:25:28.345044+00:00"
    },
    "close_QQQ_2026-01-05T16:02:32.876391+00:00": {
      "context": {
        "market_regime": "unknown",
        "volatility_regime": "NORMAL_VOL",
        "time_of_day": "AFTER_HOURS",
        "day_of_week": "MONDAY",
        "sector": "UNKNOWN",
        "market_trend": "SIDEWAYS",
        "iv_rank": "MEDIUM",
        "flow_magnitude": "LOW",
        "signal_strength": "WEAK",
        "entry_score": 0.0,
        "hour": 16
      },
      "pnl_usd": -0.68,
      "pnl_pct": -0.1099,
      "win": false,
      "components": {},
      "ts": "2026-01-05T16:02:32.876449+00:00"
    },
    "close_TLT_2026-01-05T16:02:33.204961+00:00": {
      "context": {
        "market_regime": "unknown",
        "volatility_regime": "NORMAL_VOL",
        "time_of_day": "AFTER_HOURS",
        "day_of_week": "MONDAY",
        "sector": "UNKNOWN",
        "market_trend": "SIDEWAYS",
        "iv_rank": "MEDIUM",
        "flow_magnitude": "LOW",
        "signal_strength": "WEAK",
        "entry_score": 0.0,
        "hour": 16
      },
      "pnl_usd": -0.04,
      "pnl_pct": -0.0115,
      "win": false,
      "components": {},
      "ts": "2026-01-05T16:02:33.205001+00:00"
    },
    "close_SPY_2026-01-05T16:03:38.379360+00:00": {
      "context": {
        "market_regime": "mixed",
        "volatility_regime": "NORMAL_VOL",
        "time_of_day": "AFTER_HOURS",
        "day_of_week": "MONDAY",
        "sector": "UNKNOWN",
      
```

## API list_positions (paper)
```
[CONFIG] Loaded theme_risk.json: ENABLE_THEME_RISK=True, MAX_THEME_NOTIONAL_USD=$150,000
error: cannot import name 'get_api' from 'main' (/root/stock-bot/main.py)
```