"""
Raw Signal Engine Scaffolding
This module provides placeholder functions for generating raw signals.
These will be filled in during Block 3B.
"""
from __future__ import annotations

from typing import Any, Dict, List, Union


def compute_trend_signal(price_series: Union[List[float], Any]) -> float:
    """Placeholder trend signal."""
    return 0.0


def compute_momentum_signal(price_series: Union[List[float], Any]) -> float:
    """Placeholder momentum signal."""
    return 0.0


def compute_volatility_signal(price_series: Union[List[float], Any]) -> float:
    """Placeholder volatility-adjusted signal."""
    return 0.0


def compute_regime_signal(regime_label: str) -> float:
    """Placeholder regime-aware signal."""
    return 0.0


def compute_sector_signal(sector_momentum: float) -> float:
    """Placeholder sector-relative signal."""
    return 0.0


def compute_reversal_signal(price_series: Union[List[float], Any]) -> float:
    """Placeholder reversal signal."""
    return 0.0


def compute_breakout_signal(price_series: Union[List[float], Any]) -> float:
    """Placeholder breakout/breakdown signal."""
    return 0.0


def compute_mean_reversion_signal(price_series: Union[List[float], Any]) -> float:
    """Placeholder mean-reversion signal."""
    return 0.0


def build_raw_signals(
    price_series: Union[List[float], Any],
    regime_label: str,
    sector_momentum: float,
) -> Dict[str, float]:
    """
    Returns a dict of all raw signals.
    These are placeholders until Block 3B fills them in.
    """
    ps = price_series if isinstance(price_series, list) else []
    return {
        "trend_signal": compute_trend_signal(ps),
        "momentum_signal": compute_momentum_signal(ps),
        "volatility_signal": compute_volatility_signal(ps),
        "regime_signal": compute_regime_signal(regime_label or ""),
        "sector_signal": compute_sector_signal(float(sector_momentum or 0)),
        "reversal_signal": compute_reversal_signal(ps),
        "breakout_signal": compute_breakout_signal(ps),
        "mean_reversion_signal": compute_mean_reversion_signal(ps),
    }
