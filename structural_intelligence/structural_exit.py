#!/usr/bin/env python3
"""
Physics-Based Exit Manager
Scales out positions when reaching UW Gamma "Call Walls" and triggers early exits on bid-side liquidity exhaustion.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple, List
import requests
import os

STATE_DIR = Path("state")
EXIT_STATE_FILE = STATE_DIR / "structural_exit_state.json"

class StructuralExit:
    """Physics-based exit manager using gamma call walls and liquidity analysis."""
    
    def __init__(self):
        self.uw_api_key = os.getenv("UW_API_KEY", "")
        self.uw_base_url = os.getenv("UW_API_BASE", "https://api.unusualwhales.com")
        self.state_file = EXIT_STATE_FILE
        self._load_state()
    
    def _load_state(self):
        """Load saved exit state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            except:
                self.state = {}
        else:
            self.state = {}
    
    def _save_state(self):
        """Save exit state"""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _fetch_gamma_levels(self, symbol: str) -> Optional[Dict]:
        """Fetch gamma levels (call walls) from UW API"""
        if not self.uw_api_key:
            return None
        
        try:
            url = f"{self.uw_base_url}/api/stock/{symbol}/gamma-levels"
            headers = {"Authorization": f"Bearer {self.uw_api_key}"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {})
            
            return None
        except Exception as e:
            print(f"Error fetching gamma levels for {symbol}: {e}")
            return None
    
    def _check_call_wall(self, symbol: str, current_price: float, position_side: str) -> Tuple[bool, float]:
        """
        Check if position is near a gamma call wall.
        Returns: (should_scale_out, scale_out_pct)
        """
        if position_side != "buy":  # Only for long positions
            return False, 0.0
        
        gamma_data = self._fetch_gamma_levels(symbol)
        if not gamma_data:
            return False, 0.0
        
        # Get call wall levels (strikes with high gamma exposure)
        call_walls = gamma_data.get("call_walls", [])
        if not call_walls:
            return False, 0.0
        
        # Find nearest call wall above current price
        nearest_wall = None
        min_distance = float('inf')
        
        for wall in call_walls:
            wall_price = float(wall.get("strike", 0))
            if wall_price > current_price:
                distance = wall_price - current_price
                if distance < min_distance:
                    min_distance = distance
                    nearest_wall = wall
        
        if nearest_wall is None:
            return False, 0.0
        
        wall_price = float(nearest_wall.get("strike", 0))
        wall_gamma = float(nearest_wall.get("gamma_exposure", 0))
        distance_pct = (wall_price - current_price) / current_price
        
        # Scale out if within 2% of call wall with high gamma
        if distance_pct < 0.02 and wall_gamma > 1000000:  # $1M+ gamma exposure
            # Scale out 50% when near call wall
            return True, 0.5
        
        # Scale out 25% if within 5% of call wall
        if distance_pct < 0.05 and wall_gamma > 500000:  # $500k+ gamma exposure
            return True, 0.25
        
        return False, 0.0
    
    def _check_liquidity_exhaustion(self, symbol: str, position_side: str) -> bool:
        """
        Check for bid-side liquidity exhaustion.
        Returns: True if should exit early
        """
        try:
            # Fetch order book data from UW or Alpaca
            # For now, use a simple heuristic based on recent volume
            
            # This would ideally use real-time order book data
            # For now, return False (would need real-time data feed)
            return False
            
        except Exception as e:
            print(f"Error checking liquidity for {symbol}: {e}")
            return False
    
    def should_exit_early(self, symbol: str, current_price: float, position_side: str, 
                          entry_price: float, unrealized_pnl_pct: float) -> Tuple[bool, str, float]:
        """
        Determine if position should exit early based on structural factors.
        Returns: (should_exit, reason, scale_out_pct)
        """
        # Check call wall
        near_wall, scale_pct = self._check_call_wall(symbol, current_price, position_side)
        if near_wall:
            return True, "gamma_call_wall", scale_pct
        
        # Check liquidity exhaustion
        if self._check_liquidity_exhaustion(symbol, position_side):
            return True, "liquidity_exhaustion", 1.0  # Full exit
        
        # Check if profit target reached and near call wall (take profit at wall)
        if unrealized_pnl_pct > 0.05:  # 5% profit
            near_wall, _ = self._check_call_wall(symbol, current_price, position_side)
            if near_wall:
                return True, "profit_at_call_wall", 1.0  # Full exit at wall
        
        return False, "", 0.0
    
    def get_exit_recommendation(self, symbol: str, position_data: Dict) -> Dict:
        """
        Get exit recommendation for a position.
        position_data should contain: current_price, side, entry_price, unrealized_pnl_pct
        """
        current_price = position_data.get("current_price", 0.0)
        side = position_data.get("side", "buy")
        entry_price = position_data.get("entry_price", 0.0)
        unrealized_pnl_pct = position_data.get("unrealized_pnl_pct", 0.0)
        
        should_exit, reason, scale_pct = self.should_exit_early(
            symbol, current_price, side, entry_price, unrealized_pnl_pct
        )
        
        return {
            "should_exit": should_exit,
            "reason": reason,
            "scale_out_pct": scale_pct,
            "recommended_action": "EXIT" if should_exit else "HOLD"
        }

# Global instance
_structural_exit = None

def get_structural_exit() -> StructuralExit:
    """Get global structural exit instance"""
    global _structural_exit
    if _structural_exit is None:
        _structural_exit = StructuralExit()
    return _structural_exit

