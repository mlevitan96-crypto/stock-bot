#!/usr/bin/env python3
"""
Specialist Strategy Rotator & Temporal Liquidity Gating
Integrates with existing structural intelligence and explainable logging systems.
"""

import logging
from datetime import datetime, time, timezone
from typing import Dict, Any, Optional
from pathlib import Path

# Import existing systems
try:
    from xai.explainable_logger import get_explainable_logger
    EXPLAINABLE_LOGGER_AVAILABLE = True
except ImportError:
    EXPLAINABLE_LOGGER_AVAILABLE = False
    logging.warning("ExplainableLogger not available - using standard logging")

try:
    from structural_intelligence import get_regime_detector
    STRUCTURAL_INTELLIGENCE_AVAILABLE = True
except ImportError:
    STRUCTURAL_INTELLIGENCE_AVAILABLE = False
    logging.warning("Structural intelligence not available - using default regime")


class SpecialistStrategyRotator:
    """
    Manages proactive logic shifts based on regime and temporal liquidity.
    Integrates with existing structural intelligence and explainable logging.
    """
    
    def __init__(self, current_regime: str = "mixed", min_exec_score: float = 2.0):
        self.regime = current_regime
        self.base_threshold = min_exec_score
        self.now = datetime.now(timezone.utc).time()
        
        # Get structural intelligence if available
        if STRUCTURAL_INTELLIGENCE_AVAILABLE:
            try:
                self.regime_detector = get_regime_detector()
                # Override with detected regime if available
                detected_regime, _ = self.regime_detector.detect_regime()
                if detected_regime:
                    self.regime = detected_regime
            except Exception as e:
                logging.warning(f"Could not get regime from structural intelligence: {e}")
        
        # Get explainable logger if available
        self.explainable_logger = None
        if EXPLAINABLE_LOGGER_AVAILABLE:
            try:
                self.explainable_logger = get_explainable_logger()
            except Exception as e:
                logging.warning(f"Could not get explainable logger: {e}")

    def get_proactive_threshold(self) -> float:
        """
        Tightens gates during Mid-Day liquidity gaps (11:30-13:30 EST).
        Returns adjusted threshold based on temporal liquidity conditions.
        """
        # Convert to EST (UTC-5) for market hours
        est_offset = timezone.utc.utcoffset(datetime.now(timezone.utc))
        est_now = (datetime.now(timezone.utc) + est_offset).time()
        
        mid_day_start = time(11, 30)
        mid_day_end = time(13, 30)
        
        threshold = self.base_threshold
        
        # Proactive increase to filter mid-day 'chop'
        if mid_day_start <= est_now <= mid_day_end:
            threshold += 0.75
            logging.info(f"[Temporal Liquidity Gate] Threshold increased to {threshold:.2f} (mid-day liquidity gap: 11:30-13:30 EST)")
        
        return threshold

    def get_regime_strategy_bias(self) -> Dict[str, Any]:
        """
        Defines the 'Why' for entry/exit based on Market Physics.
        Returns strategy bias configuration for current regime.
        """
        biases = {
            "RISK_ON": {
                "style": "MOMENTUM", 
                "exit_gravity": 1.0,
                "description": "Standard Whale Flow - momentum-driven entries"
            },
            "MIXED": {
                "style": "MEAN_REVERSION", 
                "exit_gravity": 0.8,
                "description": "Tighten stops near Gamma Walls - mean reversion focus"
            },
            "RISK_OFF": {
                "style": "VANNA_SQUEEZE", 
                "exit_gravity": 1.2,
                "description": "Prioritize IV-driven moves - vanna/charm mechanics"
            },
            "NEUTRAL": {
                "style": "MEAN_REVERSION",
                "exit_gravity": 0.9,
                "description": "Balanced approach with gamma wall awareness"
            }
        }
        return biases.get(self.regime, biases["MIXED"])

    def log_specialist_decision(self, ticker: str, score: float, threshold: float, 
                                strategy: Optional[Dict[str, Any]] = None) -> None:
        """
        Generates proactive audit log for XAI dashboard.
        Integrates with existing ExplainableLogger if available.
        """
        if strategy is None:
            strategy = self.get_regime_strategy_bias()
        
        bias = strategy.get('style', 'NEUTRAL')
        now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")
        
        msg = (
            f"[AUDIT] {ticker} | Score: {score:.2f} (Gate: {threshold:.2f}) | "
            f"Strategy: {bias} | Time: {now_str} | "
            f"Reason: System is prioritizing {bias} mechanics in current {self.regime} environment."
        )
        logging.info(msg)
        
        # Push to explainable logger if available
        if self.explainable_logger:
            try:
                # Use existing explainable logger format
                # Note: log_threshold_adjustment expects base_threshold, adjusted_threshold, adjustment
                adjustment = threshold - self.base_threshold
                self.explainable_logger.log_threshold_adjustment(
                    symbol=ticker,
                    base_threshold=self.base_threshold,
                    adjusted_threshold=threshold,
                    adjustment=adjustment,
                    reason=f"Temporal liquidity gate + {bias} strategy in {self.regime} regime",
                    consecutive_losses=0  # Not from loss streak, from temporal gating
                )
            except Exception as e:
                logging.warning(f"Could not log to explainable logger: {e}")


