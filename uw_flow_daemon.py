#!/usr/bin/env python3
"""
UW Flow Daemon
==============
Continuously polls Unusual Whales API and populates uw_flow_cache.json.
This is the ONLY component that should make UW API calls.

Uses SmartPoller to optimize API usage based on data freshness requirements.
"""

import os
import sys
import time
import json
import signal
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Signal-safe print function to avoid reentrant call issues
_print_lock = False
def safe_print(*args, **kwargs):
    """Print that's safe to call from signal handlers and avoids reentrant calls."""
    global _print_lock
    if _print_lock:
        return  # Prevent reentrant calls
    _print_lock = True
    try:
        msg = ' '.join(str(a) for a in args) + '\n'
        os.write(1, msg.encode())  # stdout file descriptor is 1
    except:
        pass  # If print fails, just continue
    finally:
        _print_lock = False

# #region agent log
DEBUG_LOG_PATH = Path(__file__).parent / ".cursor" / "debug.log"
_DEBUG_LOGGING = False  # Flag to prevent reentrant debug logging
def debug_log(location, message, data=None, hypothesis_id=None):
    global _DEBUG_LOGGING
    if _DEBUG_LOGGING:
        return  # Prevent reentrant calls
    _DEBUG_LOGGING = True
    try:
        # Ensure directory exists
        try:
            DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        except Exception as dir_err:
            # If directory creation fails, try to write error to stderr
            try:
                os.write(2, f"[DEBUG-ERROR] Failed to create dir {DEBUG_LOG_PATH.parent}: {dir_err}\n".encode())
            except:
                pass
            _DEBUG_LOGGING = False
            return
        
        # Create log entry
        try:
            log_entry = json.dumps({
                "sessionId": "uw-daemon-debug",
                "runId": "run1",
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data or {},
                "timestamp": int(time.time() * 1000)
            }) + "\n"
        except Exception as json_err:
            try:
                os.write(2, f"[DEBUG-ERROR] Failed to create JSON: {json_err}\n".encode())
            except:
                pass
            _DEBUG_LOGGING = False
            return
        
        # Write to file
        try:
            with DEBUG_LOG_PATH.open("a") as f:
                f.write(log_entry)
                f.flush()  # Force flush to ensure it's written
        except Exception as write_err:
            try:
                os.write(2, f"[DEBUG-ERROR] Failed to write to {DEBUG_LOG_PATH}: {write_err}\n".encode())
            except:
                pass
            _DEBUG_LOGGING = False
            return
        
        # Use os.write to avoid reentrant print issues (optional debug output to stderr)
        try:
            debug_msg = f"[DEBUG] {location}: {message} {json.dumps(data or {})}\n"
            os.write(2, debug_msg.encode())  # Write directly to stderr file descriptor
        except:
            pass  # If stderr write fails, continue - file write succeeded
    except Exception as e:
        # Use os.write for error reporting too
        try:
            error_msg = f"[DEBUG-ERROR] Unexpected error in debug_log: {e}\n"
            os.write(2, error_msg.encode())
            import traceback
            tb_msg = f"[DEBUG-ERROR] Traceback: {traceback.format_exc()}\n"
            os.write(2, tb_msg.encode())
        except:
            pass
    finally:
        _DEBUG_LOGGING = False
# #endregion

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config.registry import CacheFiles, Directories, StateFiles, read_json, atomic_write_json, append_jsonl
    # Test debug_log immediately after imports
    try:
        debug_log("uw_flow_daemon.py:imports", "Imports successful", {}, "H1")
    except Exception as debug_err:
        # If debug_log fails, write to stderr directly
        try:
            os.write(2, f"[CRITICAL] debug_log failed: {debug_err}\n".encode())
        except:
            pass
except Exception as e:
    try:
        debug_log("uw_flow_daemon.py:imports", "Import failed", {"error": str(e)}, "H1")
    except:
        pass
    raise

load_dotenv()

DATA_DIR = Directories.DATA
CACHE_FILE = CacheFiles.UW_FLOW_CACHE

