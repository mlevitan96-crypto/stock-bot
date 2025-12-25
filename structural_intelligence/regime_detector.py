#!/usr/bin/env python3
"""
Structural Intelligence Gate: HMM-Based Regime Detector
Uses Hidden Markov Model (HMM) on SPY returns to detect market regimes.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple
import requests
import alpaca_trade_api as tradeapi

# Optional imports with graceful fallback
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("WARNING: numpy not installed. Regime detection will use fallback method.")

try:
    from hmmlearn import hmm
    HAS_HMMLEARN = True
except ImportError:
    HAS_HMMLEARN = False
    print("WARNING: hmmlearn not installed. Regime detection will use fallback method.")

STATE_DIR = Path("state")
REGIME_STATE_FILE = STATE_DIR / "regime_detector_state.json"

# Regime states
REGIME_STATES = {
    0: "RISK_ON",      # Bull market, low vol
    1: "NEUTRAL",      # Normal market
    2: "RISK_OFF",     # Bear market, high vol
    3: "PANIC"         # Extreme volatility, crash risk
}

class RegimeDetector:
    """HMM-based regime detector using SPY returns."""
    
    def __init__(self):
        self.model = None
        self.current_regime = "NEUTRAL"
        self.regime_confidence = 0.0
        self.last_update = None
        self.state_file = REGIME_STATE_FILE
        self._load_state()
        
    def _load_state(self):
        """Load saved regime state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.current_regime = state.get("current_regime", "NEUTRAL")
                    self.regime_confidence = state.get("confidence", 0.0)
                    self.last_update = state.get("last_update")
            except:
                pass
    
    def _save_state(self):
        """Save current regime state"""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                "current_regime": self.current_regime,
                "confidence": self.regime_confidence,
                "last_update": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)
    
    def _fetch_spy_returns(self, days: int = 60):
        """Fetch SPY returns for HMM training"""
        try:
            key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY", "")
            secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET", "")
            base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
            
            if not key or not secret:
                return None
            
            api = tradeapi.REST(key, secret, base_url)
            
            # Fetch daily bars
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            bars = api.get_bars(
                "SPY",
                "1Day",
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                limit=1000
            ).df
            
            if bars.empty:
                return None
            
            # Calculate returns
            if HAS_NUMPY:
                returns = bars['close'].pct_change().dropna().values
                # Reshape for HMM (needs 2D array)
                return returns.reshape(-1, 1)
            else:
                # Fallback: return as list
                prices = bars['close'].tolist()
                returns = []
                for i in range(1, len(prices)):
                    if prices[i-1] > 0:
                        ret = (prices[i] - prices[i-1]) / prices[i-1]
                        returns.append([ret])
                return returns if returns else None
            
        except Exception as e:
            print(f"Error fetching SPY returns: {e}")
            return None
    
    def _train_hmm(self, returns) -> Optional:
        """Train HMM model on returns"""
        if not HAS_HMMLEARN:
            return None
        
        try:
            # Use 4 states for 4 regimes
            model = hmm.GaussianHMM(n_components=4, covariance_type="full", n_iter=100)
            model.fit(returns)
            return model
        except Exception as e:
            print(f"Error training HMM: {e}")
            return None
    
    def _detect_regime_fallback(self, returns) -> Tuple[str, float]:
        """Fallback regime detection using simple statistics"""
        if len(returns) == 0:
            return "NEUTRAL", 0.5
        
        # Handle both numpy arrays and lists
        if HAS_NUMPY and hasattr(returns, 'flatten'):
            returns_flat = returns.flatten()
            mean_return = float(np.mean(returns_flat))
            std_return = float(np.std(returns_flat))
        else:
            # Fallback: calculate manually
            returns_list = [r[0] if isinstance(r, list) else r for r in returns]
            if not returns_list:
                return "NEUTRAL", 0.5
            mean_return = sum(returns_list) / len(returns_list)
            variance = sum((x - mean_return) ** 2 for x in returns_list) / len(returns_list)
            std_return = variance ** 0.5
        
        # Simple regime classification
        if std_return > 0.03:  # High volatility
            if mean_return < -0.01:  # Negative returns
                return "PANIC", 0.7
            else:
                return "RISK_OFF", 0.6
        elif mean_return > 0.005:  # Positive returns, low vol
            return "RISK_ON", 0.6
        else:
            return "NEUTRAL", 0.5
    
    def detect_regime(self) -> Tuple[str, float]:
        """
        Detect current market regime using HMM.
        Returns: (regime_name, confidence)
        """
        # Check if we need to update (every hour)
        if self.last_update:
            last_ts = datetime.fromisoformat(self.last_update.replace('Z', '+00:00'))
            if (datetime.now(timezone.utc) - last_ts).total_seconds() < 3600:
                return self.current_regime, self.regime_confidence
        
        # Fetch SPY returns
        returns = self._fetch_spy_returns(days=60)
        if returns is None or len(returns) < 30:
            # Not enough data, return current regime
            return self.current_regime, self.regime_confidence
        
        # Try HMM detection
        if HAS_HMMLEARN:
            model = self._train_hmm(returns)
            if model:
                try:
                    # Predict regime from most recent returns
                    recent_returns = returns[-10:].reshape(-1, 1)
                    states = model.predict(recent_returns)
                    current_state = states[-1]
                    
                    # Calculate confidence (state probability)
                    if HAS_NUMPY:
                        probs = model.predict_proba(recent_returns)
                        confidence = float(np.max(probs[-1]))
                    else:
                        confidence = 0.6  # Default confidence
                    
                    regime = REGIME_STATES.get(current_state, "NEUTRAL")
                    
                    self.current_regime = regime
                    self.regime_confidence = confidence
                    self.last_update = datetime.now(timezone.utc).isoformat()
                    self._save_state()
                    
                    return regime, confidence
                except Exception as e:
                    print(f"Error in HMM prediction: {e}")
        
        # Fallback to simple detection
        regime, confidence = self._detect_regime_fallback(returns)
        self.current_regime = regime
        self.regime_confidence = confidence
        self.last_update = datetime.now(timezone.utc).isoformat()
        self._save_state()
        
        return regime, confidence
    
    def get_regime_multiplier(self, signal_direction: str = "bullish") -> float:
        """
        Get composite score multiplier based on regime.
        Penalizes bullish tech in High-Yield/Panic states.
        """
        regime = self.current_regime
        
        if regime == "RISK_ON":
            # Bull market - favor bullish
            return 1.2 if signal_direction == "bullish" else 0.9
        elif regime == "NEUTRAL":
            # Neutral - no adjustment
            return 1.0
        elif regime == "RISK_OFF":
            # Bear market - favor bearish
            return 0.8 if signal_direction == "bullish" else 1.1
        elif regime == "PANIC":
            # Panic - heavily penalize bullish
            return 0.5 if signal_direction == "bullish" else 1.2
        else:
            return 1.0

# Global instance
_regime_detector = None

def get_regime_detector() -> RegimeDetector:
    """Get global regime detector instance"""
    global _regime_detector
    if _regime_detector is None:
        _regime_detector = RegimeDetector()
    return _regime_detector

def get_current_regime() -> Tuple[str, float]:
    """Get current market regime"""
    detector = get_regime_detector()
    return detector.detect_regime()

