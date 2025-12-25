#!/usr/bin/env python3
"""
Structural Intelligence Gate: FRED API MacroGate
Tracks Treasury Yields ($TNX) and adjusts composite scores based on macro conditions.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple

STATE_DIR = Path("state")
MACRO_STATE_FILE = STATE_DIR / "macro_gate_state.json"

# FRED API endpoint
FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"

class MacroGate:
    """FRED API-based macro gate using Treasury Yields."""
    
    def __init__(self):
        self.fred_api_key = os.getenv("FRED_API_KEY", "")
        self.current_yield = None
        self.yield_trend = "NEUTRAL"  # RISING, FALLING, NEUTRAL
        self.last_update = None
        self.state_file = MACRO_STATE_FILE
        self._load_state()
    
    def _load_state(self):
        """Load saved macro state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.current_yield = state.get("current_yield")
                    self.yield_trend = state.get("yield_trend", "NEUTRAL")
                    self.last_update = state.get("last_update")
            except:
                pass
    
    def _save_state(self):
        """Save current macro state"""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                "current_yield": self.current_yield,
                "yield_trend": self.yield_trend,
                "last_update": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)
    
    def _fetch_treasury_yield(self) -> Optional[float]:
        """Fetch 10-Year Treasury Yield ($TNX) from FRED API"""
        if not self.fred_api_key:
            # Try to use free alternative or fallback
            return self._fetch_yield_fallback()
        
        try:
            # FRED API: 10-Year Treasury Constant Maturity Rate (DGS10)
            url = FRED_API_BASE
            params = {
                "series_id": "DGS10",
                "api_key": self.fred_api_key,
                "file_type": "json",
                "limit": 1,
                "sort_order": "desc"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get("observations", [])
            
            if observations:
                latest = observations[0]
                value_str = latest.get("value", "")
                if value_str and value_str != ".":
                    return float(value_str)
            
            return None
            
        except Exception as e:
            print(f"Error fetching FRED data: {e}")
            return self._fetch_yield_fallback()
    
    def _fetch_yield_fallback(self) -> Optional[float]:
        """Fallback: Use market data API or cached value"""
        # Try to get from market data API or use cached
        if self.current_yield:
            return self.current_yield
        
        # Default fallback
        return 4.5  # Typical 10-year yield
    
    def update_macro_data(self) -> bool:
        """Update macro data from FRED API"""
        # Check if we need to update (every 4 hours)
        if self.last_update:
            try:
                last_ts = datetime.fromisoformat(self.last_update.replace('Z', '+00:00'))
                if (datetime.now(timezone.utc) - last_ts).total_seconds() < 14400:  # 4 hours
                    return True
            except:
                pass
        
        new_yield = self._fetch_treasury_yield()
        if new_yield is None:
            return False
        
        # Determine trend
        if self.current_yield is not None:
            if new_yield > self.current_yield * 1.02:  # 2% increase
                self.yield_trend = "RISING"
            elif new_yield < self.current_yield * 0.98:  # 2% decrease
                self.yield_trend = "FALLING"
            else:
                self.yield_trend = "NEUTRAL"
        
        self.current_yield = new_yield
        self.last_update = datetime.now(timezone.utc).isoformat()
        self._save_state()
        
        return True
    
    def get_macro_multiplier(self, signal_direction: str = "bullish", sector: str = "Technology") -> float:
        """
        Get composite score multiplier based on macro conditions.
        High yields + rising trend = penalize growth/tech stocks.
        """
        if self.current_yield is None:
            self.update_macro_data()
        
        if self.current_yield is None:
            return 1.0
        
        multiplier = 1.0
        
        # High yield (>5%) penalizes growth stocks
        if self.current_yield > 5.0:
            if sector in ("Technology", "Consumer Discretionary"):
                multiplier *= 0.8
            if signal_direction == "bullish":
                multiplier *= 0.9
        
        # Rising yields penalize growth more
        if self.yield_trend == "RISING":
            if sector in ("Technology", "Consumer Discretionary"):
                multiplier *= 0.85
            if signal_direction == "bullish":
                multiplier *= 0.9
        
        # Low yields (<3%) favor growth
        if self.current_yield < 3.0:
            if sector in ("Technology", "Consumer Discretionary"):
                multiplier *= 1.1
            if signal_direction == "bullish":
                multiplier *= 1.05
        
        return multiplier
    
    def get_macro_status(self) -> Dict:
        """Get current macro status"""
        return {
            "current_yield": self.current_yield,
            "yield_trend": self.yield_trend,
            "last_update": self.last_update
        }

# Global instance
_macro_gate = None

def get_macro_gate() -> MacroGate:
    """Get global macro gate instance"""
    global _macro_gate
    if _macro_gate is None:
        _macro_gate = MacroGate()
    return _macro_gate