class UWClient:
    """Unusual Whales API client."""
    
    def __init__(self, api_key=None):
        from config.registry import APIConfig
        self.api_key = api_key or os.getenv("UW_API_KEY")
        self.base = APIConfig.UW_BASE_URL
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
    
    def _get(self, path_or_url: str, params: dict = None) -> dict:
        """Make API request with quota tracking."""
        url = path_or_url if path_or_url.startswith("http") else f"{self.base}{path_or_url}"
        
        # #region agent log
        debug_log("uw_flow_daemon.py:_get", "API call attempt", {"url": url, "has_api_key": bool(self.api_key)}, "H3")
        # #endregion
        
        # QUOTA TRACKING: Log all UW API calls
        quota_log = CacheFiles.UW_API_QUOTA
        quota_log.parent.mkdir(parents=True, exist_ok=True)
        try:
            with quota_log.open("a") as f:
                f.write(json.dumps({
                    "ts": int(time.time()),
                    "url": url,
                    "params": params or {},
                    "source": "uw_flow_daemon"
                }) + "\n")
        except Exception:
            pass  # Don't fail on quota logging
        
        try:
            # V4.0: Apply API resilience with exponential backoff
            try:
                from api_resilience import ExponentialBackoff, get_signal_queue, is_panic_regime
                backoff = ExponentialBackoff(max_retries=5, base_delay=1.0, max_delay=60.0)
                
                def make_request():
                    return requests.get(url, headers=self.headers, params=params or {}, timeout=10)
                
                r = backoff(make_request)()
            except ImportError:
                # Fallback if api_resilience not available
                r = requests.get(url, headers=self.headers, params=params or {}, timeout=10)
            
            # Check rate limit headers
            daily_count = r.headers.get("x-uw-daily-req-count")
            daily_limit = r.headers.get("x-uw-token-req-limit")
            
            if daily_count and daily_limit:
                count = int(daily_count)
                limit = int(daily_limit)
                pct = (count / limit * 100) if limit > 0 else 0
                
                # Log if we're getting close to limit
                if pct > 75:
                    safe_print(f"[UW-DAEMON] ⚠️  Rate limit warning: {count}/{limit} ({pct:.1f}%)")
                elif pct > 90:
                    safe_print(f"[UW-DAEMON] 🚨 Rate limit critical: {count}/{limit} ({pct:.1f}%)")
            
                # Check for 429 (rate limited) - V4.0: Queue signal if in PANIC regime
            if r.status_code == 429:
                error_data = r.json() if r.content else {}
                safe_print(f"[UW-DAEMON] ❌ RATE LIMITED (429): {error_data.get('message', 'Daily limit hit')}")
                
                # V4.0: Queue signal for later processing if in PANIC regime
                try:
                    from api_resilience import get_signal_queue, is_panic_regime
                    from datetime import datetime, timezone
                    if is_panic_regime():
                        queue = get_signal_queue()
                        queue.enqueue({
                            "url": url,
                            "params": params or {},
                            "error": f"Rate limited (429): {error_data.get('message', 'Daily limit hit')}",
                            "daily_count": daily_count,
                            "daily_limit": daily_limit,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        safe_print(f"[UW-DAEMON] 🔄 Signal queued for later processing (PANIC regime)")
                except ImportError:
                    pass  # API resilience not available - continue with existing behavior
                except Exception as queue_error:
                    safe_print(f"[UW-DAEMON] WARNING: Failed to queue signal: {queue_error}")
                
                safe_print(f"[UW-DAEMON] ⚠️  Stopping polling until limit resets (8PM EST)")
                append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {
                    "event": "UW_API_RATE_LIMITED",
                    "url": url,
                    "status": 429,
                    "daily_count": daily_count,
                    "daily_limit": daily_limit,
                    "message": error_data.get("message", ""),
                    "queued": False,  # Set based on actual queue status above
                    "ts": int(time.time())
                })
                # Set a flag to stop polling for a while
                # The daemon will continue running but won't make API calls
                return {"data": [], "_rate_limited": True}
            
            # Log non-200 responses for debugging
            if r.status_code != 200:
                safe_print(f"[UW-DAEMON] ⚠️  API returned status {r.status_code} for {url}")
                try:
                    error_text = r.text[:200] if r.text else "No response body"
                    safe_print(f"[UW-DAEMON] Response: {error_text}")
                except:
                    pass
            
            r.raise_for_status()
            response_data = r.json()
            # #region agent log
            debug_log("uw_flow_daemon.py:_get", "API call success", {
                "url": url, 
                "status": r.status_code,
                "has_data": bool(response_data.get("data")),
                "data_type": type(response_data.get("data")).__name__,
                "data_keys": list(response_data.keys()) if isinstance(response_data, dict) else []
            }, "H3")
            # #endregion
            return response_data
        except requests.exceptions.HTTPError as e:
            # #region agent log
            debug_log("uw_flow_daemon.py:_get", "API HTTP error", {
                "url": url,
                "status": getattr(e.response, 'status_code', None),
                "error": str(e)
            }, "H3")
            # #endregion
            append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {
                "event": "UW_API_ERROR",
                "url": url,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None),
                "ts": int(time.time())
            })
            return {"data": []}
        except Exception as e:
            # #region agent log
            debug_log("uw_flow_daemon.py:_get", "API exception", {
                "url": url,
                "error": str(e),
                "error_type": type(e).__name__
            }, "H3")
            # #endregion
            append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {
                "event": "UW_API_ERROR",
                "url": url,
                "error": str(e),
                "ts": int(time.time())
            })
            return {"data": []}
    
    def get_option_flow(self, ticker: str, limit: int = 100) -> List[Dict]:
        """Get option flow for a ticker."""
        raw = self._get("/api/option-trades/flow-alerts", params={"symbol": ticker, "limit": limit})
        data = raw.get("data", [])
        if data:
            safe_print(f"[UW-DAEMON] Retrieved {len(data)} flow trades for {ticker}")
        return data
    
    def get_dark_pool_levels(self, ticker: str) -> List[Dict]:
        """Get dark pool levels for a ticker."""
        raw = self._get(f"/api/darkpool/{ticker}")
        return raw.get("data", [])
    
    def get_greek_exposure(self, ticker: str) -> Dict:
        """Get Greek exposure for a ticker (detailed exposure data)."""
        # FIXED: Use correct endpoint per uw_signal_contracts.py
        raw = self._get(f"/api/stock/{ticker}/greek-exposure")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_greeks(self, ticker: str) -> Dict:
        """Get Greeks for a ticker (basic greeks data - different from greek_exposure)."""
        # This is a separate endpoint from greek_exposure (per sre_monitoring.py core_endpoints)
        raw = self._get(f"/api/stock/{ticker}/greeks")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_top_net_impact(self, limit: int = 50) -> List[Dict]:
        """Get top net impact symbols."""
        raw = self._get("/api/market/top-net-impact", params={"limit": limit})
        return raw.get("data", [])
    
    def get_market_tide(self) -> Dict:
        """Get market-wide options sentiment (market tide)."""
        raw = self._get("/api/market/market-tide")
        # #region agent log
        debug_log("uw_flow_daemon.py:get_market_tide", "Raw API response", {
            "raw_type": type(raw).__name__,
            "raw_keys": list(raw.keys()) if isinstance(raw, dict) else [],
            "has_data_key": "data" in raw if isinstance(raw, dict) else False
        }, "H3")
        # #endregion
        
        data = raw.get("data", {})
        # #region agent log
        debug_log("uw_flow_daemon.py:get_market_tide", "Extracted data", {
            "data_type": type(data).__name__,
            "is_list": isinstance(data, list),
            "list_len": len(data) if isinstance(data, list) else 0,
            "is_dict": isinstance(data, dict),
            "dict_keys": list(data.keys()) if isinstance(data, dict) else []
        }, "H3")
        # #endregion
        
        if isinstance(data, list):
            if len(data) > 0:
                data = data[0]
            else:
                # Empty list - return empty dict
                # #region agent log
                debug_log("uw_flow_daemon.py:get_market_tide", "Empty list returned", {}, "H3")
                # #endregion
                return {}
        
        # If data is already a dict, return it; otherwise return empty dict
        result = data if isinstance(data, dict) else {}
        # #region agent log
        debug_log("uw_flow_daemon.py:get_market_tide", "Final result", {
            "result_type": type(result).__name__,
            "result_keys": list(result.keys()) if isinstance(result, dict) else [],
            "result_empty": not bool(result)
        }, "H3")
        # #endregion
        return result
    
    def get_oi_change(self, ticker: str) -> Dict:
        """Get open interest changes for a ticker."""
        raw = self._get(f"/api/stock/{ticker}/oi-change")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_etf_flow(self, ticker: str) -> Dict:
        """Get ETF inflow/outflow for a ticker."""
        raw = self._get(f"/api/etfs/{ticker}/in-outflow")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_iv_rank(self, ticker: str) -> Dict:
        """Get IV rank for a ticker."""
        raw = self._get(f"/api/stock/{ticker}/iv-rank")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_shorts_ftds(self, ticker: str) -> Dict:
        """Get fails-to-deliver data for a ticker."""
        raw = self._get(f"/api/shorts/{ticker}/ftds")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_max_pain(self, ticker: str) -> Dict:
        """Get max pain for a ticker."""
        raw = self._get(f"/api/stock/{ticker}/max-pain")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_insider(self, ticker: str) -> Dict:
        """Get insider trading data for a ticker."""
        raw = self._get(f"/api/insider/{ticker}")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_calendar(self, ticker: str) -> Dict:
        """Get calendar/events data for a ticker."""
        raw = self._get(f"/api/calendar/{ticker}")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_congress(self, ticker: str) -> Dict:
        """
        Get congress trading data.
        
        NOTE: Per-ticker endpoint `/api/congress/{ticker}` returns 404.
        Congress data may be market-wide only. This endpoint is kept for
        compatibility but will return empty dict.
        
        Reference: https://api.unusualwhales.com/docs#/
        """
        try:
            # Try per-ticker first (may not exist)
            raw = self._get(f"/api/congress/{ticker}")
            data = raw.get("data", {})
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            return data if isinstance(data, dict) else {}
        except Exception:
            # Per-ticker doesn't exist - return empty
            # TODO: Check if market-wide endpoint exists
            return {}
    
    def get_institutional(self, ticker: str) -> Dict:
        """
        Get institutional data.
        
        NOTE: Per-ticker endpoint `/api/institutional/{ticker}` returns 404.
        Institutional data may be market-wide only. This endpoint is kept for
        compatibility but will return empty dict.
        
        Reference: https://api.unusualwhales.com/docs#/
        """
        try:
            # Try per-ticker first (may not exist)
            raw = self._get(f"/api/institutional/{ticker}")
            data = raw.get("data", {})
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            return data if isinstance(data, dict) else {}
        except Exception:
            # Per-ticker doesn't exist - return empty
            # TODO: Check if market-wide endpoint exists
            return {}


