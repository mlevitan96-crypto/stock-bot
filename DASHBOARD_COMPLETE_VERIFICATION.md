# Complete Dashboard Verification & Data Mapping

## Overview
This document provides a complete mapping of all dashboard tabs, sections, API endpoints, and data sources to ensure everything is operational.

## Dashboard Tabs

### 1. 📊 Positions Tab
**Status**: ✅ Fully Implemented

**Frontend**:
- Tab ID: `positions-tab`
- Load Function: `updateDashboard()`
- Auto-refresh: Every 60 seconds

**API Endpoints**:
- `/api/positions` - Returns positions, total value, P&L
- `/api/health_status` - Returns Last Order and Doctor status

**Data Sources**:
- **Positions**: Alpaca API (`_alpaca_api.list_positions()`)
- **Account**: Alpaca API (`_alpaca_api.get_account()`)
- **Last Order**: Reads from `data/live_orders.jsonl`, `logs/orders.jsonl`, or `logs/trading.jsonl`
- **Doctor/Heartbeat**: Reads from `state/bot_heartbeat.json` (primary), `state/doctor_state.json`, `state/system_heartbeat.json`, or `state/heartbeat.json`

**Expected Response Structure**:
```json
{
  "positions": [
    {
      "symbol": "AAPL",
      "side": "long",
      "qty": 100,
      "avg_entry_price": 150.0,
      "current_price": 155.0,
      "market_value": 15500.0,
      "unrealized_pnl": 500.0,
      "unrealized_pnl_pct": 3.33
    }
  ],
  "total_value": 100000.0,
  "unrealized_pnl": 500.0,
  "day_pnl": 100.0
}
```

**Health Status Response**:
```json
{
  "last_order": {
    "timestamp": 1234567890,
    "age_sec": 3600,
    "age_hours": 1.0,
    "status": "healthy"
  },
  "doctor": {
    "age_sec": 300,
    "age_minutes": 5.0,
    "status": "healthy"
  },
  "market": {
    "open": true,
    "status": "market_open"
  }
}
```

---

### 2. 🔍 SRE Monitoring Tab
**Status**: ✅ Fully Implemented

**Frontend**:
- Tab ID: `sre-tab`
- Load Function: `loadSREContent()`
- Render Function: `renderSREContent(data, container)`
- Auto-refresh: Every 60 seconds

**API Endpoint**:
- `/api/sre/health` - Returns comprehensive SRE health data

**Data Sources**:
- **Signal Components**: `sre_monitoring.SREMonitoringEngine.get_signal_health()`
- **UW API Endpoints**: `sre_monitoring.SREMonitoringEngine.get_uw_endpoint_health()`
- **Order Execution**: `sre_monitoring.SREMonitoringEngine.get_order_execution_health()`
- **Comprehensive Learning**: `sre_monitoring.SREMonitoringEngine.get_comprehensive_learning_health()`

**Expected Response Structure**:
```json
{
  "overall_health": "healthy",
  "market_open": true,
  "market_status": "market_open",
  "critical_issues": [],
  "warnings": [],
  "signal_components": {
    "flow": {
      "status": "healthy",
      "last_update_age_sec": 45,
      "data_freshness_sec": 45,
      "signals_generated_1h": 10,
      "found_in_symbols": ["AAPL", "TSLA"]
    }
  },
  "uw_api_endpoints": {
    "option_flow": {
      "status": "healthy",
      "endpoint": "/api/option-trades/flow-alerts",
      "avg_latency_ms": 245,
      "error_rate_1h": 0.02,
      "last_success_age_sec": 30
    }
  },
  "order_execution": {
    "status": "healthy",
    "last_order_age_sec": 1800,
    "orders_1h": 5,
    "orders_3h": 12,
    "orders_24h": 45,
    "fill_rate": 0.95
  },
  "comprehensive_learning": {
    "running": true,
    "last_run_age_sec": 3600,
    "success_count": 10,
    "error_count": 0
  }
}
```

---

### 3. 📈 Executive Summary Tab
**Status**: ✅ Fully Implemented

**Frontend**:
- Tab ID: `executive-tab`
- Load Function: `loadExecutiveSummary()`
- Render Function: `renderExecutiveSummary(data, container)`
- Auto-refresh: Every 60 seconds

**API Endpoint**:
- `/api/executive_summary` - Returns executive summary with trades, P&L, and learning analysis

**Data Sources**:
- **Trades**: `executive_summary_generator.get_all_trades()` → Reads from `logs/attribution.jsonl`
- **P&L Metrics**: `executive_summary_generator.calculate_pnl_metrics()`
- **Signal Analysis**: `executive_summary_generator.analyze_signal_performance()`
- **Learning Insights**: `executive_summary_generator.get_learning_insights()` → Reads from:
  - `state/signal_weights.json` (weight adjustments)
  - `data/comprehensive_learning.jsonl` (learning results)
  - `data/counterfactual_results.jsonl` (counterfactual analysis)

