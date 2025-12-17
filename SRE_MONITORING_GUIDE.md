# SRE Monitoring Guide

## Overview

The SRE monitoring system provides granular health monitoring for all system components, following Site Reliability Engineering best practices.

## What Gets Monitored

### 1. Signal Components (Granular)
Each signal source is monitored individually:
- **flow** - Options flow sentiment
- **dark_pool** - Dark pool activity
- **insider** - Insider trading signals
- **iv_term_skew** - IV term structure
- **smile_slope** - Volatility smile
- **greeks_gamma** - Gamma exposure
- **oi_change** - Open interest changes
- **etf_flow** - ETF money flow
- **market_tide** - Market-wide sentiment
- **congress** - Congress/politician trading
- **shorts_squeeze** - Short interest signals

**Metrics per signal:**
- Data freshness (last update age)
- Signal generation rate (signals/hour)
- Error rate (errors/hour)
- Status: healthy, degraded, no_data, unknown

### 2. UW API Endpoints (Per-Endpoint Health)
Each UW API endpoint is monitored separately:
- `/api/option-trades/flow-alerts`
- `/api/darkpool/{ticker}`
- `/api/stock/{ticker}/greeks`
- `/api/market/top-net-impact`
- `/api/market/market-tide`
- `/api/stock/{ticker}/greek-exposure`
- `/api/stock/{ticker}/oi-change`
- `/api/etfs/{ticker}/in-outflow`
- `/api/stock/{ticker}/iv-rank`
- `/api/shorts/{ticker}/ftds`
- `/api/stock/{ticker}/max-pain`

**Metrics per endpoint:**
- Connectivity status
- Average latency (ms)
- Error rate (last 1 hour)
- Rate limit remaining
- Last error message

### 3. Order Execution Pipeline
- Last order timestamp (accurate, from live_orders.jsonl)
- Orders per hour (1h, 3h, 24h windows)
- Fill rate (filled vs submitted)
- Average fill time
- Error rate

### 4. System Health
- Market hours awareness (knows when market is open)
- Doctor/heartbeat status
- UW cache freshness
- Health supervisor status

## API Endpoints

### `/api/sre/health` - Comprehensive Health
Returns complete health status for all components:
```json
{
  "timestamp": 1234567890,
  "market_open": true,
  "market_status": "market_open",
  "last_order": {
    "timestamp": 1234567890,
    "age_sec": 10800,
    "age_hours": 3.0
  },
  "uw_api_endpoints": {
    "option_flow": {
      "status": "healthy",
      "error_rate_1h": 0.02,
      "avg_latency_ms": 245
    }
  },
  "signal_components": {
    "flow": {
      "status": "healthy",
      "last_update_age_sec": 45,
      "data_freshness_sec": 45
    }
  },
  "order_execution": {
    "status": "degraded",
    "last_order_age_sec": 10800,
    "orders_1h": 0,
    "fill_rate": 0.95
  },
  "overall_health": "degraded"
}
```

### `/api/sre/signals` - Signal Component Health
Detailed health for each signal component.

### `/api/sre/uw_endpoints` - UW API Endpoint Health
Detailed health for each UW API endpoint.

### `/api/health_status` - Dashboard Health Status
Simplified endpoint for dashboard indicators:
```json
{
  "last_order": {
    "age_sec": 10800,
    "age_hours": 3.0,
    "status": "warning"
  },
  "doctor": {
    "age_sec": 3000,
    "age_minutes": 50,
    "status": "warning"
  },
  "market": {
    "open": true,
    "status": "market_open"
  }
}
```

## Dashboard Integration

The dashboard now shows:
- **Last Order** - Accurate timestamp from `data/live_orders.jsonl`
  - Green: < 1 hour
  - Yellow: 1-3 hours
  - Red: > 3 hours

- **Doctor** - Heartbeat status from `state/doctor_state.json`
  - Green: < 5 minutes
  - Yellow: 5-30 minutes
  - Red: > 30 minutes

## Market Hours Awareness

The system knows US market hours (9:30 AM - 4:00 PM ET):
- During market hours: No orders in 1h = degraded status
- Outside market hours: No orders = normal (market_closed status)

## Usage on Droplet

### Check Comprehensive Health:
```bash
cd /root/stock-bot && source venv/bin/activate && python3 -c "from sre_monitoring import get_sre_health; import json; print(json.dumps(get_sre_health(), indent=2, default=str))"
```

### Via API (if services running):
```bash
curl http://localhost:8081/api/sre/health | python3 -m json.tool
```

### Check Specific Components:
```bash
# Signal health
curl http://localhost:8081/api/sre/signals | python3 -m json.tool

# UW API health
curl http://localhost:8081/api/sre/uw_endpoints | python3 -m json.tool
```

## Health Status Meanings

### Signal Component Status:
- **healthy** - Data is fresh, signals being generated
- **degraded** - Data is stale but present
- **no_data** - No data for this signal
- **no_recent_signals** - No signals generated in last hour

### UW API Endpoint Status:
- **healthy** - Endpoint responding normally
- **rate_limited** - Hit rate limits (429)
- **auth_failed** - Authentication issue (401)
- **timeout** - Request timeout
- **connection_error** - Cannot connect
- **error** - Other HTTP error

### Order Execution Status:
- **healthy** - Orders executing normally
- **degraded** - No orders in last hour (during market hours)
- **market_closed** - No orders (normal, market is closed)
- **no_recent_orders** - No orders in last 24h

## SRE Best Practices Implemented

1. **Granular Monitoring** - Each component monitored separately
2. **Error Rate Tracking** - Errors per hour for each component
3. **Latency Monitoring** - Response times for API calls
4. **Data Freshness** - Age of data for each signal
5. **Market Context** - Understands market hours
6. **Degradation Detection** - Identifies partial failures
7. **Rate Limit Awareness** - Tracks API rate limits
8. **Accurate Timestamps** - Reads directly from source files

## Troubleshooting

### If Last Order shows wrong time:
- Check `data/live_orders.jsonl` directly
- Verify the file is being written to
- Check for file permissions

### If Doctor shows wrong time:
- Check `state/doctor_state.json` or `state/system_heartbeat.json`
- Verify heartbeat-keeper process is running
- Check file modification time

### If signals show "no_data":
- Check UW API connectivity
- Verify UW daemon is running
- Check `data/uw_flow_cache.json` freshness
- Review `logs/uw_error.jsonl` for API errors

### If UW endpoints show errors:
- Check API key is set: `echo $UW_API_KEY`
- Review rate limits: Check `X-RateLimit-Remaining` headers
- Check network connectivity
- Review error logs: `tail -50 logs/uw_error.jsonl`
