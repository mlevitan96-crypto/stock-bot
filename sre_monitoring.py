#!/usr/bin/env python3
"""
SRE-Style Granular Monitoring Engine
====================================
Comprehensive health monitoring for all signal sources, APIs, and system components.

Monitors:
- Each UW API endpoint individually (connectivity, latency, error rates)
- Signal generation health (are signals being produced?)
- Data freshness per signal component
- Order execution pipeline health
- Market hours awareness
- Error rates and degradation detection
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

@dataclass
class SignalHealth:
    """Health status for a single signal component."""
    name: str
    status: str  # "healthy", "degraded", "down", "unknown"
    last_update_age_sec: float
    data_freshness_sec: Optional[float] = None
    error_rate_1h: float = 0.0
    request_count_1h: int = 0
    success_count_1h: int = 0
    avg_latency_ms: Optional[float] = None
    last_error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIEndpointHealth:
    """Health status for a UW API endpoint."""
    endpoint: str
    status: str
    last_success_age_sec: Optional[float] = None
    error_rate_1h: float = 0.0
    avg_latency_ms: Optional[float] = None
    rate_limit_remaining: Optional[int] = None
    last_error: Optional[str] = None

class SREMonitoringEngine:
    """SRE-style comprehensive monitoring for all system components."""
    
    def __init__(self):
        self.uw_base = "https://api.unusualwhales.com"
        self.uw_api_key = os.getenv("UW_API_KEY")
        self.watchlist = ["AAPL", "MSFT", "NVDA", "QQQ", "SPY", "TSLA"]  # Default, should come from config
        
    def is_market_open(self) -> Tuple[bool, str]:
        """Check if US market is currently open (9:30 AM - 4:00 PM ET)."""
        now_utc = datetime.now(timezone.utc)
        now_et = now_utc.astimezone(timezone(timedelta(hours=-5)))  # EST/EDT approximation
        
        # Check if weekday (Monday=0, Sunday=6)
        if now_et.weekday() >= 5:  # Saturday or Sunday
            return False, "market_closed_weekend"
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        
        if market_open <= now_et <= market_close:
            return True, "market_open"
        elif now_et < market_open:
            return False, "market_closed_pre_market"
        else:
            return False, "market_closed_after_hours"
    
    def get_last_order_timestamp(self) -> Optional[float]:
        """Get the actual last order timestamp from live_orders.jsonl."""
        orders_file = DATA_DIR / "live_orders.jsonl"
        if not orders_file.exists():
            return None
        
        try:
            last_order_ts = 0
            with orders_file.open("r") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_ts = event.get("_ts", 0)
                        event_type = event.get("event", "")
                        if event_ts > last_order_ts and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:
                            last_order_ts = event_ts
                    except:
                        pass
            return last_order_ts if last_order_ts > 0 else None
        except Exception:
            return None
    
    def check_uw_endpoint_health(self, endpoint: str, test_symbol: str = "AAPL") -> APIEndpointHealth:
        """Check health of a specific UW API endpoint."""
        health = APIEndpointHealth(endpoint=endpoint, status="unknown")
        
        if not self.uw_api_key:
            health.status = "no_api_key"
            health.last_error = "UW_API_KEY not set"
            return health
        
        # Check error logs for this endpoint
        error_log = DATA_DIR / "uw_error.jsonl"
        now = time.time()
        cutoff_1h = now - 3600
        
        errors_1h = 0
        requests_1h = 0
        last_error_msg = None
        
        if error_log.exists():
            try:
                for line in error_log.read_text().splitlines()[-100:]:
                    try:
                        event = json.loads(line)
                        if endpoint in event.get("url", ""):
                            requests_1h += 1
                            if event.get("_ts", 0) > cutoff_1h:
                                errors_1h += 1
                                if not last_error_msg:
                                    last_error_msg = event.get("error", "Unknown error")
                    except:
                        pass
            except:
                pass
        
        # Try a test request (with timeout to avoid blocking)
        try:
            url = f"{self.uw_base}{endpoint}".replace("{ticker}", test_symbol).replace("{symbol}", test_symbol)
            headers = {"Authorization": f"Bearer {self.uw_api_key}"}
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=5, params={"limit": 1})
            latency_ms = (time.time() - start_time) * 1000
            
            health.avg_latency_ms = latency_ms
            
            if response.status_code == 200:
                health.status = "healthy"
                health.last_success_age_sec = 0
                health.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", -1))
            elif response.status_code == 429:
                health.status = "rate_limited"
                health.last_error = "Rate limit exceeded"
            elif response.status_code == 401:
                health.status = "auth_failed"
                health.last_error = "Authentication failed"
            else:
                health.status = "error"
                health.last_error = f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            health.status = "timeout"
            health.last_error = "Request timeout"
        except requests.exceptions.ConnectionError:
            health.status = "connection_error"
            health.last_error = "Connection failed"
        except Exception as e:
            health.status = "error"
            health.last_error = str(e)
        
        if requests_1h > 0:
            health.error_rate_1h = errors_1h / requests_1h
        
        return health
    
    def check_signal_generation_health(self) -> Dict[str, SignalHealth]:
        """Check health of each signal component."""
        signals = {}
        
        # Check UW flow cache for signal freshness
        uw_cache_file = DATA_DIR / "uw_flow_cache.json"
        if uw_cache_file.exists():
            try:
                cache = json.loads(uw_cache_file.read_text())
                cache_age = time.time() - uw_cache_file.stat().st_mtime
                
                # Get all symbols from cache (not just watchlist) to ensure we check everything
                all_cache_symbols = [k for k in cache.keys() if not k.startswith("_")]
                # Check watchlist first, then any other symbols in cache
                symbols_to_check = list(set(self.watchlist + all_cache_symbols[:10]))  # Check up to 10 additional symbols
                
                for symbol in symbols_to_check:
                    symbol_data = cache.get(symbol, {})
                    if isinstance(symbol_data, str):
                        try:
                            symbol_data = json.loads(symbol_data)
                        except:
                            symbol_data = {}
                    
                    if not isinstance(symbol_data, dict):
                        continue
                    
                    # Check each signal component
                    components = {
                        "flow": symbol_data.get("sentiment"),
                        "dark_pool": symbol_data.get("dark_pool", {}),
                        "insider": symbol_data.get("insider", {}),
                        "iv_term_skew": symbol_data.get("iv_term_skew"),
                        "smile_slope": symbol_data.get("smile_slope"),
                    }
                    
                    for comp_name, comp_data in components.items():
                        if comp_name not in signals:
                            signals[comp_name] = SignalHealth(
                                name=comp_name,
                                status="unknown",
                                last_update_age_sec=cache_age
                            )
                        
                        # Only update if status is still unknown or no_data (don't overwrite healthy)
                        if signals[comp_name].status == "healthy":
                            continue
                        
                        # Check if signal has data (handle both dict and numeric values)
                        has_data = False
                        if comp_name == "insider":
                            # Insider is a dict - check if it exists and is not empty
                            has_data = isinstance(comp_data, dict) and len(comp_data) > 0
                        elif comp_name in ["iv_term_skew", "smile_slope"]:
                            # Numeric signals - check if not None (0.0 is valid!)
                            has_data = comp_data is not None
                        else:
                            # Other signals - check if truthy and not empty dict
                            has_data = comp_data and comp_data != {}
                        
                        if has_data:
                            signals[comp_name].status = "healthy"
                            signals[comp_name].data_freshness_sec = cache_age
                            # Mark that we found data in at least one symbol
                            if "found_in_symbols" not in signals[comp_name].details:
                                signals[comp_name].details["found_in_symbols"] = []
                            if symbol not in signals[comp_name].details["found_in_symbols"]:
                                signals[comp_name].details["found_in_symbols"].append(symbol)
                        else:
                            if signals[comp_name].status == "unknown":
                                signals[comp_name].status = "no_data"
            except Exception as e:
                import traceback
                # Log error but don't fail
                signals["_error"] = SignalHealth(
                    name="_error",
                    status="error",
                    last_update_age_sec=0,
                    details={"error": str(e), "traceback": traceback.format_exc()}
                )
        
        # Check signal generation from logs
        signals_log = LOGS_DIR / "signals.jsonl"
        if signals_log.exists():
            now = time.time()
            cutoff_1h = now - 3600
            
            signal_counts = {}
            for line in signals_log.read_text().splitlines()[-500:]:
                try:
                    event = json.loads(line)
                    if event.get("_ts", 0) > cutoff_1h:
                        signal_type = event.get("signal_type") or event.get("type") or "unknown"
                        signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
                except:
                    pass
            
            # Update signal health based on generation rate
            for signal_name, health in signals.items():
                count = signal_counts.get(signal_name, 0)
                if count > 0:
                    health.status = "healthy"
                    health.details["signals_generated_1h"] = count
                elif health.status == "unknown":
                    health.status = "no_recent_signals"
        
        return signals
    
    def check_uw_api_health(self) -> Dict[str, APIEndpointHealth]:
        """Check health of all UW API endpoints."""
        from config.uw_signal_contracts import UW_ENDPOINT_CONTRACTS
        
        endpoints_health = {}
        
        for endpoint_name, contract in UW_ENDPOINT_CONTRACTS.items():
            test_symbol = "AAPL"  # Default test symbol
            health = self.check_uw_endpoint_health(contract.endpoint, test_symbol)
            endpoints_health[endpoint_name] = health
        
        # Also check core endpoints
        core_endpoints = [
            ("option_flow", "/api/option-trades/flow-alerts"),
            ("dark_pool", "/api/darkpool/{ticker}"),
            ("greeks", "/api/stock/{ticker}/greeks"),
            ("net_impact", "/api/market/top-net-impact"),
        ]
        
        for name, endpoint in core_endpoints:
            if name not in endpoints_health:
                health = self.check_uw_endpoint_health(endpoint, "AAPL")
                endpoints_health[name] = health
        
        return endpoints_health
    
    def check_order_execution_pipeline(self) -> Dict[str, Any]:
        """Check order execution pipeline health."""
        result = {
            "status": "unknown",
            "last_order_age_sec": None,
            "orders_1h": 0,
            "orders_3h": 0,
            "orders_24h": 0,
            "fill_rate": 0.0,
            "avg_fill_time_sec": None,
            "errors_1h": 0
        }
        
        orders_file = DATA_DIR / "live_orders.jsonl"
        if not orders_file.exists():
            result["status"] = "no_orders_file"
            return result
        
        now = time.time()
        cutoff_1h = now - 3600
        cutoff_3h = now - 10800
        cutoff_24h = now - 86400
        
        orders_1h = []
        orders_3h = []
        orders_24h = []
        filled_orders = []
        submitted_orders = []
        
        try:
            for line in orders_file.read_text().splitlines()[-500:]:
                try:
                    event = json.loads(line.strip())
                    event_ts = event.get("_ts", 0)
                    event_type = event.get("event", "")
                    
                    if event_ts > cutoff_1h:
                        orders_1h.append(event)
                    if event_ts > cutoff_3h:
                        orders_3h.append(event)
                    if event_ts > cutoff_24h:
                        orders_24h.append(event)
                    
                    if event_type in ["MARKET_FILLED", "LIMIT_FILLED"]:
                        filled_orders.append(event)
                    elif event_type == "ORDER_SUBMITTED":
                        submitted_orders.append(event)
                except:
                    pass
            
            result["orders_1h"] = len(orders_1h)
            result["orders_3h"] = len(orders_3h)
            result["orders_24h"] = len(orders_24h)
            
            if submitted_orders:
                result["fill_rate"] = len(filled_orders) / len(submitted_orders)
            
            if orders_1h:
                last_order = max(orders_1h, key=lambda x: x.get("_ts", 0))
                result["last_order_age_sec"] = now - last_order.get("_ts", 0)
            
            # Check for errors
            error_log = DATA_DIR / "worker_error.jsonl"
            if error_log.exists():
                for line in error_log.read_text().splitlines()[-100:]:
                    try:
                        event = json.loads(line)
                        if event.get("_ts", 0) > cutoff_1h and "order" in event.get("event", "").lower():
                            result["errors_1h"] += 1
                    except:
                        pass
            
            # Determine status
            market_open, _ = self.is_market_open()
            if market_open:
                if result["orders_1h"] == 0 and result["last_order_age_sec"] and result["last_order_age_sec"] > 3600:
                    result["status"] = "degraded"  # No orders in last hour during market hours
                elif result["orders_1h"] > 0:
                    result["status"] = "healthy"
                else:
                    result["status"] = "no_recent_orders"
            else:
                result["status"] = "market_closed"  # Normal if market is closed
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive health status for all components."""
        market_open, market_status = self.is_market_open()
        last_order_ts = self.get_last_order_timestamp()
        
        result = {
            "timestamp": time.time(),
            "market_status": market_status,
            "market_open": market_open,
            "last_order": {
                "timestamp": last_order_ts,
                "age_sec": time.time() - last_order_ts if last_order_ts else None,
                "age_hours": (time.time() - last_order_ts) / 3600 if last_order_ts else None
            },
            "uw_api_endpoints": {},
            "signal_components": {},
            "order_execution": {},
            "overall_health": "unknown"
        }
        
        # Check UW API endpoints
        uw_health = self.check_uw_api_health()
        result["uw_api_endpoints"] = {
            name: {
                "status": h.status,
                "error_rate_1h": h.error_rate_1h,
                "avg_latency_ms": h.avg_latency_ms,
                "last_error": h.last_error
            }
            for name, h in uw_health.items()
        }
        
        # Check signal generation
        signal_health = self.check_signal_generation_health()
        result["signal_components"] = {
            name: {
                "status": s.status,
                "last_update_age_sec": s.last_update_age_sec,
                "data_freshness_sec": s.data_freshness_sec,
                "error_rate_1h": s.error_rate_1h,
                "details": s.details
            }
            for name, s in signal_health.items()
        }
        
        # Check order execution
        result["order_execution"] = self.check_order_execution_pipeline()
        
        # Determine overall health
        critical_issues = []
        warnings = []
        
        # Check for critical issues
        for name, health in uw_health.items():
            if health.status in ["auth_failed", "connection_error"]:
                critical_issues.append(f"UW API {name}: {health.status}")
        
        if result["order_execution"]["status"] == "degraded" and market_open:
            warnings.append("No orders in last hour during market hours")
        
        # Check signal health
        unhealthy_signals = [name for name, s in signal_health.items() if s.status == "no_data"]
        if unhealthy_signals:
            warnings.append(f"Signals with no data: {', '.join(unhealthy_signals)}")
        
        if critical_issues:
            result["overall_health"] = "critical"
            result["critical_issues"] = critical_issues
        elif warnings:
            result["overall_health"] = "degraded"
            result["warnings"] = warnings
        else:
            result["overall_health"] = "healthy"
        
        return result

