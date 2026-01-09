#!/usr/bin/env python3
"""
Signal-to-Trade Funnel Tracker
Tracks the complete funnel: UW Alerts -> Parsed Signals -> Scored > 2.7 -> Orders Sent
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from collections import deque

STATE_DIR = Path("state")
LOGS_DIR = Path("logs")
DATA_DIR = Path("data")

FUNNEL_WINDOW_SEC = 1800  # 30 minutes
STAGNATION_ALERT_THRESHOLD = 50  # >50 alerts but 0 trades = stagnation
STAGNATION_60MIN_WINDOW_SEC = 3600  # 60 minutes for adaptive scaling
STAGNATION_60MIN_ORDERS_THRESHOLD = 0  # 0 orders in 60 minutes = stagnation

class SignalFunnelTracker:
    """Tracks signal-to-trade funnel metrics"""
    
    def __init__(self):
        self.state_file = STATE_DIR / "signal_funnel_state.json"
        self.state = self._load_state()
        
        # Rolling windows (30 minutes)
        self.alerts_window = deque(maxlen=1000)
        self.parsed_window = deque(maxlen=1000)
        self.scored_window = deque(maxlen=1000)
        self.orders_window = deque(maxlen=1000)
        
    def _load_state(self) -> Dict[str, Any]:
        """Load funnel state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_reset_ts": time.time(),
            "total_alerts": 0,
            "total_parsed": 0,
            "total_scored": 0,
            "total_orders": 0
        }
    
    def _save_state(self):
        """Save funnel state to disk"""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def record_uw_alert(self, symbol: str, alert_type: str = "option_flow"):
        """Record an incoming UW alert"""
        now = time.time()
        self.alerts_window.append({
            "timestamp": now,
            "symbol": symbol,
            "type": alert_type
        })
        self.state["total_alerts"] = self.state.get("total_alerts", 0) + 1
        self._save_state()
    
    def record_parsed_signal(self, symbol: str, cluster_count: int = 1):
        """Record a parsed signal (cluster generated)"""
        now = time.time()
        for _ in range(cluster_count):
            self.parsed_window.append({
                "timestamp": now,
                "symbol": symbol
            })
        self.state["total_parsed"] = self.state.get("total_parsed", 0) + cluster_count
        self._save_state()
    
    def record_scored_signal(self, symbol: str, score: float):
        """Record a signal that scored > 2.7 (entry threshold)"""
        now = time.time()
        self.scored_window.append({
            "timestamp": now,
            "symbol": symbol,
            "score": score
        })
        self.state["total_scored"] = self.state.get("total_scored", 0) + 1
        self._save_state()
    
    def record_order_sent(self, symbol: str, order_id: str, score: float):
        """Record an order that was sent"""
        now = time.time()
        self.orders_window.append({
            "timestamp": now,
            "symbol": symbol,
            "order_id": order_id,
            "score": score
        })
        self.state["total_orders"] = self.state.get("total_orders", 0) + 1
        self._save_state()
    
    def get_funnel_metrics(self, window_sec: int = FUNNEL_WINDOW_SEC) -> Dict[str, Any]:
        """Get funnel metrics for the last window_sec seconds"""
        now = time.time()
        cutoff = now - window_sec
        
        alerts_30m = sum(1 for a in self.alerts_window if a["timestamp"] >= cutoff)
        parsed_30m = sum(1 for p in self.parsed_window if p["timestamp"] >= cutoff)
        scored_30m = sum(1 for s in self.scored_window if s["timestamp"] >= cutoff and s.get("score", 0) > 2.7)
        orders_30m = sum(1 for o in self.orders_window if o["timestamp"] >= cutoff)
        
        # Calculate conversion rates
        parsed_rate = (parsed_30m / alerts_30m * 100) if alerts_30m > 0 else 0.0
        scored_rate = (scored_30m / parsed_30m * 100) if parsed_30m > 0 else 0.0
        order_rate = (orders_30m / scored_30m * 100) if scored_30m > 0 else 0.0
        overall_rate = (orders_30m / alerts_30m * 100) if alerts_30m > 0 else 0.0
        
        return {
            "window_sec": window_sec,
            "alerts": alerts_30m,
            "parsed": parsed_30m,
            "scored_above_threshold": scored_30m,
            "orders_sent": orders_30m,
            "parsed_rate_pct": round(parsed_rate, 2),
            "scored_rate_pct": round(scored_rate, 2),
            "order_rate_pct": round(order_rate, 2),
            "overall_conversion_pct": round(overall_rate, 2),
            "timestamp": now
        }
    
    def check_stagnation(self, market_regime: str = "mixed") -> Optional[Dict[str, Any]]:
        """
        Check for logic stagnation: >50 alerts but 0 trades in 30min window during RISK_ON regimes.
        
        Returns:
            Dict with stagnation details if detected, None otherwise
        """
        # Only check during RISK_ON regimes (market_open, not market_closed)
        risk_on_regimes = ["market_open", "mixed", "low_vol_uptrend", "high_vol_neg_gamma"]
        if market_regime not in risk_on_regimes:
            return None
        
        metrics = self.get_funnel_metrics(FUNNEL_WINDOW_SEC)
        
        # Stagnation condition: >50 alerts but 0 orders in 30min
        if metrics["alerts"] >= STAGNATION_ALERT_THRESHOLD and metrics["orders_sent"] == 0:
            return {
                "detected": True,
                "reason": "funnel_stagnation",
                "alerts_30m": metrics["alerts"],
                "parsed_30m": metrics["parsed"],
                "scored_30m": metrics["scored_above_threshold"],
                "orders_30m": metrics["orders_sent"],
                "regime": market_regime,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return None
    
    def check_60min_stagnation_for_adaptive_scaling(self, market_regime: str = "mixed") -> Optional[Dict[str, Any]]:
        """
        ALPHA REPAIR: Stagnation-Triggered Adaptive Scaling
        
        If the Signal Funnel reports 0 orders for 60 minutes during active market hours,
        the bot must automatically lower the 'ATR Exhaustion Multiplier' from 2.5 to 3.0.
        This allows the bot to 'lean into' strong trends that don't pull back.
        
        Returns:
            Dict with 60min stagnation details if detected, None otherwise
        """
        # Only check during active market hours (RISK_ON regimes)
        risk_on_regimes = ["market_open", "mixed", "low_vol_uptrend", "high_vol_neg_gamma"]
        if market_regime not in risk_on_regimes:
            return None
        
        # Check 60-minute window
        metrics_60m = self.get_funnel_metrics(STAGNATION_60MIN_WINDOW_SEC)
        
        # Stagnation condition: 0 orders in 60 minutes during active market hours
        if metrics_60m["orders_sent"] == STAGNATION_60MIN_ORDERS_THRESHOLD:
            return {
                "detected": True,
                "reason": "60min_stagnation_adaptive_scaling",
                "alerts_60m": metrics_60m["alerts"],
                "parsed_60m": metrics_60m["parsed"],
                "scored_60m": metrics_60m["scored_above_threshold"],
                "orders_60m": metrics_60m["orders_sent"],
                "regime": market_regime,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action_required": "lower_atr_exhaustion_multiplier",
                "current_multiplier": 2.5,
                "target_multiplier": 3.0
            }
        
        return None
    
    def get_total_counts(self) -> Dict[str, int]:
        """Get total lifetime counts"""
        return {
            "total_alerts": self.state.get("total_alerts", 0),
            "total_parsed": self.state.get("total_parsed", 0),
            "total_scored": self.state.get("total_scored", 0),
            "total_orders": self.state.get("total_orders", 0)
        }

# Global singleton
_funnel_tracker = None

def get_funnel_tracker() -> SignalFunnelTracker:
    """Get singleton funnel tracker instance"""
    global _funnel_tracker
    if _funnel_tracker is None:
        _funnel_tracker = SignalFunnelTracker()
    return _funnel_tracker
