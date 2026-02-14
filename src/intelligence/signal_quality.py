"""
Signal quality: smoothing, persistence, longevity scoring, volatility filtering, trend confirmation.
Used by live_entry_adjustments for entry scoring.
"""
from __future__ import annotations

from collections import deque
from typing import Dict

# Per-symbol state for SignalQuality (history, EMA)
_engines: Dict[str, "SignalQuality"] = {}


class SignalQuality:
    """
    Provides smoothing, persistence, longevity scoring, volatility filtering,
    and trend confirmation for entry signals.
    """

    def __init__(self, max_history: int = 20, ema_alpha: float = 0.3) -> None:
        self.history: deque = deque(maxlen=max_history)
        self.ema_alpha = ema_alpha
        self.last_ema: float | None = None

    def update(self, raw_signal: float) -> float:
        """Update EMA-smoothed signal. Returns current EMA."""
        self.history.append(float(raw_signal))
        if self.last_ema is None:
            self.last_ema = float(raw_signal)
        else:
            self.last_ema = (
                self.ema_alpha * float(raw_signal)
                + (1 - self.ema_alpha) * self.last_ema
            )
        return self.last_ema

    def persistence_score(self) -> float:
        """Require at least 2 consecutive positive signals. Returns 1, -1, or 0."""
        if len(self.history) < 3:
            return 0.0
        a, b = self.history[-2], self.history[-1]
        return 1.0 if (a > 0 and b > 0) else (-1.0 if (a <= 0 and b <= 0) else 0.0)

    def longevity_score(self) -> float:
        """Longevity = average of last N smoothed signals."""
        if not self.history:
            return 0.0
        return sum(self.history) / len(self.history)

    def trend_confirmation(self) -> float:
        """Trend confirmation: last 3 smoothed signals increasing. Returns 1, -1, or 0."""
        if len(self.history) < 3:
            return 0.0
        a, b, c = self.history[-3], self.history[-2], self.history[-1]
        return 1.0 if (a < b < c) else (-1.0 if (a > b > c) else 0.0)

    def volatility_filter(self, atr: float, threshold: float = 0.2) -> float:
        """Reject signals during extreme chop (low ATR). Returns 1 if ok, -1 if filter."""
        return 1.0 if (atr is not None and float(atr) > threshold) else -1.0


def get_engine(symbol: str, max_history: int = 20, ema_alpha: float = 0.3) -> SignalQuality:
    """Get or create SignalQuality engine for symbol."""
    if symbol not in _engines:
        _engines[symbol] = SignalQuality(max_history=max_history, ema_alpha=ema_alpha)
    return _engines[symbol]


def signal_quality_delta(
    symbol: str,
    raw_signal: float = 0.0,
    atr: float | None = None,
    *,
    weight_smoothed: float = 0.10,
    weight_persistence: float = 0.05,
    weight_longevity: float = 0.10,
    weight_trend: float = 0.05,
    weight_vol: float = 0.05,
) -> float:
    """
    Compute signal-quality adjustment to add to composite score.
    Uses smoothing, persistence, longevity, trend confirmation, volatility filter.
    Returns delta (can be negative). If no history yet, returns 0.
    """
    engine = get_engine(symbol)
    smoothed = engine.update(raw_signal)
    persistence = engine.persistence_score()
    longevity = engine.longevity_score()
    trend = engine.trend_confirmation()
    atr_val = float(atr) if atr is not None else 0.5
    vol_ok = engine.volatility_filter(atr_val)
    delta = (
        weight_smoothed * smoothed
        + weight_persistence * persistence
        + weight_longevity * longevity
        + weight_trend * trend
        + weight_vol * vol_ok
    )
    return round(delta, 4)
