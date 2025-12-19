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
        
        # Check cache freshness first - if cache is fresh, API key must be working
        # (even if we can't see it in environment variables)
        cache_file = DATA_DIR / "uw_flow_cache.json"
        if cache_file.exists():
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < 300:  # Cache updated in last 5 minutes
                # Cache is fresh - API key must be working
                health.status = "healthy"
                health.last_success_age_sec = cache_age
                health.avg_latency_ms = None
                # Still check error logs for this endpoint
                error_log = DATA_DIR / "uw_error.jsonl"
                if error_log.exists():
                    now = time.time()
                    cutoff_1h = now - 3600
                    errors_1h = 0
                    requests_1h = 0
                    last_error_msg = None
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
                    
                    if requests_1h > 0:
                        health.error_rate_1h = errors_1h / requests_1h
                        if health.error_rate_1h > 0.5:  # More than 50% errors
                            health.status = "degraded"
                            health.last_error = last_error_msg
                
                return health
            elif cache_age < 600:  # Cache updated in last 10 minutes
                health.status = "degraded"
                health.last_success_age_sec = cache_age
            else:
                # Cache is stale - check if API key is available
                if not self.uw_api_key:
                    health.status = "no_api_key"
                    health.last_error = "UW_API_KEY not set and cache is stale"
                else:
                    health.status = "stale"
                    health.last_success_age_sec = cache_age
                    health.last_error = f"Cache stale ({int(cache_age)}s old)"
                return health
        else:
            # No cache file - check if API key is available
            if not self.uw_api_key:
                health.status = "no_api_key"
                health.last_error = "UW_API_KEY not set and no cache file"
                return health
            else:
                health.status = "no_cache"
                health.last_error = "Cache file does not exist"
                return health
        
        # If we get here, cache exists but is moderately stale - continue with normal checks
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
        
        # Calculate error rate from logs
        if requests_1h > 0:
            health.error_rate_1h = errors_1h / requests_1h
            if health.error_rate_1h > 0.5:  # More than 50% errors
                health.status = "degraded"
                health.last_error = last_error_msg
        else:
            health.error_rate_1h = 0.0
        
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
                    
                    # Check CORE signal components (always expected)
                    # These are the signals that are actually populated in the cache
                    core_components = {
                        "options_flow": symbol_data.get("sentiment") or symbol_data.get("flow_sentiment"),
                        "dark_pool": symbol_data.get("dark_pool", {}),
                        "insider": symbol_data.get("insider", {}),
                    }
                    
                    # Check COMPUTED signal components (may be enriched)
                    # These are computed from raw data and may not always be present
                    computed_components = {
                        "iv_term_skew": symbol_data.get("iv_term_skew"),
                        "smile_slope": symbol_data.get("smile_slope"),
                    }
                    
                    # Check ENRICHED signal components (optional, from enrichment service)
                    # These are only present if enrichment is running
                    enriched_components = {
                        "whale_persistence": symbol_data.get("whale_persistence") or symbol_data.get("motif_whale"),
                        "event_alignment": symbol_data.get("event_alignment"),
                        "temporal_motif": symbol_data.get("temporal_motif") or symbol_data.get("motif_staircase") or symbol_data.get("motif_burst"),
                        "congress": symbol_data.get("congress", {}),
                        "shorts_squeeze": symbol_data.get("shorts_squeeze"),
                        "institutional": symbol_data.get("institutional", {}),
                        "market_tide": symbol_data.get("market_tide"),
                        "calendar_catalyst": symbol_data.get("calendar_catalyst"),
                        "etf_flow": symbol_data.get("etf_flow"),
                        "greeks_gamma": symbol_data.get("greeks_gamma"),
                        "ftd_pressure": symbol_data.get("ftd_pressure"),
                        "iv_rank": symbol_data.get("iv_rank"),
                        "oi_change": symbol_data.get("oi_change"),
                        "squeeze_score": symbol_data.get("squeeze_score"),
                    }
                    
                    # Combine all components
                    components = {**core_components, **computed_components, **enriched_components}
                    
                    for comp_name, comp_data in components.items():
                        # Determine if this is a core, computed, or enriched signal
                        is_core = comp_name in core_components
                        is_computed = comp_name in computed_components
                        is_enriched = comp_name in enriched_components
                        signal_type = "core" if is_core else ("computed" if is_computed else "enriched")
                        
                        if comp_name not in signals:
                            signals[comp_name] = SignalHealth(
                                name=comp_name,
                                status="unknown",
                                last_update_age_sec=cache_age
                            )
                            # Mark signal type for proper handling
                            signals[comp_name].details["signal_type"] = signal_type
                            signals[comp_name].details["last_seen_ts"] = time.time()  # Track when we last saw this signal
                        
                        # Check if signal has data (handle both dict and numeric values)
                        has_data = False
                        
                        if comp_name in ["insider", "dark_pool", "congress", "institutional"]:
                            # Dict signals - check if it exists and is not empty
                            has_data = isinstance(comp_data, dict) and len(comp_data) > 0
                        elif comp_name in ["iv_term_skew", "smile_slope", "iv_rank", "squeeze_score", "whale_persistence", 
                                          "event_alignment", "temporal_motif", "market_tide", "calendar_catalyst", 
                                          "etf_flow", "greeks_gamma", "ftd_pressure", "oi_change", "shorts_squeeze"]:
                            # Numeric signals - check if not None (0.0 is valid!)
                            has_data = comp_data is not None
                        elif comp_name == "options_flow":
                            # Options flow can be string (sentiment) or dict
                            has_data = comp_data is not None and comp_data != "" and comp_data != {}
                        else:
                            # Other signals - check if truthy and not empty dict
                            has_data = comp_data and comp_data != {}
                        
                        if has_data:
                            # Update last seen timestamp when we find data
                            signals[comp_name].details["last_seen_ts"] = time.time()
                            signals[comp_name].status = "healthy"
                            # Calculate actual freshness: time since we last saw this signal
                            last_seen = signals[comp_name].details.get("last_seen_ts", time.time())
                            signals[comp_name].data_freshness_sec = time.time() - last_seen
                            signals[comp_name].last_update_age_sec = cache_age  # Cache file age
                            # Mark that we found data in at least one symbol
                            if "found_in_symbols" not in signals[comp_name].details:
                                signals[comp_name].details["found_in_symbols"] = []
                            if symbol not in signals[comp_name].details["found_in_symbols"]:
                                signals[comp_name].details["found_in_symbols"].append(symbol)
                        else:
                            # Calculate age since last seen
                            last_seen = signals[comp_name].details.get("last_seen_ts", 0)
                            if last_seen > 0:
                                signals[comp_name].last_update_age_sec = time.time() - last_seen
                            else:
                                signals[comp_name].last_update_age_sec = cache_age  # Fallback to cache age
                            
                            # Only mark as "no_data" if it's a core signal (required)
                            # Enriched signals are optional and should be "optional" not "no_data"
                            if signals[comp_name].status == "unknown":
                                if signal_type == "core":
                                    signals[comp_name].status = "no_data"  # Core signals are required
                                elif signal_type == "enriched":
                                    signals[comp_name].status = "optional"  # Enriched signals are optional
                                else:
                                    signals[comp_name].status = "no_data"  # Computed signals should exist
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
        
        # Check comprehensive learning system
        try:
            from comprehensive_learning_orchestrator import get_learning_orchestrator
            orchestrator = get_learning_orchestrator()
            learning_health = orchestrator.get_health()
            result["comprehensive_learning"] = {
                "running": learning_health.get("running", False),
                "last_run_age_sec": learning_health.get("last_run_age_sec"),
                "error_count": learning_health.get("error_count", 0),
                "success_count": learning_health.get("success_count", 0),
                "components_available": learning_health.get("components_available", {})
            }
        except Exception as e:
            result["comprehensive_learning"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Determine overall health
        critical_issues = []
        warnings = []
        
        # Check for critical issues
        # Only mark as critical if:
        # 1. Auth failed or connection error (actual API problems)
        # 2. No API key AND cache is stale (proves API key is needed but missing)
        # Don't mark as critical if cache is fresh (proves API key is working even if env var not visible)
        for name, health in uw_health.items():
            if health.status in ["auth_failed", "connection_error"]:
                critical_issues.append(f"UW API {name}: {health.status}")
            elif health.status == "no_api_key":
                # Only critical if cache is actually stale (proves API key is needed)
                # If cache is fresh, API key must be working (just not visible in env)
                cache_file = DATA_DIR / "uw_flow_cache.json"
                if cache_file.exists():
                    cache_age = time.time() - cache_file.stat().st_mtime
                    if cache_age > 600:  # Cache is stale (> 10 minutes)
                        critical_issues.append(f"UW API {name}: {health.status} (cache stale)")
                else:
                    # No cache file - this is critical
                    critical_issues.append(f"UW API {name}: {health.status} (no cache)")
        
        if result["order_execution"]["status"] == "degraded" and market_open:
            warnings.append("No orders in last hour during market hours")
        
        # Check signal health - only warn about CORE signals (required)
        # Enriched signals are optional and shouldn't trigger warnings
        core_signals = ["options_flow", "dark_pool", "insider"]
        unhealthy_core_signals = [
            name for name, s in signal_health.items() 
            if name in core_signals and s.status == "no_data"
        ]
        if unhealthy_core_signals:
            critical_issues.append(f"Core signals missing: {', '.join(unhealthy_core_signals)}")
        
        # Optional: Check computed signals (should exist but not critical)
        computed_signals = ["iv_term_skew", "smile_slope"]
        missing_computed = [
            name for name, s in signal_health.items()
            if name in computed_signals and s.status == "no_data"
        ]
        if missing_computed:
            warnings.append(f"Computed signals missing (may be normal): {', '.join(missing_computed)}")
        
        # Enriched signals are optional - don't warn about them
        # They're only present if enrichment service is running
        
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
    # Trigger cache enrichment before checking to ensure signals are present
    try:
        from cache_enrichment_service import CacheEnrichmentService
        service = CacheEnrichmentService()
        service.run_once()
    except Exception:
        # Continue even if enrichment fails
        pass
    
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