def get_sre_health() -> Dict[str, Any]:
    """Get SRE health status - main entry point."""
    engine = SREMonitoringEngine()
    health = engine.get_comprehensive_health()
    
    # Trigger self-healing if issues detected
    try:
        from self_healing_monitor import SelfHealingMonitor
        monitor = SelfHealingMonitor()
        
        # Check if we should run healing (only if degraded/critical)
        if health.get("overall_health") in ["degraded", "critical"]:
            # Run healing in background (non-blocking)
            import threading
            def run_healing():
                try:
                    result = monitor.run_healing_cycle()
                    health["self_healing"] = {
                        "last_run": result.get("timestamp"),
                        "issues_healed": result.get("issues_healed", 0),
                        "issues_skipped": result.get("issues_skipped", 0),
                        "status": "completed"
                    }
                except Exception as e:
                    health["self_healing"] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Run healing in background thread
            healing_thread = threading.Thread(target=run_healing, daemon=True)
            healing_thread.start()
            
            # Add pending status
            health["self_healing"] = {
                "status": "running",
                "message": "Healing cycle in progress"
            }
    except Exception as e:
        # Don't fail if self-healing isn't available
        pass
    
    return health

if __name__ == "__main__":
    engine = SREMonitoringEngine()
    health = engine.get_comprehensive_health()
    print(json.dumps(health, indent=2, default=str))