class SmartPoller:
    """Intelligent polling manager to optimize API usage."""
    
    def __init__(self):
        self.state_file = StateFiles.SMART_POLLER
        # OPTIMIZED: Maximize API usage while staying under 15,000/day limit
        # Market hours: 9:30 AM - 4:00 PM ET = 6.5 hours = 390 minutes
        # Target: Use ~14,000 calls (93% of limit) to leave buffer
        #
        # Calculation:
        # - Option flow (most critical): 53 tickers × (390/2.5) = 8,268 calls
        # - Dark pool: 53 tickers × (390/10) = 2,067 calls  
        # - Greeks: 53 tickers × (390/30) = 689 calls
        # - Top net impact (market-wide): 390/5 = 78 calls
        # Total: 8,268 + 2,067 + 689 + 78 = 11,102 calls (74% of limit)
        #
        # We can increase frequency if needed, but this is safe
        self.intervals = {
            "option_flow": 150,       # 2.5 min: Most critical data, poll frequently
            "dark_pool_levels": 600,  # 10 min: Important but less time-sensitive
            "greek_exposure": 1800,   # 30 min: Detailed exposure (changes slowly)
            "greeks": 1800,           # 30 min: Basic greeks (changes slowly)
            "top_net_impact": 300,    # 5 min: Market-wide, poll moderately
            "market_tide": 300,       # 5 min: Market-wide sentiment
            "insider": 1800,          # 30 min: Insider trading (changes slowly)
            "calendar": 3600,         # 60 min: Calendar events (changes slowly)
            "congress": 1800,         # 30 min: Congress trading (changes slowly)
            "institutional": 1800,    # 30 min: Institutional data (changes slowly)
            "oi_change": 900,         # 15 min: OI changes per ticker
            "etf_flow": 1800,         # 30 min: ETF flows per ticker
            "iv_rank": 1800,          # 30 min: IV rank per ticker
            "shorts_ftds": 3600,      # 60 min: FTD data changes slowly
            "max_pain": 900,           # 15 min: Max pain per ticker
        }
        self.last_call = self._load_state()
    
    def _load_state(self) -> dict:
        """Load persisted polling timestamps."""
        try:
            if self.state_file.exists():
                return json.loads(self.state_file.read_text())
        except Exception:
            pass
        return {}
    
    def _save_state(self):
        """Persist polling timestamps."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.last_call, indent=2))
            tmp.replace(self.state_file)
        except Exception:
            pass
    
    def should_poll(self, endpoint: str, force_first: bool = False) -> bool:
        """Check if enough time has passed since last call."""
        now = time.time()
        last = self.last_call.get(endpoint, 0)
        base_interval = self.intervals.get(endpoint, 60)
        
        # #region agent log
        debug_log("uw_flow_daemon.py:should_poll", "Polling decision", {
            "endpoint": endpoint,
            "force_first": force_first,
            "last": last,
            "interval": base_interval,
            "time_since_last": now - last if last > 0 else None
        }, "H5")
        # #endregion
        
        # If this is the first poll (no last call recorded), allow it immediately
        if force_first and last == 0:
            self.last_call[endpoint] = now
            self._save_state()
            # #region agent log
            debug_log("uw_flow_daemon.py:should_poll", "First poll allowed", {"endpoint": endpoint}, "H5")
            # #endregion
            return True
        
        # OPTIMIZATION: During market hours, use normal intervals
        # Outside market hours, use longer intervals to conserve quota
        if self._is_market_hours():
            interval = base_interval
        else:
            # Outside market hours: poll 3x less frequently (conserve quota)
            interval = base_interval * 3
        
        if now - last < interval:
            # #region agent log
            debug_log("uw_flow_daemon.py:should_poll", "Polling skipped - interval not elapsed", {
                "endpoint": endpoint,
                "time_remaining": interval - (now - last)
            }, "H5")
            # #endregion
            return False
        
        # Update timestamp
        self.last_call[endpoint] = now
        self._save_state()
        # #region agent log
        debug_log("uw_flow_daemon.py:should_poll", "Polling allowed", {"endpoint": endpoint}, "H5")
        # #endregion
        return True
    
    def _is_market_hours(self) -> bool:
        """Check if currently in trading hours (9:30 AM - 4:00 PM ET).
        
        Uses US/Eastern timezone which automatically handles DST (EST/EDT).
        Matches timezone usage in main.py and sre_monitoring.py.
        """
        try:
            import pytz
            et = pytz.timezone('US/Eastern')  # Handles DST automatically (EST/EDT)
            now_et = datetime.now(et)
            hour_min = now_et.hour * 60 + now_et.minute
            market_open = 9 * 60 + 30  # 9:30 AM ET
            market_close = 16 * 60      # 4:00 PM ET
            is_open = market_open <= hour_min < market_close
            
            # Log market status for debugging (only log when closed to reduce noise)
            if not is_open:
                safe_print(f"[UW-DAEMON] Market is CLOSED (ET time: {now_et.strftime('%H:%M')}) - will use longer polling intervals")
            
            return is_open
        except Exception as e:
            # Maintain backward compatibility: default to True if timezone check fails
            # This matches original behavior and prevents breaking existing functionality
            safe_print(f"[UW-DAEMON] ⚠️  Error checking market hours: {e} - defaulting to OPEN (backward compatibility)")
            return True


class UWFlowDaemon:
    """Daemon that polls UW API and populates cache."""
    
    def __init__(self):
        self.client = UWClient()
        self.poller = SmartPoller()
        self._rate_limited = False  # Track if we've hit rate limit
        self.tickers = os.getenv("TICKERS", 
            "AAPL,MSFT,GOOGL,AMZN,META,NVDA,TSLA,AMD,NFLX,INTC,"
            "SPY,QQQ,IWM,DIA,XLF,XLE,XLK,XLV,XLI,XLP,"
            "JPM,BAC,GS,MS,C,WFC,BLK,V,MA,"
            "COIN,PLTR,SOFI,HOOD,RIVN,LCID,F,GM,NIO,"
            "BA,CAT,XOM,CVX,COP,SLB,"
            "JNJ,PFE,MRNA,UNH,WMT,TGT,COST,HD,LOW"
        ).split(",")
        self.tickers = [t.strip().upper() for t in self.tickers if t.strip()]
        self.running = True
        self._shutting_down = False  # Prevent reentrant signal handler calls
        self._loop_entered = False  # Track if main loop has been entered
        
        # Register signal handlers BEFORE any debug_log calls that might block
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # #region agent log
        try:
            debug_log("uw_flow_daemon.py:__init__", "UWFlowDaemon initialized", {
                "ticker_count": len(self.tickers),
                "has_api_key": bool(self.client.api_key) if hasattr(self, 'client') else False
            }, "H1")
        except Exception as debug_err:
            safe_print(f"[UW-DAEMON] Debug log failed in __init__ (non-critical): {debug_err}")
        # #endregion
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        # CRITICAL FIX: Ignore signals until main loop is entered
        # This prevents premature shutdown during initialization
        if not self._loop_entered:
            safe_print(f"[UW-DAEMON] Signal {signum} received before loop entry - IGNORING (daemon still initializing)")
            return  # Ignore signal until loop is entered
        
        # Use safe_print immediately to avoid any blocking
        safe_print(f"[UW-DAEMON] Signal handler called: signal {signum}")
        
        # #region agent log
        try:
            debug_log("uw_flow_daemon.py:_signal_handler", "Signal received", {
                "signum": signum,
                "signal_name": "SIGTERM" if signum == 15 else "SIGINT" if signum == 2 else f"UNKNOWN({signum})",
                "already_shutting_down": self._shutting_down,
                "running_before": self.running,
                "loop_entered": self._loop_entered
            }, "H2")
        except Exception as debug_err:
            safe_print(f"[UW-DAEMON] Debug log failed in signal handler: {debug_err}")
        # #endregion
        
        # Prevent reentrant calls - if already shutting down, just set flag
        if self._shutting_down:
            self.running = False
            # #region agent log
            debug_log("uw_flow_daemon.py:_signal_handler", "Already shutting down, setting running=False", {}, "H2")
            # #endregion
            return
        
        self._shutting_down = True
        # Use os.write to avoid reentrant print/stderr issues
        try:
            import os
            msg = f"\n[UW-DAEMON] Received signal {signum}, shutting down...\n"
            os.write(2, msg.encode())  # Write directly to stderr file descriptor (2)
        except:
            pass  # If write fails, just continue - we still need to set running=False
        self.running = False
        # #region agent log
        debug_log("uw_flow_daemon.py:_signal_handler", "Signal handled - running set to False", {
            "running": self.running,
            "shutting_down": self._shutting_down
        }, "H2")
        # #endregion
    
    def _normalize_flow_data(self, flow_data: List[Dict], ticker: str) -> Dict:
        """Normalize flow data into cache format."""
        if not flow_data:
            return {}
        
        # Calculate sentiment and conviction from flow
        # API may return "premium" or "total_premium" - try both
        total_premium = sum(float(t.get("total_premium") or t.get("premium") or 0) for t in flow_data)
        call_premium = sum(float(t.get("total_premium") or t.get("premium") or 0) for t in flow_data 
                          if t.get("type", "").upper() in ("CALL", "C"))
        put_premium = total_premium - call_premium
        
        net_premium = call_premium - put_premium
        
        # Sentiment based on net premium
        # FIXED: Lowered threshold from 100k to 10k to capture more flow signals
        # This ensures smaller institutional flows contribute to scores
        if net_premium > 10000:  # Lowered from 100000
            sentiment = "BULLISH"
            # Scale conviction more aggressively for smaller flows
            conviction = min(1.0, 0.3 + (net_premium / 2_000_000))  # Start at 0.3, scale to 1.0
        elif net_premium < -10000:  # Lowered from -100000
            sentiment = "BEARISH"
            # Scale conviction more aggressively for smaller flows
            conviction = min(1.0, 0.3 + (abs(net_premium) / 2_000_000))  # Start at 0.3, scale to 1.0
        else:
            sentiment = "NEUTRAL"
            # FIXED: Give small positive conviction even for neutral flows if there's any activity
            # This ensures NEUTRAL flows still contribute to scores (with stealth boost, gives ~0.4-0.6 flow component)
            if total_premium > 0:
                # Scale conviction from 0.1 to 0.3 based on total premium
                # This ensures even small flows contribute meaningfully to scores
                conviction = min(0.3, 0.1 + (total_premium / 5_000_000))
            else:
                # No activity at all - give minimal conviction so stealth boost still applies
                conviction = 0.05  # Small base so stealth boost (0.2) gives 0.25 total
        
        return {
            "sentiment": sentiment,
            "conviction": conviction,
            "total_premium": total_premium,
            "call_premium": call_premium,
            "put_premium": put_premium,
            "net_premium": net_premium,
            "trade_count": len(flow_data),
            "last_update": int(time.time())
        }
    
    def _normalize_dark_pool(self, dp_data: List[Dict]) -> Dict:
        """Normalize dark pool data.
        
        Dark pool API returns volume data, not premium. We calculate notional value
        from volume * price to estimate premium equivalent.
        """
        if not dp_data or not isinstance(dp_data, list):
            return {}
        
        # Dark pool data has: price, lit_volume, off_lit_volume, total_volume, side
        # Calculate notional value (volume * price) as proxy for premium
        total_notional = 0.0
        total_off_lit_volume = 0.0
        buy_volume = 0.0
        sell_volume = 0.0
        
        for d in dp_data:
            if not isinstance(d, dict):
                continue
            
            # Get volume and price
            price = float(d.get("price") or d.get("last_price") or 0)
            off_lit_vol = float(d.get("off_lit_volume") or d.get("dark_volume") or 0)
            total_vol = float(d.get("total_volume") or off_lit_vol or 0)
            side = str(d.get("side") or "").upper()
            
            # Calculate notional (volume * price)
            notional = total_vol * price
            total_notional += notional
            total_off_lit_volume += off_lit_vol
            
            # Track buy vs sell
            if side in ("BUY", "B"):
                buy_volume += total_vol
            elif side in ("SELL", "S"):
                sell_volume += total_vol
        
        print_count = len(dp_data)
        
        # Sentiment based on buy/sell imbalance and notional value
        net_volume = buy_volume - sell_volume
        if total_notional > 1000000 and net_volume > 0:
            sentiment = "BULLISH"
        elif total_notional > 1000000 and net_volume < 0:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        return {
            "sentiment": sentiment,
            "total_premium": total_notional,  # Use notional as proxy for premium
            "print_count": print_count,
            "total_off_lit_volume": total_off_lit_volume,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "net_volume": net_volume,
            "last_update": int(time.time())
        }
    
    def _update_cache(self, ticker: str, data: Dict):
        """Update cache for a ticker."""
        # #region agent log
        debug_log("uw_flow_daemon.py:_update_cache", "Cache update start", {
            "ticker": ticker,
            "data_keys": list(data.keys()),
            "has_data": bool(data)
        }, "H4")
        # #endregion
        
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache
        cache = {}
        if CACHE_FILE.exists():
            try:
                cache = read_json(CACHE_FILE, default={})
            except Exception:
                cache = {}
        
        # Update ticker data
        if ticker not in cache:
            cache[ticker] = {}
        
        # GRACEFUL DEGRADATION: Preserve existing flow_trades if new data is empty
        # This allows trading bot to continue using stale data when API is rate limited
        existing_flow_trades = cache[ticker].get("flow_trades", [])
        new_flow_trades = data.get("flow_trades", [])
        
        # If new data is empty but we have existing trades < 2 hours old, preserve them
        if not new_flow_trades and existing_flow_trades:
            existing_last_update = cache[ticker].get("_last_update", 0)
            current_time = time.time()
            age_sec = current_time - existing_last_update if existing_last_update else float('inf')
            
            if age_sec < 2 * 3600:  # Less than 2 hours old
                print(f"[UW-DAEMON] Preserving existing flow_trades for {ticker} ({int(age_sec/60)} min old, {len(existing_flow_trades)} trades)", flush=True)
                data["flow_trades"] = existing_flow_trades  # Preserve old trades
                # Also preserve old sentiment/conviction if new normalization failed
                if not data.get("sentiment") and cache[ticker].get("sentiment"):
                    data["sentiment"] = cache[ticker]["sentiment"]
                if not data.get("conviction") and cache[ticker].get("conviction"):
                    data["conviction"] = cache[ticker]["conviction"]
        
        cache[ticker].update(data)
        cache[ticker]["_last_update"] = int(time.time())
        
        # Add metadata
        cache["_metadata"] = {
            "last_update": int(time.time()),
            "updated_by": "uw_flow_daemon",
            "ticker_count": len([k for k in cache.keys() if not k.startswith("_")])
        }
        
        # Atomic write
        atomic_write_json(CACHE_FILE, cache)
        # #region agent log
        debug_log("uw_flow_daemon.py:_update_cache", "Cache update complete", {
            "ticker": ticker,
            "cache_size": len(cache),
            "ticker_data_keys": list(cache.get(ticker, {}).keys())
        }, "H4")
        # #endregion
    
    def _poll_ticker(self, ticker: str):
        """Poll all endpoints for a ticker."""
        try:
            # Check if we're rate limited
            # If rate limited, we skip NEW polling but keep existing cache data
            # This allows trading bot to use stale cache (graceful degradation)
            if hasattr(self, '_rate_limited') and self._rate_limited:
                # Don't make new API calls, but don't clear existing cache either
                # Trading bot can use stale data if available
                return
            
            # Poll option flow (should_poll already checks market hours)
            if self.poller.should_poll("option_flow"):
                flow_data = self.client.get_option_flow(ticker, limit=100)
                
                # Check if rate limited
                if isinstance(flow_data, dict) and flow_data.get("_rate_limited"):
                    self._rate_limited = True
                    # GRACEFUL DEGRADATION: Don't clear existing cache when rate limited
                    # Preserve old flow_trades so trading bot can use stale data
                    print(f"[UW-DAEMON] Rate limited for {ticker} - preserving existing cache data", flush=True)
                    return  # Skip update, keep old cache data
                
                if flow_data:
                    print(f"[UW-DAEMON] Polling {ticker}: got {len(flow_data)} raw trades", flush=True)
                else:
                    print(f"[UW-DAEMON] Polling {ticker}: API returned 0 trades", flush=True)
                
                flow_normalized = self._normalize_flow_data(flow_data, ticker)
                
                # CRITICAL: ALWAYS store flow_trades, even if empty or normalization fails
                # main.py needs to see the data (or lack thereof) to know what's happening
                # BUT: If we have existing cache data and API returns empty, preserve old data for graceful degradation
                existing_cache = {}
                if CACHE_FILE.exists():
                    try:
                        existing_cache = read_json(CACHE_FILE, default={})
                        existing_ticker_data = existing_cache.get(ticker, {})
                        existing_flow_trades = existing_ticker_data.get("flow_trades", [])
                        existing_last_update = existing_ticker_data.get("_last_update", 0)
                    except:
                        existing_flow_trades = []
                        existing_last_update = 0
                else:
                    existing_flow_trades = []
                    existing_last_update = 0
                
                # If API returned empty but we have existing trades < 2 hours old, preserve them
                if not flow_data and existing_flow_trades:
                    current_time = time.time()
                    age_sec = current_time - existing_last_update if existing_last_update else float('inf')
                    if age_sec < 2 * 3600:  # Less than 2 hours old
                        print(f"[UW-DAEMON] API returned empty for {ticker}, preserving existing cache ({int(age_sec/60)} min old, {len(existing_flow_trades)} trades)", flush=True)
                        flow_data = existing_flow_trades  # Use existing data
                        # Re-normalize existing data
                        flow_normalized = self._normalize_flow_data(flow_data, ticker)
                
                cache_update = {
                    "flow_trades": flow_data if flow_data else []  # Store new data or preserve old
                }
                
                if flow_normalized:
                    # Add normalized summary data
                    cache_update.update({
                        "sentiment": flow_normalized.get("sentiment", "NEUTRAL"),
                        "conviction": flow_normalized.get("conviction", 0.0),
                        "total_premium": flow_normalized.get("total_premium", 0.0),
                        "call_premium": flow_normalized.get("call_premium", 0.0),
                        "put_premium": flow_normalized.get("put_premium", 0.0),
                        "net_premium": flow_normalized.get("net_premium", 0.0),
                        "trade_count": flow_normalized.get("trade_count", 0),
                        "flow": flow_normalized,  # Also keep nested for compatibility
                    })
                else:
                    # Even if normalization fails, store basic info
                    # CRITICAL FIX: Always set sentiment and conviction, even if empty
                    # This ensures scoring can work even when API returns no data
                    cache_update.update({
                        "sentiment": "NEUTRAL",
                        "conviction": 0.0,
                        "trade_count": len(flow_data) if flow_data else 0,
                        "total_premium": 0.0,
                        "call_premium": 0.0,
                        "put_premium": 0.0,
                        "net_premium": 0.0
                    })
                
                # Always update cache (even if empty - main.py needs to know)
                # _update_cache will preserve existing data if new is empty (graceful degradation)
                self._update_cache(ticker, cache_update)
                
                # Check what was actually stored (may have preserved old data)
                final_cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}
                final_trades = final_cache.get(ticker, {}).get("flow_trades", [])
                
                if final_trades:
                    print(f"[UW-DAEMON] Cache for {ticker}: {len(final_trades)} trades stored", flush=True)
                else:
                    print(f"[UW-DAEMON] Cache for {ticker}: empty (no data available)", flush=True)
            
            # Poll dark pool
            if self.poller.should_poll("dark_pool_levels"):
                dp_data = self.client.get_dark_pool_levels(ticker)
                dp_normalized = self._normalize_dark_pool(dp_data)
                # Always store dark_pool (even if empty) so we know it was polled
                # If normalization returned empty dict, create minimal structure
                if not dp_normalized:
                    dp_normalized = {"sentiment": "NEUTRAL", "total_premium": 0.0, "print_count": 0, "last_update": int(time.time())}
                # Write dark_pool data (nested is fine - main.py reads it as cache_data.get("dark_pool", {}))
                self._update_cache(ticker, {"dark_pool": dp_normalized})
            
            # Poll greek_exposure (detailed exposure data)
            if self.poller.should_poll("greek_exposure"):
                try:
                    print(f"[UW-DAEMON] Polling greek_exposure for {ticker}...", flush=True)
                    gex_data = self.client.get_greek_exposure(ticker)
                    if gex_data:
                        # Load existing cache to merge greeks data
                        cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}
                        existing_greeks = cache.get(ticker, {}).get("greeks", {})
                        existing_greeks.update(gex_data)  # Merge with existing greeks data
                        self._update_cache(ticker, {"greeks": existing_greeks})
                        print(f"[UW-DAEMON] Updated greek_exposure for {ticker}: {len(gex_data)} fields", flush=True)
                    else:
                        print(f"[UW-DAEMON] greek_exposure for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching greek_exposure for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
            
            # Poll greeks (basic greeks data - separate endpoint)
            if self.poller.should_poll("greeks"):
                try:
                    print(f"[UW-DAEMON] Polling greeks for {ticker}...", flush=True)
                    greeks_data = self.client.get_greeks(ticker)
                    if greeks_data:
                        # Load existing cache to merge greeks data
                        cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}
                        existing_greeks = cache.get(ticker, {}).get("greeks", {})
                        existing_greeks.update(greeks_data)  # Merge with existing
                        self._update_cache(ticker, {"greeks": existing_greeks})
                        print(f"[UW-DAEMON] Updated greeks for {ticker}: {len(greeks_data)} fields", flush=True)
                    else:
                        print(f"[UW-DAEMON] greeks for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching greeks for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
            
            # Poll OI change
            if self.poller.should_poll("oi_change"):
                try:
                    print(f"[UW-DAEMON] Polling oi_change for {ticker}...", flush=True)
                    oi_data = self.client.get_oi_change(ticker)
                    # Always store oi_change (even if empty) so we know it was polled
                    if not oi_data:
                        oi_data = {}  # Store empty structure
                    self._update_cache(ticker, {"oi_change": oi_data})
                    if oi_data:
                        print(f"[UW-DAEMON] Updated oi_change for {ticker}: {len(str(oi_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] oi_change for {ticker}: API returned empty (stored as empty)", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching oi_change for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
                    # Store empty on error too
                    self._update_cache(ticker, {"oi_change": {}})
            
            # Poll ETF flow
            if self.poller.should_poll("etf_flow"):
                try:
                    print(f"[UW-DAEMON] Polling etf_flow for {ticker}...", flush=True)
                    etf_data = self.client.get_etf_flow(ticker)
                    # Always store etf_flow (even if empty) so we know it was polled
                    if not etf_data:
                        etf_data = {}  # Store empty structure
                    self._update_cache(ticker, {"etf_flow": etf_data})
                    if etf_data:
                        print(f"[UW-DAEMON] Updated etf_flow for {ticker}: {len(str(etf_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] etf_flow for {ticker}: API returned empty (stored as empty)", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching etf_flow for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
                    # Store empty on error too
                    self._update_cache(ticker, {"etf_flow": {}})
            
            # Poll IV rank
            if self.poller.should_poll("iv_rank"):
                try:
                    print(f"[UW-DAEMON] Polling iv_rank for {ticker}...", flush=True)
                    iv_data = self.client.get_iv_rank(ticker)
                    # Always store iv_rank (even if empty) so we know it was polled
                    if not iv_data:
                        iv_data = {}  # Store empty structure
                    self._update_cache(ticker, {"iv_rank": iv_data})
                    if iv_data:
                        print(f"[UW-DAEMON] Updated iv_rank for {ticker}: {len(str(iv_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] iv_rank for {ticker}: API returned empty (stored as empty)", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching iv_rank for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
                    # Store empty on error too
                    self._update_cache(ticker, {"iv_rank": {}})
            
            # Poll shorts/FTDs
            if self.poller.should_poll("shorts_ftds"):
                try:
                    print(f"[UW-DAEMON] Polling shorts_ftds for {ticker}...", flush=True)
                    ftd_data = self.client.get_shorts_ftds(ticker)
                    # Always store ftd_pressure (even if empty) so we know it was polled
                    if not ftd_data:
                        ftd_data = {}  # Store empty structure
                    self._update_cache(ticker, {"ftd_pressure": ftd_data})
                    if ftd_data:
                        print(f"[UW-DAEMON] Updated ftd_pressure for {ticker}: {len(str(ftd_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] shorts_ftds for {ticker}: API returned empty (stored as empty)", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching shorts_ftds for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
                    # Store empty on error too
                    self._update_cache(ticker, {"ftd_pressure": {}})
            
            # Poll max pain
            if self.poller.should_poll("max_pain"):
                try:
                    print(f"[UW-DAEMON] Polling max_pain for {ticker}...", flush=True)
                    max_pain_data = self.client.get_max_pain(ticker)
                    if max_pain_data:
                        # Max pain contributes to greeks_gamma signal
                        cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}
                        existing_greeks = cache.get(ticker, {}).get("greeks", {})
                        max_pain_value = max_pain_data.get("max_pain") or max_pain_data.get("maxPain")
                        if max_pain_value:
                            existing_greeks["max_pain"] = max_pain_value
                            self._update_cache(ticker, {"greeks": existing_greeks})
                            print(f"[UW-DAEMON] Updated max_pain for {ticker}: {max_pain_value}", flush=True)
                        else:
                            print(f"[UW-DAEMON] max_pain for {ticker}: no max_pain value in response (keys: {list(max_pain_data.keys())})", flush=True)
                    else:
                        print(f"[UW-DAEMON] max_pain for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching max_pain for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
            
            # Poll insider
            if self.poller.should_poll("insider"):
                try:
                    print(f"[UW-DAEMON] Polling insider for {ticker}...", flush=True)
                    insider_data = self.client.get_insider(ticker)
                    if insider_data:
                        self._update_cache(ticker, {"insider": insider_data})
                        print(f"[UW-DAEMON] Updated insider for {ticker}: {len(str(insider_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] insider for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching insider for {ticker}: {e}", flush=True)
            
            # Poll calendar
            if self.poller.should_poll("calendar"):
                try:
                    print(f"[UW-DAEMON] Polling calendar for {ticker}...", flush=True)
                    calendar_data = self.client.get_calendar(ticker)
                    # Always store calendar (even if empty) so we know it was polled
                    if not calendar_data:
                        calendar_data = {}  # Store empty structure
                    self._update_cache(ticker, {"calendar": calendar_data})
                    if calendar_data:
                        print(f"[UW-DAEMON] Updated calendar for {ticker}: {len(str(calendar_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] calendar for {ticker}: API returned empty (stored as empty)", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching calendar for {ticker}: {e}", flush=True)
                    # Store empty on error too
                    self._update_cache(ticker, {"calendar": {}})
            
            # Poll congress
            if self.poller.should_poll("congress"):
                try:
                    print(f"[UW-DAEMON] Polling congress for {ticker}...", flush=True)
                    congress_data = self.client.get_congress(ticker)
                    # Always store congress (even if empty or 404) so we know it was polled
                    if not congress_data:
                        congress_data = {}  # Store empty structure
                    self._update_cache(ticker, {"congress": congress_data})
                    if congress_data:
                        print(f"[UW-DAEMON] Updated congress for {ticker}: {len(str(congress_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] congress for {ticker}: API returned empty (stored as empty)", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching congress for {ticker}: {e}", flush=True)
                    # Store empty on error too
                    self._update_cache(ticker, {"congress": {}})
            
            # Poll institutional
            if self.poller.should_poll("institutional"):
                try:
                    print(f"[UW-DAEMON] Polling institutional for {ticker}...", flush=True)
                    institutional_data = self.client.get_institutional(ticker)
                    # Always store institutional (even if empty or 404) so we know it was polled
                    if not institutional_data:
                        institutional_data = {}  # Store empty structure
                    self._update_cache(ticker, {"institutional": institutional_data})
                    if institutional_data:
                        print(f"[UW-DAEMON] Updated institutional for {ticker}: {len(str(institutional_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] institutional for {ticker}: API returned empty (stored as empty)", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching institutional for {ticker}: {e}", flush=True)
                    # Store empty on error too
                    self._update_cache(ticker, {"institutional": {}})
        
        except Exception as e:
            print(f"[UW-DAEMON] Error polling {ticker}: {e}", flush=True)
    
    def run(self):
        """Main daemon loop."""
        try:
            safe_print("[UW-DAEMON] run() method called")
            safe_print(f"[UW-DAEMON] self.running = {self.running}")
            
            # #region agent log
            try:
                debug_log("uw_flow_daemon.py:run", "Daemon starting", {
                    "ticker_count": len(self.tickers),
                    "has_api_key": bool(self.client.api_key),
                    "cache_file": str(CACHE_FILE)
                }, "H2")
            except Exception as debug_err:
                safe_print(f"[UW-DAEMON] Debug log failed (non-critical): {debug_err}")
            # #endregion
            
            safe_print("[UW-DAEMON] Starting UW Flow Daemon...")
            safe_print(f"[UW-DAEMON] Monitoring {len(self.tickers)} tickers")
            safe_print(f"[UW-DAEMON] Cache file: {CACHE_FILE}")
            
            # Force first poll of market-wide endpoints on startup
            first_poll = True
            cycle = 0
            
            safe_print("[UW-DAEMON] Step 1: Variables initialized")
            safe_print(f"[UW-DAEMON] Step 2: Running flag = {self.running}")
            
            # CRITICAL: Check running flag BEFORE any debug_log calls
            if not self.running:
                safe_print("[UW-DAEMON] ERROR: running=False before entering loop!")
                return
            
            safe_print("[UW-DAEMON] Step 3: Running check passed")
            
            # #region agent log
            try:
                debug_log("uw_flow_daemon.py:run", "Entering main loop", {"running": self.running, "cycle": cycle}, "H2")
            except Exception as debug_err:
                safe_print(f"[UW-DAEMON] Debug log failed (non-critical): {debug_err}")
            # #endregion
            
            safe_print("[UW-DAEMON] Step 4: About to enter while loop")
            safe_print(f"[UW-DAEMON] Step 5: Checking while condition: self.running = {self.running}")
            
            # CRITICAL: Force check running flag one more time right before loop
            if not self.running:
                safe_print("[UW-DAEMON] ERROR: running became False right before loop!")
                return
            
            safe_print("[UW-DAEMON] Step 5.5: Final check passed, entering while loop NOW")
            
            # Use a local variable to track if we should continue, to avoid signal handler race conditions
            should_continue = True
            
            # CRITICAL FIX: Enter loop FIRST, then set flag to prevent race condition
            # This ensures we're actually in the loop before accepting signals
            while should_continue and self.running:
                # Set loop entry flag on FIRST iteration only
                if not self._loop_entered:
                    self._loop_entered = True
                    safe_print("[UW-DAEMON] ✅ LOOP ENTERED - Loop entry flag set, signals will now be honored")
                
                safe_print(f"[UW-DAEMON] Step 6: INSIDE while loop! Cycle will be {cycle + 1}")
                try:
                    cycle += 1
                    if cycle == 1:
                        safe_print(f"[UW-DAEMON] ✅ SUCCESS: Entered main loop! Cycle {cycle}")
                    elif cycle <= 3:
                        safe_print(f"[UW-DAEMON] Loop continuing, cycle {cycle}")
                    
                    # Check running flag at start of each cycle
                    if not self.running:
                        safe_print(f"[UW-DAEMON] Running flag became False during cycle {cycle}")
                        should_continue = False
                        break
                    
                    # #region agent log
                    try:
                        debug_log("uw_flow_daemon.py:run", "Cycle start", {"cycle": cycle, "first_poll": first_poll, "running": self.running}, "H2")
                    except Exception as debug_err:
                        pass  # Non-critical
                    # #endregion
                    
                    # Check if we should exit
                    if not self.running:
                        # #region agent log
                        debug_log("uw_flow_daemon.py:run", "Exiting loop - running=False", {}, "H2")
                        # #endregion
                        break
                    
                    # Poll top net impact (market-wide, not per-ticker)
                    if self.poller.should_poll("top_net_impact", force_first=first_poll):
                        try:
                            safe_print(f"[UW-DAEMON] Polling top_net_impact (first_poll={first_poll})...")
                            top_net = self.client.get_top_net_impact(limit=100)
                            # Store in cache metadata
                            cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}
                            cache["_top_net_impact"] = {
                                "data": top_net,
                                "last_update": int(time.time())
                            }
                            atomic_write_json(CACHE_FILE, cache)
                        except Exception as e:
                            safe_print(f"[UW-DAEMON] Error polling top_net_impact: {e}")
                    
                    # Poll market tide (market-wide, not per-ticker)
                    if self.poller.should_poll("market_tide", force_first=first_poll):
                        try:
                            safe_print(f"[UW-DAEMON] Polling market_tide (first_poll={first_poll})...")
                            # #region agent log
                            debug_log("uw_flow_daemon.py:run:market_tide", "Calling get_market_tide", {"first_poll": first_poll}, "H3")
                            # #endregion
                            tide_data = self.client.get_market_tide()
                            # #region agent log
                            debug_log("uw_flow_daemon.py:run:market_tide", "get_market_tide response", {
                                "has_data": bool(tide_data),
                                "data_type": type(tide_data).__name__,
                                "data_keys": list(tide_data.keys()) if isinstance(tide_data, dict) else [],
                                "data_str": str(tide_data)[:200] if tide_data else "empty"
                            }, "H3")
                            # #endregion
                            if tide_data:
                                # Store in cache metadata AND per-ticker (for scoring)
                                cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}
                                cache["_market_tide"] = {
                                    "data": tide_data,
                                    "last_update": int(time.time())
                                }
                                # Also store per-ticker so scoring can access it
                                for ticker in self.tickers:
                                    if ticker not in cache:
                                        cache[ticker] = {}
                                    cache[ticker]["market_tide"] = tide_data
                                atomic_write_json(CACHE_FILE, cache)
                                safe_print(f"[UW-DAEMON] Updated market_tide: {len(str(tide_data))} bytes (stored globally and per-ticker)")
                            else:
                                safe_print(f"[UW-DAEMON] market_tide: API returned empty data")
                        except Exception as e:
                            safe_print(f"[UW-DAEMON] Error polling market_tide: {e}")
                            import traceback
                            safe_print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}")
                    
                    # Poll each ticker (optimized delay for rate limit efficiency)
                    for ticker in self.tickers:
                        if not self.running:
                            break
                        self._poll_ticker(ticker)
                        # 1.5s delay: balances speed with rate limit safety
                        # With 53 tickers: ~80 seconds per full cycle at 1.5s delay
                        time.sleep(1.5)
                    
                    # Clear first_poll flag after first cycle
                    if first_poll:
                        first_poll = False
                        safe_print("[UW-DAEMON] Completed first poll cycle - all endpoints attempted")
                    
                    # Log cycle completion
                    if cycle % 10 == 0:
                        safe_print(f"[UW-DAEMON] Completed {cycle} cycles")
                        # #region agent log
                        debug_log("uw_flow_daemon.py:run", "Cycle milestone", {"cycle": cycle}, "H2")
                        # #endregion
                    
                    # Sleep before next cycle
                    # If rate limited, sleep longer (check every 5 minutes for reset)
                    if self._rate_limited:
                        # Log status periodically so user knows system is still monitoring
                        if cycle % 12 == 0:  # Every 12 cycles = every hour when rate limited
                            safe_print(f"[UW-DAEMON] ⏳ Rate limited - monitoring for reset (8PM EST). Cache data preserved for graceful degradation.")
                        # #region agent log
                        debug_log("uw_flow_daemon.py:run", "Rate limited - sleeping", {}, "H2")
                        # #endregion
                        time.sleep(300)  # 5 minutes
                        # Check if it's past 8PM EST (limit reset time)
                        try:
                            import pytz
                            et = pytz.timezone('US/Eastern')
                            now_et = datetime.now(et)
                            if now_et.hour >= 20:  # 8PM or later
                                print(f"[UW-DAEMON] ✅ Limit should have reset, resuming polling...", flush=True)
                                self._rate_limited = False
                        except:
                            pass
                    else:
                        # #region agent log
                        debug_log("uw_flow_daemon.py:run", "Normal sleep", {"cycle": cycle}, "H2")
                        # #endregion
                        time.sleep(30)  # Normal: Check every 30 seconds
                
                except KeyboardInterrupt:
                    safe_print("[UW-DAEMON] Keyboard interrupt received")
                    # #region agent log
                    try:
                        debug_log("uw_flow_daemon.py:run", "Keyboard interrupt", {}, "H2")
                    except:
                        pass
                    # #endregion
                    should_continue = False
                    self.running = False
                    break
                except Exception as e:
                    # #region agent log
                    try:
                        debug_log("uw_flow_daemon.py:run", "Main loop exception", {
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "cycle": cycle,
                            "running": self.running
                        }, "H2")
                    except:
                        pass
                    # #endregion
                    safe_print(f"[UW-DAEMON] Error in main loop: {e}")
                    import traceback
                    tb = traceback.format_exc()
                    safe_print(f"[UW-DAEMON] Traceback: {tb}")
                    # #region agent log
                    try:
                        debug_log("uw_flow_daemon.py:run", "Exception traceback", {"traceback": tb}, "H2")
                    except:
                        pass
                    # #endregion
                    # Don't exit on error - continue loop unless explicitly stopped
                    if not self.running:
                        safe_print(f"[UW-DAEMON] Running flag False after exception, breaking loop")
                        should_continue = False
                        break
                    time.sleep(60)  # Wait longer on error
        
        except Exception as e:
            safe_print(f"[UW-DAEMON] FATAL ERROR in run() method: {e}")
            import traceback
            safe_print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}")
            # #region agent log
            try:
                debug_log("uw_flow_daemon.py:run", "Fatal exception", {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }, "H1")
            except:
                pass
            # #endregion
            raise
        
        safe_print("[UW-DAEMON] Shutting down...")
        # #region agent log
        try:
            debug_log("uw_flow_daemon.py:run", "Daemon shutdown complete", {"cycle": cycle}, "H2")
        except:
            pass
        # #endregion
        
        # Reset loop entry flag for potential restart
        self._loop_entered = False


def main():
    """Entry point."""
    safe_print("[UW-DAEMON] Main function called")
    # #region agent log
    try:
        debug_log("uw_flow_daemon.py:main", "Main function called", {
            "cwd": str(Path.cwd()),
            "script_path": str(Path(__file__)),
            "debug_log_path": str(DEBUG_LOG_PATH)
        }, "H1")
    except Exception as debug_err:
        safe_print(f"[UW-DAEMON] Debug log failed (non-critical): {debug_err}")
    # #endregion
    
    try:
        safe_print("[UW-DAEMON] Creating daemon object...")
        daemon = UWFlowDaemon()
        safe_print("[UW-DAEMON] Daemon object created successfully")
        safe_print(f"[UW-DAEMON] Daemon running flag: {daemon.running}")
        # #region agent log
        try:
            debug_log("uw_flow_daemon.py:main", "Daemon object created", {
                "ticker_count": len(daemon.tickers),
                "running": daemon.running
            }, "H1")
        except Exception as debug_err:
            safe_print(f"[UW-DAEMON] Debug log failed (non-critical): {debug_err}")
        # #endregion
        safe_print("[UW-DAEMON] Calling daemon.run()...")
        daemon.run()
        safe_print("[UW-DAEMON] daemon.run() returned")
    except Exception as e:
        # #region agent log
        debug_log("uw_flow_daemon.py:main", "Main exception", {
            "error": str(e),
            "error_type": type(e).__name__
        }, "H1")
        # #endregion
        import traceback
        print(f"[UW-DAEMON] Fatal error: {e}", flush=True)
        print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
        raise


if __name__ == "__main__":
    main()