**Expected Response Structure**:
```json
{
  "total_trades": 50,
  "pnl_metrics": {
    "pnl_2d": 500.0,
    "pnl_5d": 1200.0,
    "trades_2d": 10,
    "trades_5d": 25,
    "win_rate_2d": 60.0,
    "win_rate_5d": 55.0
  },
  "trades": [
    {
      "timestamp": "2025-01-15T10:30:00Z",
      "symbol": "AAPL",
      "pnl_usd": 50.0,
      "pnl_pct": 2.5,
      "hold_minutes": 120,
      "entry_score": 2.5,
      "close_reason": "profit_target"
    }
  ],
  "signal_analysis": {
    "top_signals": {
      "flow": {
        "total_pnl": 500.0,
        "avg_pnl": 50.0,
        "win_rate": 60.0,
        "count": 10
      }
    },
    "bottom_signals": {
      "congress": {
        "total_pnl": -100.0,
        "avg_pnl": -10.0,
        "win_rate": 30.0,
        "count": 10
      }
    }
  },
  "learning_insights": {
    "weight_adjustments": {
      "flow": {
        "current_multiplier": 1.2,
        "sample_count": 50,
        "win_rate": 60.0
      }
    },
    "counterfactual_insights": {
      "missed_opportunities": 5,
      "avoided_losses": 3,
      "theoretical_pnl": 200.0
    }
  },
  "written_summary": "Executive summary text..."
}
```

---

### 4. 🧠 Natural Language Auditor (XAI) Tab
**Status**: ✅ Fully Implemented

**Frontend**:
- Tab ID: `xai-tab`
- Load Function: `loadXAIAuditor()`
- Render Function: `renderXAIAuditor(data, container)`
- Export Function: `exportXAI()`
- Auto-refresh: Every 60 seconds

**API Endpoints**:
- `/api/xai/auditor` - Returns trade and weight explanations
- `/api/xai/export` - Exports all logs as JSON download

**Data Sources**:
- **Trade Explanations**: `xai.explainable_logger.ExplainableLogger.get_trade_explanations()` → Reads from `data/explainable_logs.jsonl`
- **Weight Explanations**: `xai.explainable_logger.ExplainableLogger.get_weight_explanations()` → Reads from `data/explainable_logs.jsonl`

**Expected Response Structure**:
```json
{
  "trades": [
    {
      "type": "trade_entry",
      "symbol": "AAPL",
      "timestamp": "2025-01-15T10:30:00Z",
      "why": "Entered AAPL because: high flow conviction (0.85), bullish regime, strong gamma exposure.",
      "regime": "RISK_ON",
      "pnl_pct": null
    },
    {
      "type": "trade_exit",
      "symbol": "AAPL",
      "timestamp": "2025-01-15T12:30:00Z",
      "why": "Exited AAPL because: profit target reached (2.5%), gamma wall resistance.",
      "regime": "RISK_ON",
      "pnl_pct": 2.5
    }
  ],
  "weights": [
    {
      "type": "weight_adjustment",
      "component": "flow",
      "timestamp": "2025-01-15T09:00:00Z",
      "old_weight": 1.0,
      "new_weight": 1.2,
      "why": "Adjusted flow weight because: 50 samples, 60% win rate, positive P&L contribution.",
      "sample_count": 50,
      "win_rate": 0.6
    }
  ]
}
```

---

### 5. ⚠️ Trading Readiness (Failure Points) Tab
**Status**: ✅ Fully Implemented

**Frontend**:
- Tab ID: `failure_points-tab`
- Load Function: `loadFailurePoints()`
- Render Function: `renderFailurePoints(data, container)`
- Auto-refresh: Every 30 seconds

**API Endpoint**:
- `/api/failure_points` - Returns failure point status and trading readiness

**Data Sources**:
- **Failure Points**: `failure_point_monitor.FailurePointMonitor.get_trading_readiness()` → Checks all 36+ failure points

**Expected Response Structure**:
```json
{
  "readiness": "READY",
  "color": "green",
  "critical_count": 0,
  "warning_count": 2,
  "total_checked": 36,
  "critical_fps": [],
  "warning_fps": ["FP-2.1", "FP-3.2"],
  "failure_points": {
    "FP-1.1": {
      "id": "FP-1.1",
      "name": "UW Daemon Running",
      "category": "Data & Signal Generation",
      "status": "OK",
      "last_check": 1234567890,
      "last_error": null,
      "self_healing_attempted": false,
      "self_healing_success": false
    }
  }
}
```

---

## Data File Mappings

