# ALPACA METADATA HEALTH

- UTC `20260330_180816Z`

- Metadata symbols (non-internal): **32**
- Positions missing entry_reason/reason field: **32**
- Positions missing v2 snapshot block: **32**
- entry_score null/zero: **32** / 32

## signal_strength_cache.json freshness (sample)

```json
{
  "AAPL": {
    "signal_strength": 1.71,
    "position_side": "SHORT",
    "evaluated_at": "2026-03-30T18:07:37.685542Z",
    "prev_signal_strength": 1.71,
    "prev_evaluated_at": "2026-03-30T18:07:36.022510Z",
    "signal_delta": 0.0,
    "signal_delta_abs": 0.0,
    "signal_trend": "flat",
    "signal_trend_window": "last_eval"
  },
  "AMD": {
    "signal_strength": 2.424,
    "position_side": "SHORT",
    "evaluated_at": "2026-03-30T18:07:37.725252Z",
    "prev_signal_strength": 2.424,
    "prev_evaluated_at": "2026-03-30T18:07:36.041293Z",
    "signal_delta": 0.0,
    "signal_delta_abs": 0.0,
    "signal_trend": "flat",
    "signal_trend_window": "last_eval"
  },
  "C": {
    "signal_strength": 2.168,
    "position_side": "SHORT",
    "evaluated_at": "2026-03-30T18:07:37.763637Z",
    "prev_signal_strength": 2.168,
    "prev_evaluated_at": "2026-03-30T18:07:36.060011Z",
    "signal_delta": 0.0,
    "signal_delta_abs": 0.0,
    "signal_trend": "flat",
    "signal_trend_window": "last_eval"
  },
  "COIN": {
    "signal_strength": 2.229,
    "position_side": "SHORT",
    "evaluated_at": "2026-03-30T18:07:37.802621Z",
    "prev_signal_strength": 2.229,
    "prev_evaluated_at": "2026-03-30T18:07:36.078687Z",
    "signal_delta": 0.0,
    "signal_delta_abs": 0.0,
    "signal_trend": "flat",
    "signal_trend_window": "last_eval"
  },
  "COP": {
    "signal_strength": 1.791,
    "position_side": "SHORT",
    "evaluated_at": "2026-03-30T18:07:37.840477Z",
    "prev_signal_strength": 1.791,
    "prev_evaluated_at": "2026-03-30T18:07:36.096780Z",
    "signal_delta": 0.0,
    "signal_delta_abs": 0.0,
    "signal_trend": "flat",
    "signal_trend_window": "last_eval"
  }
}
```

## peak_equity.json

```json
{
  "peak_equity": 47374.31,
  "last_updated": "2026-03-30T17:42:48.008760+00:00",
  "peak_timestamp": 1774892601,
  "reset_reason": "SRE: telemetry default 100k peak vs depleted paper equity caused spurious max_drawdown_exceeded; baseline set to current equity"
}
```
