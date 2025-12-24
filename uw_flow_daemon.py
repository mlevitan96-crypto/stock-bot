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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.registry import CacheFiles, Directories, StateFiles, read_json, atomic_write_json, append_jsonl

load_dotenv()

DATA_DIR = Directories.DATA
CACHE_FILE = CacheFiles.UW_FLOW_CACHE

class UWClient:
    """Unusual Whales API client."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("UW_API_KEY")
        self.base = "https://api.unusualwhales.com"
        self.headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
    
    def _get(self, path_or_url: str, params: dict = None) -> dict:
        """Make API request with quota tracking."""
        url = path_or_url if path_or_url.startswith("http") else f"{self.base}{path_or_url}"
        
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
                    print(f"[UW-DAEMON] ⚠️  Rate limit warning: {count}/{limit} ({pct:.1f}%)", flush=True)
                elif pct > 90:
                    print(f"[UW-DAEMON] 🚨 Rate limit critical: {count}/{limit} ({pct:.1f}%)", flush=True)
            
            # Check for 429 (rate limited)
            if r.status_code == 429:
                error_data = r.json() if r.content else {}
                print(f"[UW-DAEMON] ❌ RATE LIMITED (429): {error_data.get('message', 'Daily limit hit')}", flush=True)
                print(f"[UW-DAEMON] ⚠️  Stopping polling until limit resets (8PM EST)", flush=True)
                append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {
                    "event": "UW_API_RATE_LIMITED",
                    "url": url,
                    "status": 429,
                    "daily_count": daily_count,
                    "daily_limit": daily_limit,
                    "message": error_data.get("message", ""),
                    "ts": int(time.time())
                })
                # Set a flag to stop polling for a while
                # The daemon will continue running but won't make API calls
                return {"data": [], "_rate_limited": True}
            
            # Log non-200 responses for debugging
            if r.status_code != 200:
                print(f"[UW-DAEMON] ⚠️  API returned status {r.status_code} for {url}", flush=True)
                try:
                    error_text = r.text[:200] if r.text else "No response body"
                    print(f"[UW-DAEMON] Response: {error_text}", flush=True)
                except:
                    pass
            
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {
                "event": "UW_API_ERROR",
                "url": url,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None),
                "ts": int(time.time())
            })
            return {"data": []}
        except Exception as e:
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
            print(f"[UW-DAEMON] Retrieved {len(data)} flow trades for {ticker}", flush=True)
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
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
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
        
        # If this is the first poll (no last call recorded), allow it immediately
        if force_first and last == 0:
            self.last_call[endpoint] = now
            self._save_state()
            return True
        
        # OPTIMIZATION: During market hours, use normal intervals
        # Outside market hours, use longer intervals to conserve quota
        if self._is_market_hours():
            interval = base_interval
        else:
            # Outside market hours: poll 3x less frequently (conserve quota)
            interval = base_interval * 3
        
        if now - last < interval:
            return False
        
        # Update timestamp
        self.last_call[endpoint] = now
        self._save_state()
        return True
    
    def _is_market_hours(self) -> bool:
        """Check if currently in trading hours (9:30 AM - 4:00 PM ET)."""
        try:
            import pytz
            et = pytz.timezone('US/Eastern')
            now_et = datetime.now(et)
            hour_min = now_et.hour * 60 + now_et.minute
            market_open = 9 * 60 + 30  # 9:30 AM
            market_close = 16 * 60      # 4:00 PM
            return market_open <= hour_min < market_close
        except:
            return True  # Default to allowing polls if timezone check fails


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
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n[UW-DAEMON] Received signal {signum}, shutting down...", flush=True)
        self.running = False
    
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
        if net_premium > 100000:
            sentiment = "BULLISH"
            conviction = min(1.0, net_premium / 5_000_000)
        elif net_premium < -100000:
            sentiment = "BEARISH"
            conviction = min(1.0, abs(net_premium) / 5_000_000)
        else:
            sentiment = "NEUTRAL"
            conviction = 0.0
        
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
        """Normalize dark pool data."""
        if not dp_data:
            return {}
        
        total_premium = sum(float(d.get("premium", 0) or 0) for d in dp_data)
        print_count = len(dp_data)
        
        # Sentiment based on premium
        if total_premium > 1000000:
            sentiment = "BULLISH"
        elif total_premium < -1000000:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        return {
            "sentiment": sentiment,
            "total_premium": total_premium,
            "print_count": print_count,
            "last_update": int(time.time())
        }
    
    def _update_cache(self, ticker: str, data: Dict):
        """Update cache for a ticker."""
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
            
            # Poll option flow
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
                    cache_update.update({
                        "sentiment": "NEUTRAL",
                        "conviction": 0.0,
                        "trade_count": len(flow_data) if flow_data else 0
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
                if dp_normalized:
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
                    if oi_data:
                        self._update_cache(ticker, {"oi_change": oi_data})
                        print(f"[UW-DAEMON] Updated oi_change for {ticker}: {len(str(oi_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] oi_change for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching oi_change for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
            
            # Poll ETF flow
            if self.poller.should_poll("etf_flow"):
                try:
                    print(f"[UW-DAEMON] Polling etf_flow for {ticker}...", flush=True)
                    etf_data = self.client.get_etf_flow(ticker)
                    if etf_data:
                        self._update_cache(ticker, {"etf_flow": etf_data})
                        print(f"[UW-DAEMON] Updated etf_flow for {ticker}: {len(str(etf_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] etf_flow for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching etf_flow for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
            
            # Poll IV rank
            if self.poller.should_poll("iv_rank"):
                try:
                    print(f"[UW-DAEMON] Polling iv_rank for {ticker}...", flush=True)
                    iv_data = self.client.get_iv_rank(ticker)
                    if iv_data:
                        self._update_cache(ticker, {"iv_rank": iv_data})
                        print(f"[UW-DAEMON] Updated iv_rank for {ticker}: {len(str(iv_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] iv_rank for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching iv_rank for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
            
            # Poll shorts/FTDs
            if self.poller.should_poll("shorts_ftds"):
                try:
                    print(f"[UW-DAEMON] Polling shorts_ftds for {ticker}...", flush=True)
                    ftd_data = self.client.get_shorts_ftds(ticker)
                    if ftd_data:
                        self._update_cache(ticker, {"ftd_pressure": ftd_data})
                        print(f"[UW-DAEMON] Updated ftd_pressure for {ticker}: {len(str(ftd_data))} bytes", flush=True)
                    else:
                        print(f"[UW-DAEMON] shorts_ftds for {ticker}: API returned empty", flush=True)
                except Exception as e:
                    print(f"[UW-DAEMON] Error fetching shorts_ftds for {ticker}: {e}", flush=True)
                    import traceback
                    print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
            
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
        
        except Exception as e:
            print(f"[UW-DAEMON] Error polling {ticker}: {e}", flush=True)
    
    def run(self):
        """Main daemon loop."""
        print("[UW-DAEMON] Starting UW Flow Daemon...", flush=True)
        print(f"[UW-DAEMON] Monitoring {len(self.tickers)} tickers", flush=True)
        print(f"[UW-DAEMON] Cache file: {CACHE_FILE}", flush=True)
        
        # Force first poll of market-wide endpoints on startup
        first_poll = True
        
        cycle = 0
        while self.running:
            try:
                cycle += 1
                
                # Poll top net impact (market-wide, not per-ticker)
                if self.poller.should_poll("top_net_impact", force_first=first_poll):
                    try:
                        top_net = self.client.get_top_net_impact(limit=100)
                        # Store in cache metadata
                        cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}
                        cache["_top_net_impact"] = {
                            "data": top_net,
                            "last_update": int(time.time())
                        }
                        atomic_write_json(CACHE_FILE, cache)
                    except Exception as e:
                        print(f"[UW-DAEMON] Error polling top_net_impact: {e}", flush=True)
                
                # Poll market tide (market-wide, not per-ticker)
                if self.poller.should_poll("market_tide", force_first=first_poll):
                    try:
                        print(f"[UW-DAEMON] Polling market_tide...", flush=True)
                        tide_data = self.client.get_market_tide()
                        if tide_data:
                            # Store in cache metadata
                            cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}
                            cache["_market_tide"] = {
                                "data": tide_data,
                                "last_update": int(time.time())
                            }
                            atomic_write_json(CACHE_FILE, cache)
                            print(f"[UW-DAEMON] Updated market_tide: {len(str(tide_data))} bytes", flush=True)
                        else:
                            print(f"[UW-DAEMON] market_tide: API returned empty data", flush=True)
                    except Exception as e:
                        print(f"[UW-DAEMON] Error polling market_tide: {e}", flush=True)
                        import traceback
                        print(f"[UW-DAEMON] Traceback: {traceback.format_exc()}", flush=True)
                
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
                    print("[UW-DAEMON] Completed first poll cycle - all endpoints attempted", flush=True)
                
                # Log cycle completion
                if cycle % 10 == 0:
                    print(f"[UW-DAEMON] Completed {cycle} cycles", flush=True)
                
                # Sleep before next cycle
                # If rate limited, sleep longer (check every 5 minutes for reset)
                if self._rate_limited:
                    # Log status periodically so user knows system is still monitoring
                    if cycle % 12 == 0:  # Every 12 cycles = every hour when rate limited
                        print(f"[UW-DAEMON] ⏳ Rate limited - monitoring for reset (8PM EST). Cache data preserved for graceful degradation.", flush=True)
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
                    time.sleep(30)  # Normal: Check every 30 seconds
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[UW-DAEMON] Error in main loop: {e}", flush=True)
                time.sleep(60)  # Wait longer on error
        
        print("[UW-DAEMON] Shutting down...", flush=True)


def main():
    """Entry point."""
    daemon = UWFlowDaemon()
    daemon.run()


if __name__ == "__main__":
    main()