| Data Type | File Path(s) | Writer | Reader | Status |
|-----------|--------------|--------|--------|--------|
| **Attribution (Trades)** | `logs/attribution.jsonl` | `main.py::jsonl_write()` | `executive_summary_generator.py` | ✅ Correct |
| **Explainable Logs** | `data/explainable_logs.jsonl` | `xai.explainable_logger` | `xai.explainable_logger` | ✅ Correct |
| **Signal Weights** | `state/signal_weights.json` | `adaptive_signal_optimizer.py` | `executive_summary_generator.py` | ✅ Correct |
| **Comprehensive Learning** | `data/comprehensive_learning.jsonl` | `comprehensive_learning_orchestrator.py` | `executive_summary_generator.py` | ✅ Correct |
| **Counterfactual Results** | `data/counterfactual_results.jsonl` | `counterfactual_analyzer.py` | `executive_summary_generator.py` | ✅ Correct |
| **UW Flow Cache** | `data/uw_flow_cache.json` | `uw_flow_daemon.py` | `sre_monitoring.py` | ✅ Correct |
| **Live Orders** | `data/live_orders.jsonl` | `main.py` | `dashboard.py::api_health_status()` | ✅ Correct |
| **Bot Heartbeat** | `state/bot_heartbeat.json` | `main.py` | `dashboard.py::api_health_status()` | ✅ Correct |
| **Failure Point State** | `state/failure_point_monitor.json` | `failure_point_monitor.py` | `failure_point_monitor.py` | ✅ Correct |

---

## API Endpoint Summary

| Endpoint | Method | Handler | Status |
|----------|--------|---------|--------|
| `/` | GET | `index()` | ✅ Returns main dashboard HTML |
| `/health` | GET | `health()` | ✅ Health check |
| `/api/positions` | GET | `api_positions()` | ✅ Returns positions from Alpaca |
| `/api/health_status` | GET | `api_health_status()` | ✅ Returns Last Order & Doctor status |
| `/api/sre/health` | GET | `api_sre_health()` | ✅ Returns comprehensive SRE health |
| `/api/executive_summary` | GET | `api_executive_summary()` | ✅ Returns executive summary |
| `/api/xai/auditor` | GET | `api_xai_auditor()` | ✅ Returns XAI logs |
| `/api/xai/export` | GET | `api_xai_export()` | ✅ Exports XAI logs as JSON |
| `/api/failure_points` | GET | `api_failure_points()` | ✅ Returns failure point status |
| `/api/closed_positions` | GET | `api_closed_positions()` | ✅ Returns closed positions |

---

## Testing

### Local Testing
Run the comprehensive test script:
```bash
python test_dashboard_complete.py
```

### On Droplet
```bash
cd ~/stock-bot
source venv/bin/activate
python3 test_dashboard_complete.py
```

### Manual Endpoint Testing
```bash
# Test each endpoint
curl http://localhost:5000/api/positions | python3 -m json.tool
curl http://localhost:5000/api/sre/health | python3 -m json.tool
curl http://localhost:5000/api/executive_summary | python3 -m json.tool
curl http://localhost:5000/api/xai/auditor | python3 -m json.tool
curl http://localhost:5000/api/failure_points | python3 -m json.tool
curl http://localhost:5000/api/health_status | python3 -m json.tool
```

---

## Known Issues & Fixes

### ✅ Fixed Issues
1. **Attribution Path Mismatch**: Fixed - All readers now use `logs/attribution.jsonl`
2. **Heartbeat Field Names**: Fixed - Checks `last_heartbeat_ts` first, then fallbacks
3. **Last Order Timestamp**: Fixed - Reads from multiple possible files
4. **Open Trades in Executive Summary**: Fixed - Filters out `open_` trade IDs

### ⚠️ Expected Behaviors
1. **No Trades Yet**: Executive Summary will show "No trades found" - this is expected
2. **No Learning Data**: Learning data appears after first learning cycle runs (hourly)
3. **Missing Data Files**: Some data files may not exist until bot runs - this is normal

---

## Verification Checklist

- [x] All 5 tabs implemented in HTML
- [x] All API endpoints implemented in `dashboard.py`
- [x] All data sources correctly mapped
- [x] Frontend JavaScript functions implemented
- [x] Error handling in place
- [x] Auto-refresh configured
- [x] Test script created (`test_dashboard_complete.py`)

---

## Next Steps

1. **Deploy to Droplet**: Ensure all dependencies are installed
2. **Run Test Script**: Execute `test_dashboard_complete.py` on droplet
3. **Verify Each Tab**: Manually check each tab loads correctly
4. **Monitor Logs**: Check dashboard logs for any errors
5. **Verify Data Flow**: Ensure data files are being written and read correctly

---

## Support

If any tab or section is not working:
1. Check browser console (F12) for JavaScript errors
2. Check dashboard logs: `tail -f logs/dashboard.log`
3. Test API endpoints directly with `curl`
4. Verify data files exist and are readable
5. Check that all dependencies are installed

