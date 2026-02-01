# UW Config and Events

**Generated:** 2026-01-28T16:44:56.247012+00:00
**System events (last 24h, uw/cache):** 1323

## Config references

- **config.registry:** CacheFiles.UW_FLOW_CACHE = data/uw_flow_cache.json
- **uw_flow_daemon:** SmartPoller endpoints option_flow, dark_pool_levels, greek_exposure, greeks, top_net_impact, market_tide, oi_change, etf_flow, iv_rank, shorts_ftds, max_pain
- **Market hours:** daemon polls 3x less frequently when market closed (offhours).

## Sample system events (uw/cache)

```json
{
  "timestamp": "2026-01-28T16:44:44.716930+00:00",
  "subsystem": "uw",
  "event_type": "uw_call",
  "severity": "INFO",
  "details": {
    "endpoint": "https://api.unusualwhales.com/api/darkpool/JNJ",
    "endpoint_name": "",
    "status": 200,
    "cache_hit": false,
    "latency_ms": 283
  }
}
```
```json
{
  "timestamp": "2026-01-28T16:44:46.013209+00:00",
  "subsystem": "uw",
  "event_type": "uw_call",
  "severity": "INFO",
  "details": {
    "endpoint": "https://api.unusualwhales.com/api/stock/JNJ/greek-exposure",
    "endpoint_name": "",
    "status": 200,
    "cache_hit": false,
    "latency_ms": 271
  }
}
```
```json
{
  "timestamp": "2026-01-28T16:44:47.420580+00:00",
  "subsystem": "displacement",
  "event_type": "displacement_evaluated",
  "severity": "INFO",
  "details": {
    "current_symbol": "CAT",
    "challenger_symbol": "GOOGL",
    "current_score": 2.305,
    "challenger_score": 3.713,
    "delta_score": 1.408,
    "current_entry_ts": "2026-01-28 16:44:08.498202",
    "age_seconds": 0.0,
    "regime
```
```json
{
  "timestamp": "2026-01-28T16:44:47.422234+00:00",
  "subsystem": "gate",
  "event_type": "blocked",
  "severity": "INFO",
  "details": {
    "symbol": "GOOGL",
    "displaced_symbol": "CAT",
    "reason": "displacement_blocked",
    "diagnostics": {
      "current_symbol": "CAT",
      "challenger_symbol": "GOOGL",
      "current_score": 2.305,
      "challenger_score": 3.713,
      "delta_scor
```
```json
{
  "timestamp": "2026-01-28T16:44:47.432861+00:00",
  "subsystem": "uw",
  "event_type": "uw_call",
  "severity": "INFO",
  "details": {
    "endpoint": "https://api.unusualwhales.com/api/stock/JNJ/greeks",
    "endpoint_name": "",
    "status": 200,
    "cache_hit": false,
    "latency_ms": 242
  }
}
```
```json
{
  "timestamp": "2026-01-28T16:44:47.635460+00:00",
  "subsystem": "uw",
  "event_type": "uw_call",
  "severity": "INFO",
  "details": {
    "endpoint": "https://api.unusualwhales.com/api/stock/JNJ/oi-change",
    "endpoint_name": "",
    "status": 200,
    "cache_hit": false,
    "latency_ms": 184
  }
}
```
```json
{
  "timestamp": "2026-01-28T16:44:49.027395+00:00",
  "subsystem": "uw",
  "event_type": "uw_call",
  "severity": "INFO",
  "details": {
    "endpoint": "https://api.unusualwhales.com/api/etfs/JNJ/in-outflow",
    "endpoint_name": "",
    "status": 200,
    "cache_hit": false,
    "latency_ms": 255
  }
}
```
```json
{
  "timestamp": "2026-01-28T16:44:50.422644+00:00",
  "subsystem": "uw",
  "event_type": "uw_call",
  "severity": "INFO",
  "details": {
    "endpoint": "https://api.unusualwhales.com/api/stock/JNJ/iv-rank",
    "endpoint_name": "",
    "status": 200,
    "cache_hit": false,
    "latency_ms": 228
  }
}
```
```json
{
  "timestamp": "2026-01-28T16:44:51.150637+00:00",
  "subsystem": "displacement",
  "event_type": "displacement_evaluated",
  "severity": "INFO",
  "details": {
    "current_symbol": "CAT",
    "challenger_symbol": "MRNA",
    "current_score": 2.301,
    "challenger_score": 3.686,
    "delta_score": 1.385,
    "current_entry_ts": "2026-01-28 16:44:08.498202",
    "age_seconds": 0.0,
    "regime_
```
```json
{
  "timestamp": "2026-01-28T16:44:51.152039+00:00",
  "subsystem": "gate",
  "event_type": "blocked",
  "severity": "INFO",
  "details": {
    "symbol": "MRNA",
    "displaced_symbol": "CAT",
    "reason": "displacement_blocked",
    "diagnostics": {
      "current_symbol": "CAT",
      "challenger_symbol": "MRNA",
      "current_score": 2.301,
      "challenger_score": 3.686,
      "delta_score"
```
```json
{
  "timestamp": "2026-01-28T16:44:51.863747+00:00",
  "subsystem": "uw",
  "event_type": "uw_call",
  "severity": "INFO",
  "details": {
    "endpoint": "https://api.unusualwhales.com/api/shorts/JNJ/ftds",
    "endpoint_name": "",
    "status": 200,
    "cache_hit": false,
    "latency_ms": 348
  }
}
```
```json
{
  "timestamp": "2026-01-28T16:44:53.027622+00:00",
  "subsystem": "uw",
  "event_type": "uw_call",
  "severity": "INFO",
  "details": {
    "endpoint": "https://api.unusualwhales.com/api/stock/JNJ/max-pain",
    "endpoint_name": "",
    "status": 200,
    "cache_hit": false,
    "latency_ms": 217
  }
}
```
```json
{
  "timestamp": "2026-01-28T16:44:54.730378+00:00",
  "subsystem": "displacement",
  "event_type": "displacement_evaluated",
  "severity": "INFO",
  "details": {
    "current_symbol": "CAT",
    "challenger_symbol": "WFC",
    "current_score": 2.294,
    "challenger_score": 3.681,
    "delta_score": 1.387,
    "current_entry_ts": "2026-01-28 16:44:08.498202",
    "age_seconds": 0.0,
    "regime_l
```
```json
{
  "timestamp": "2026-01-28T16:44:54.731681+00:00",
  "subsystem": "gate",
  "event_type": "blocked",
  "severity": "INFO",
  "details": {
    "symbol": "WFC",
    "displaced_symbol": "CAT",
    "reason": "displacement_blocked",
    "diagnostics": {
      "current_symbol": "CAT",
      "challenger_symbol": "WFC",
      "current_score": 2.294,
      "challenger_score": 3.681,
      "delta_score": 
```
```json
{
  "timestamp": "2026-01-28T16:44:56.715029+00:00",
  "subsystem": "uw",
  "event_type": "uw_call",
  "severity": "INFO",
  "details": {
    "endpoint": "https://api.unusualwhales.com/api/option-trades/flow-alerts",
    "endpoint_name": "",
    "status": 200,
    "cache_hit": false,
    "latency_ms": 492
  }
}
```