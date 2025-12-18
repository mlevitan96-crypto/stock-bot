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

from config.registry import CacheFiles, Directories, read_json, atomic_write_json, append_jsonl

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
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            append_jsonl(CacheFiles.UW_FLOW_CACHE_LOG, {
                "event": "UW_API_ERROR",
                "url": url,
                "error": str(e),
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
        return raw.get("data", [])
    
    def get_dark_pool_levels(self, ticker: str) -> List[Dict]:
        """Get dark pool levels for a ticker."""
        raw = self._get(f"/api/darkpool/{ticker}")
        return raw.get("data", [])
    
    def get_greek_exposure(self, ticker: str) -> Dict:
        """Get Greek exposure for a ticker."""
        raw = self._get(f"/api/stock/{ticker}/greeks")
        data = raw.get("data", {})
        if isinstance(data, list) and len(data) > 0:
            data = data[0]
        return data if isinstance(data, dict) else {}
    
    def get_top_net_impact(self, limit: int = 50) -> List[Dict]:
        """Get top net impact symbols."""
        raw = self._get("/api/market/top-net-impact", params={"limit": limit})
        return raw.get("data", [])


class SmartPoller:
    """Intelligent polling manager to optimize API usage."""
    
    def __init__(self):
        self.state_file = Path("state/smart_poller.json")
        self.intervals = {
            "option_flow": 60,        # 1 min: Real-time institutional trades
            "top_net_impact": 300,    # 5 min: Aggregated net premium
            "greek_exposure": 900,    # 15 min: Gamma exposure
            "dark_pool_levels": 120,  # 2 min: Block trades
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
    
    def should_poll(self, endpoint: str) -> bool:
        """Check if enough time has passed since last call."""
        now = time.time()
        last = self.last_call.get(endpoint, 0)
        interval = self.intervals.get(endpoint, 60)
        
        if now - last < interval:
            return False
        
        # Update timestamp
        self.last_call[endpoint] = now
        self._save_state()
        return True


class UWFlowDaemon:
    """Daemon that polls UW API and populates cache."""
    
    def __init__(self):
        self.client = UWClient()
        self.poller = SmartPoller()
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
    
    def _normalize_flow_data(self, flow_data: List[Dict], ticker: str) -> Dict:
        """Normalize flow data into cache format."""
        if not flow_data:
            return {}
        
        # Calculate sentiment and conviction from flow
        total_premium = sum(float(t.get("premium", 0) or 0) for t in flow_data)
        call_premium = sum(float(t.get("premium", 0) or 0) for t in flow_data 
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
            # Poll option flow
            if self.poller.should_poll("option_flow"):
                flow_data = self.client.get_option_flow(ticker, limit=100)
                flow_normalized = self._normalize_flow_data(flow_data, ticker)
                if flow_normalized:
                    # CRITICAL: Store both aggregated summary AND raw trades
                    # main.py needs raw trades for clustering, not just sentiment
                    # Write at top level (not nested in "flow") to match main.py expectations
                    # main.py expects: cache[ticker]["sentiment"] and cache[ticker]["conviction"]
                    self._update_cache(ticker, {
                        "sentiment": flow_normalized.get("sentiment", "NEUTRAL"),
                        "conviction": flow_normalized.get("conviction", 0.0),
                        "total_premium": flow_normalized.get("total_premium", 0.0),
                        "call_premium": flow_normalized.get("call_premium", 0.0),
                        "put_premium": flow_normalized.get("put_premium", 0.0),
                        "net_premium": flow_normalized.get("net_premium", 0.0),
                        "trade_count": flow_normalized.get("trade_count", 0),
                        "flow": flow_normalized,  # Also keep nested for compatibility
                        "flow_trades": flow_data  # CRITICAL: Store raw trades for clustering
                    })
            
            # Poll dark pool
            if self.poller.should_poll("dark_pool_levels"):
                dp_data = self.client.get_dark_pool_levels(ticker)
                dp_normalized = self._normalize_dark_pool(dp_data)
                if dp_normalized:
                    # Write dark_pool data (nested is fine - main.py reads it as cache_data.get("dark_pool", {}))
                    self._update_cache(ticker, {"dark_pool": dp_normalized})
            
            # Poll greeks (less frequently)
            if self.poller.should_poll("greek_exposure"):
                gex_data = self.client.get_greek_exposure(ticker)
                if gex_data:
                    self._update_cache(ticker, {"greeks": gex_data})
        
        except Exception as e:
            print(f"[UW-DAEMON] Error polling {ticker}: {e}", flush=True)
    
    def run(self):
        """Main daemon loop."""
        print("[UW-DAEMON] Starting UW Flow Daemon...", flush=True)
        print(f"[UW-DAEMON] Monitoring {len(self.tickers)} tickers", flush=True)
        print(f"[UW-DAEMON] Cache file: {CACHE_FILE}", flush=True)
        
        cycle = 0
        while self.running:
            try:
                cycle += 1
                
                # Poll top net impact (market-wide, not per-ticker)
                if self.poller.should_poll("top_net_impact"):
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
                
                # Poll each ticker
                for ticker in self.tickers:
                    if not self.running:
                        break
                    self._poll_ticker(ticker)
                    time.sleep(0.5)  # Small delay between tickers to avoid rate limits
                
                # Log cycle completion
                if cycle % 10 == 0:
                    print(f"[UW-DAEMON] Completed {cycle} cycles", flush=True)
                
                # Sleep before next cycle
                time.sleep(30)  # Check every 30 seconds
            
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