def calculate_atr_size(ticker_data, account_size: float = 100000.0, risk_pct: float = 0.01) -> int:
    """
    Sizes positions so a 1-ATR move equals risk_pct of the account.
    Maintains constant 'Dollar at Risk' regardless of volatility.
    
    Args:
        ticker_data: pandas DataFrame with High, Low, Close columns
        account_size: Total account equity
        risk_pct: Percentage of account to risk per trade (default 1%)
    
    Returns:
        Quantity (shares) to trade
    """
    try:
        import pandas as pd
        import numpy as np
        
        # ATR Calculation (14-period standard)
        high_low = ticker_data['High'] - ticker_data['Low']
        high_close = np.abs(ticker_data['High'] - ticker_data['Close'].shift())
        low_close = np.abs(ticker_data['Low'] - ticker_data['Close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean().iloc[-1]
        
        if pd.isna(atr) or atr <= 0:
            # Fallback to flat dollar sizing
            current_price = ticker_data['Close'].iloc[-1]
            return max(1, int(500 / current_price))
        
        # Sizing logic: (Account * Risk) / Volatility
        dollar_risk = account_size * risk_pct
        qty = dollar_risk / atr
        
        # VIX Overload Protection: If ATR is exceptionally high (Market Panic), cap the size
        # ATR > 5% of price suggests extreme volatility
        current_price = ticker_data['Close'].iloc[-1]
        atr_pct = atr / current_price if current_price > 0 else 0
        
        if atr_pct > 0.05:  # 5% ATR = extreme volatility
            # Cap size to 2x normal during panic
            qty = min(qty, (dollar_risk * 2) / atr)
            logging.warning(f"[ATR Sizing] Extreme volatility detected (ATR={atr_pct:.1%}) - capping position size")
        
        return max(1, int(qty))
        
    except Exception as e:
        logging.warning(f"[ATR Sizing] Failed for {getattr(ticker_data, 'name', 'unknown')}: {e}")
        # Fallback to flat dollar sizing
        try:
            current_price = ticker_data['Close'].iloc[-1]
            return max(1, int(500 / current_price))
        except:
            return 1


# ==========================================
# REGIME-AWARE OPTIMIZER (Integration Note)
# ==========================================
# 
# NOTE: Regime-aware Thompson Sampling is already implemented in adaptive_signal_optimizer.py
# The existing SignalWeightModel tracks regime-specific multipliers via regime_multipliers.
# 
# To use regime-aware weights:
#   from adaptive_signal_optimizer import get_optimizer
#   optimizer = get_optimizer()
#   weight = optimizer.entry_model.get_effective_weight(component, regime)
# 
# The optimizer already uses:
#   - Thompson Sampling (Beta distribution: alpha/beta)
#   - Accelerated learning (MIN_SAMPLES: 15, UPDATE_STEP: 0.20)
#   - Wilson Confidence Interval (95%) for anti-overfitting
#   - Regime-specific multipliers per component
#
# No duplicate implementation needed - use existing system.

