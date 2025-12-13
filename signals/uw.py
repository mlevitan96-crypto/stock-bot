#!/usr/bin/env python3
"""
Unusual Whales (UW) Signal Layer

Provides institutional-grade signal utilities leveraging UW option flow data:
- Dynamic weighting by market regime
- Flow-based entry gates
- Conviction-based position sizing
- Adaptive exits when flow flips
- Theme-based signal propagation
"""

from typing import Dict, List, Any, Optional


def uw_weighting(regime: str, uw_flow_score: float) -> float:
    """
    Dynamic UW flow weighting by market regime.
    
    Args:
        regime: Market regime ('RISK_ON', 'RISK_OFF', 'NEUTRAL')
        uw_flow_score: Base flow score (can be positive or negative)
    
    Returns:
        Adjusted flow score based on regime
    
    Regime multipliers:
        - RISK_ON: Amplify bullish conviction (1.5x)
        - RISK_OFF: Amplify bearish penalty (2.0x), dampen bullish (0.5x)
        - NEUTRAL: Modest influence (1.0x)
    
    Example:
        >>> uw_weighting('RISK_ON', 2.0)  # Bullish flow in risk-on regime
        3.0
        >>> uw_weighting('RISK_OFF', -1.5)  # Bearish flow in risk-off regime
        -3.0
    """
    reg = (regime or "NEUTRAL").upper()
    score = uw_flow_score or 0.0
    
    if reg == "RISK_ON":
        return score * 1.5
    elif reg == "RISK_OFF":
        # Amplify bearish signals, dampen bullish
        return score * 2.0 if score < 0 else score * 0.5
    else:
        return score * 1.0


def uw_entry_gate(uw_cluster: Optional[Dict[str, Any]]) -> bool:
    """
    Flow-based entry gate for institutional quality signals.
    
    Args:
        uw_cluster: Cluster data with 'count' and 'avg_premium' keys
    
    Returns:
        True if cluster meets institutional threshold, False otherwise
    
    Requirements:
        - Minimum 2 sweeps within cluster window (60 seconds)
        - Average premium >= $100,000 (institutional size)
    
    Example:
        >>> uw_entry_gate({'count': 3, 'avg_premium': 250000})
        True
        >>> uw_entry_gate({'count': 1, 'avg_premium': 50000})
        False
    """
    if not uw_cluster:
        return False
    
    count = int(uw_cluster.get("count", 0))
    avg_premium = float(uw_cluster.get("avg_premium", 0.0))
    
    return count >= 2 and avg_premium >= 100_000.0


def uw_size_modifier(base_contracts: int, uw_sentiment: str, conviction: float) -> int:
    """
    Sizing modifier based on UW sentiment and conviction.
    
    Args:
        base_contracts: Base position size (shares or contracts)
        uw_sentiment: Flow sentiment ('BULLISH', 'BEARISH', or other)
        conviction: Conviction score (0.0 to 1.0)
    
    Returns:
        Adjusted position size (minimum 1)
    
    Modifiers:
        - BULLISH + conviction > 0.70: +20% size
        - BEARISH + conviction > 0.70: -20% size
        - Otherwise: No change
    
    Note: Capital ramp and risk limits still apply after this modifier
    
    Example:
        >>> uw_size_modifier(10, 'BULLISH', 0.85)
        12
        >>> uw_size_modifier(10, 'BEARISH', 0.75)
        8
    """
    sentiment = (uw_sentiment or "").upper()
    conv = float(conviction or 0.0)
    
    if sentiment == "BULLISH" and conv > 0.70:
        return max(1, int(round(base_contracts * 1.20)))
    elif sentiment == "BEARISH" and conv > 0.70:
        return max(1, int(round(base_contracts * 0.80)))
    
    return base_contracts


def uw_exit_adjustment(open_position: Dict[str, Any], uw_flow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tighten trailing stops when UW flow flips against current position.
    
    Args:
        open_position: Position data with 'side' and 'trail_stop' keys
        uw_flow: Current UW flow with 'sentiment' and 'conviction' keys
    
    Returns:
        Updated position dict with adjusted trail_stop if flow conflicts
    
    Logic:
        - If conviction < 0.6: No adjustment (low confidence)
        - If LONG position + BEARISH flow: Tighten stop by 20% (0.80x)
        - If SHORT position + BULLISH flow: Tighten stop by 20% (0.80x)
        - Otherwise: No change
    
    Example:
        >>> pos = {'side': 'LONG', 'trail_stop': 1.0}
        >>> flow = {'sentiment': 'BEARISH', 'conviction': 0.75}
        >>> uw_exit_adjustment(pos, flow)
        {'side': 'LONG', 'trail_stop': 0.8}
    """
    pos = dict(open_position or {})
    sentiment = (uw_flow.get("sentiment") or "").upper()
    conv = float(uw_flow.get("conviction") or 0.0)
    
    # Only adjust on high-conviction signals
    if conv < 0.6:
        return pos
    
    # Tighten stops when flow conflicts with position
    if sentiment == "BEARISH" and pos.get("side") == "LONG":
        pos["trail_stop"] = round(float(pos.get("trail_stop", 1.0)) * 0.80, 4)
    elif sentiment == "BULLISH" and pos.get("side") == "SHORT":
        pos["trail_stop"] = round(float(pos.get("trail_stop", 1.0)) * 0.80, 4)
    
    return pos


def uw_theme_propagation(symbol: str, uw_signal: Dict[str, Any], theme_map: Dict[str, List[str]]) -> Dict[str, float]:
    """
    Propagate UW conviction across correlated symbols within a theme.
    
    Args:
        symbol: Source symbol generating the signal
        uw_signal: Signal data with 'conviction' key
        theme_map: Mapping of symbols to lists of correlated symbols
    
    Returns:
        Dict mapping correlated symbols to propagated conviction (half-weight)
    
    Use case:
        Strong NVDA flow modestly boosts AMD/AVGO candidates within Semiconductors theme
    
    Example:
        >>> theme_map = {'NVDA': ['AMD', 'AVGO', 'INTC']}
        >>> uw_theme_propagation('NVDA', {'conviction': 0.80}, theme_map)
        {'AMD': 0.4, 'AVGO': 0.4, 'INTC': 0.4}
    """
    conv = float(uw_signal.get("conviction", 0.0))
    correlated = theme_map.get(symbol, [])
    
    # Apply half-weight to correlated symbols
    return {sym: round(conv * 0.5, 3) for sym in correlated}
