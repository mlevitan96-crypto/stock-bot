#!/usr/bin/env python3
"""
Alpha Signature Capture
Captures RVOL, RSI, and Put/Call Ratio at decision points for forensic analysis.
"""

import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

try:
    import alpaca_trade_api as tradeapi
    from dotenv import load_dotenv
    import os
    load_dotenv()
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

def calculate_rsi(prices: list, period: int = 14) -> Optional[float]:
    """
    Calculate RSI (Relative Strength Index) for a list of prices.
    
    Args:
        prices: List of closing prices (most recent last)
        period: RSI period (default: 14)
    
    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(prices) < period + 1:
        return None
    
    # Calculate price changes
    deltas = []
    for i in range(1, len(prices)):
        deltas.append(prices[i] - prices[i-1])
    
    # Separate gains and losses
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    
    # Calculate average gain and loss
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100.0  # All gains, no losses
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)

def calculate_rvol(api, symbol: str, window_minutes: int = 20) -> Optional[float]:
    """
    Calculate Relative Volume (RVOL) - current volume vs average volume.
    
    Args:
        api: Alpaca API client
        symbol: Ticker symbol
        window_minutes: Window for current volume (default: 20 minutes)
    
    Returns:
        RVOL ratio (current_volume / avg_volume) or None if unavailable
    """
    try:
        if not ALPACA_AVAILABLE:
            return None
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=window_minutes)
        
        # Get recent bars for current volume
        recent_bars = api.get_bars(
            symbol,
            "1Min",
            start=start_time.isoformat(),
            end=end_time.isoformat(),
            limit=window_minutes
        ).df
        
        if recent_bars.empty:
            return None
        
        current_volume = recent_bars['volume'].sum()
        
        # Get historical bars for average volume (last 20 days, same time window)
        historical_start = end_time - timedelta(days=20)
        historical_bars = api.get_bars(
            symbol,
            "1Day",
            start=historical_start.isoformat(),
            end=end_time.isoformat(),
            limit=20
        ).df
        
        if historical_bars.empty:
            return None
        
        # Calculate average daily volume
        avg_daily_volume = historical_bars['volume'].mean()
        
        # Normalize current volume to daily equivalent (assuming 390 trading minutes per day)
        current_volume_daily_equivalent = (current_volume / window_minutes) * 390
        
        if avg_daily_volume == 0:
            return None
        
        rvol = current_volume_daily_equivalent / avg_daily_volume
        return round(rvol, 2)
    
    except Exception:
        return None

def calculate_put_call_ratio(uw_cache: Dict[str, Any], symbol: str) -> Optional[float]:
    """
    Calculate Put/Call Ratio for a ticker from UW cache.
    
    Args:
        uw_cache: UW flow cache dictionary
        symbol: Ticker symbol
    
    Returns:
        Put/Call Ratio (puts / calls) or None if unavailable
    """
    try:
        symbol_data = uw_cache.get(symbol, {})
        flow_trades = symbol_data.get("flow_trades", [])
        
        if not flow_trades:
            return None
        
        call_volume = 0
        put_volume = 0
        
        for trade in flow_trades:
            option_type = trade.get("option_type", "").upper()
            volume = trade.get("volume", 0)
            
            if option_type == "CALL":
                call_volume += volume
            elif option_type == "PUT":
                put_volume += volume
        
        if call_volume == 0:
            return None  # Can't calculate ratio without calls
        
        pcr = put_volume / call_volume
        return round(pcr, 3)
    
    except Exception:
        return None

def capture_alpha_signature(api, symbol: str, uw_cache: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capture complete alpha signature at decision point.
    
    Args:
        api: Alpaca API client
        symbol: Ticker symbol
        uw_cache: UW flow cache dictionary
    
    Returns:
        Dict with:
            - rvol: Relative Volume ratio
            - rsi: RSI (14-period)
            - put_call_ratio: Put/Call Ratio
            - timestamp: Capture timestamp
    """
    signature = {
        "rvol": None,
        "rsi": None,
        "put_call_ratio": None,
        "timestamp": time.time()
    }
    
    try:
        # Calculate RVOL
        signature["rvol"] = calculate_rvol(api, symbol)
        
        # Calculate RSI
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)  # Get 30 days for RSI calculation
            
            bars = api.get_bars(
                symbol,
                "1Day",
                start=start_time.isoformat(),
                end=end_time.isoformat(),
                limit=30
            ).df
            
            if not bars.empty and len(bars) >= 15:
                closes = bars['close'].tolist()
                signature["rsi"] = calculate_rsi(closes, period=14)
        except Exception:
            pass
        
        # Calculate Put/Call Ratio
        signature["put_call_ratio"] = calculate_put_call_ratio(uw_cache, symbol)
    
    except Exception:
        pass  # Fail gracefully
    
    return signature
