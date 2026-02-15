"""
Raw Signal Engine — Block 3B predictive logic; Block 3C/3D weighting and gating.
Computes trend, momentum, volatility, regime, sector, reversal, breakout, mean-reversion signals.
All signals normalized or bounded to [-1, 1] where applicable.
Block 3C: per-signal weights and gate multiplier (volatility/regime).
Block 3D: regime-specific weights, sector alignment, composite gate, bounded delta.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Union

# Block 3C: small safe weights for first iteration (max total ~0.18)
DEFAULT_SIGNAL_WEIGHTS: Dict[str, float] = {
    "trend_signal": 0.03,
    "momentum_signal": 0.03,
    "volatility_signal": 0.02,
    "regime_signal": 0.02,
    "sector_signal": 0.02,
    "reversal_signal": 0.02,
    "breakout_signal": 0.02,
    "mean_reversion_signal": 0.02,
}
SIGNAL_KEYS = list(DEFAULT_SIGNAL_WEIGHTS.keys())

# Block 3D: base weights (trend/momentum stronger; reversal/mean_reversion lower)
DEFAULT_SIGNAL_WEIGHTS_3D: Dict[str, float] = {
    "trend_signal": 0.05,
    "momentum_signal": 0.04,
    "volatility_signal": 0.025,
    "regime_signal": 0.025,
    "sector_signal": 0.025,
    "reversal_signal": 0.015,
    "breakout_signal": 0.025,
    "mean_reversion_signal": 0.015,
}
# Block 3D: bounds for weighted delta (final delta added to score)
WEIGHTED_DELTA_MAX_ABS = 0.25
COMPOSITE_GATE_MIN = 0.1
# Volatility gate thresholds on vol_signal [-1, 1]: low = chop/chaos, high = very healthy
VOL_GATE_THRESHOLD_LOW = 0.0
VOL_GATE_THRESHOLD_HIGH = 0.7
SECTOR_ALIGNMENT_DAMP = 0.5
SECTOR_ALIGNMENT_BOOST = 1.2


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _norm(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    """Clamp x to [lo, hi]."""
    return _clamp(x, lo, hi)


def _ema(prices: List[float], span: int) -> float:
    """Exponential moving average. Uses last `span` elements; if len < span, uses all."""
    if not prices:
        return 0.0
    n = min(span, len(prices))
    if n <= 0:
        return 0.0
    alpha = 2.0 / (n + 1) if n >= 1 else 1.0
    ema_val = prices[-n]
    for i in range(-n + 1, 0):
        ema_val = alpha * prices[i] + (1 - alpha) * ema_val
    return ema_val


def _sma(prices: List[float], n: int) -> float:
    """Simple moving average of last n prices."""
    if not prices or n <= 0:
        return 0.0
    window = prices[-n:]
    return sum(window) / len(window)


def _std(prices: List[float]) -> float:
    """Sample std dev of prices."""
    if len(prices) < 2:
        return 0.0
    m = sum(prices) / len(prices)
    var = sum((p - m) ** 2 for p in prices) / (len(prices) - 1)
    return math.sqrt(max(0, var))


def _returns(prices: List[float]) -> List[float]:
    """Price returns (percent or log). Use simple percent."""
    out = []
    for i in range(1, len(prices)):
        if prices[i - 1] and prices[i - 1] != 0:
            out.append((prices[i] - prices[i - 1]) / prices[i - 1])
        else:
            out.append(0.0)
    return out


def compute_trend_signal(price_series: Union[List[float], Any]) -> float:
    """
    Positive when short EMA > long EMA, negative when short < long, near zero when flat.
    Normalized to [-1, 1].
    """
    ps = price_series if isinstance(price_series, list) else []
    if len(ps) < 26:
        return 0.0
    short_ema = _ema(ps, 12)
    long_ema = _ema(ps, 26)
    if long_ema and long_ema != 0:
        raw = (short_ema - long_ema) / abs(long_ema)
        return _norm(raw * 10.0)  # scale so typical moves land in [-1,1]
    return 0.0


def compute_momentum_signal(price_series: Union[List[float], Any]) -> float:
    """
    Positive when price rising recently, negative when falling, near zero when flat.
    Normalized to [-1, 1].
    """
    ps = price_series if isinstance(price_series, list) else []
    if len(ps) < 5:
        return 0.0
    window = min(14, len(ps) - 1)
    first = ps[-window - 1] if len(ps) > window else ps[0]
    last = ps[-1]
    if first and first != 0:
        raw = (last - first) / abs(first)
        return _norm(raw * 5.0)
    return 0.0


def compute_volatility_signal(price_series: Union[List[float], Any]) -> float:
    """
    Positive when volatility in healthy band; negative when very low (chop) or very high (chaos).
    Normalized to [-1, 1].
    """
    ps = price_series if isinstance(price_series, list) else []
    if len(ps) < 5:
        return 0.0
    rets = _returns(ps)
    if not rets:
        return 0.0
    vol = _std(rets)
    # Healthy band: vol between ~0.005 and ~0.03 (daily). Chop < 0.002, chaos > 0.05
    if vol < 1e-9:
        return -1.0
    if vol < 0.002:
        return _norm(-1.0 + vol / 0.002, -1, 1)  # chop
    if vol <= 0.03:
        return _norm((vol - 0.002) / 0.028, -1, 1)  # healthy band -> positive
    if vol <= 0.05:
        return _norm(1.0 - (vol - 0.03) / 0.02, -1, 1)
    return -1.0  # chaos


def compute_regime_signal(regime_label: str) -> float:
    """Positive in BULL, negative in BEAR, near zero in RANGE/UNKNOWN."""
    r = (regime_label or "").strip().upper()
    if r == "BULL":
        return 1.0
    if r == "BEAR":
        return -1.0
    if r == "RANGE" or r == "MIXED":
        return 0.0
    return 0.0


def compute_sector_signal(sector_momentum: float) -> float:
    """Positive when sector trending up, negative when down, near zero when flat. Clamped to [-1, 1]."""
    try:
        m = float(sector_momentum or 0)
        return _norm(m)
    except (TypeError, ValueError):
        return 0.0


def _rsi(prices: List[float], period: int = 14) -> float:
    """Classic RSI [0, 100]. Returns 50 if insufficient data."""
    ps = prices if isinstance(prices, list) else []
    if len(ps) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(-period, 0):
        chg = ps[i] - ps[i - 1]
        if chg > 0:
            gains.append(chg)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(-chg)
    avg_gain = sum(gains) / period if gains else 0.0
    avg_loss = sum(losses) / period if losses else 0.0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1 + rs))


def compute_reversal_signal(price_series: Union[List[float], Any]) -> float:
    """
    Positive when downside exhaustion suggests bounce (RSI oversold);
    negative when upside exhaustion suggests drop (RSI overbought).
    Normalized to [-1, 1].
    """
    ps = price_series if isinstance(price_series, list) else []
    if len(ps) < 16:
        return 0.0
    rsi = _rsi(ps, 14)
    if rsi <= 30:
        return _norm((30 - rsi) / 30.0, 0, 1)  # oversold -> positive
    if rsi >= 70:
        return _norm((rsi - 70) / 30.0, -1, 0)  # overbought -> negative
    return 0.0


def compute_breakout_signal(price_series: Union[List[float], Any]) -> float:
    """
    Positive when breaking above resistance, negative when breaking below support.
    Uses recent high/low as proxy for resistance/support.
    """
    ps = price_series if isinstance(price_series, list) else []
    if len(ps) < 21:
        return 0.0
    lookback = 20
    recent_high = max(ps[-lookback:-1]) if len(ps) > 1 else ps[-1]
    recent_low = min(ps[-lookback:-1]) if len(ps) > 1 else ps[-1]
    current = ps[-1]
    span = recent_high - recent_low
    if span and span > 0:
        # above resistance -> positive, below support -> negative
        raw = (current - (recent_high + recent_low) / 2) / (span / 2)
        return _norm(raw)
    return 0.0


def compute_mean_reversion_signal(price_series: Union[List[float], Any]) -> float:
    """
    Positive when stretched down (below MA) in stable context;
    negative when stretched up. Z-score style, normalized to [-1, 1].
    """
    ps = price_series if isinstance(price_series, list) else []
    if len(ps) < 20:
        return 0.0
    sma = _sma(ps, 20)
    std = _std(ps[-20:])
    current = ps[-1]
    if std and std > 0:
        z = (current - sma) / std
        # stretched down (z < 0) -> positive mean reversion; stretched up (z > 0) -> negative
        return _norm(-z / 2.0)
    return 0.0


def build_raw_signals(
    price_series: Union[List[float], Any],
    regime_label: str,
    sector_momentum: float,
) -> Dict[str, float]:
    """
    Returns a dict of all raw signals (floats).
    Block 3B: real predictive logic; all signals normalized/bounded.
    """
    ps = price_series if isinstance(price_series, list) else []
    return {
        "trend_signal": float(compute_trend_signal(ps)),
        "momentum_signal": float(compute_momentum_signal(ps)),
        "volatility_signal": float(compute_volatility_signal(ps)),
        "regime_signal": float(compute_regime_signal(regime_label or "")),
        "sector_signal": float(compute_sector_signal(float(sector_momentum or 0))),
        "reversal_signal": float(compute_reversal_signal(ps)),
        "breakout_signal": float(compute_breakout_signal(ps)),
        "mean_reversion_signal": float(compute_mean_reversion_signal(ps)),
    }


def compute_signal_gate_multiplier(raw_signals: Union[Dict[str, float], Any]) -> float:
    """
    Block 3C: gate multiplier in [0, 1] based on volatility and regime.
    - 1.0 when volatility in healthy band and regime is BULL/BEAR.
    - 0.5 when regime is RANGE/UNKNOWN (damp).
    - 0.25 when volatility indicates chop/chaos (vol_signal < 0).
    Ensures we don't amplify signals in chaotic or unclear regimes.
    """
    if not isinstance(raw_signals, dict):
        return 0.5
    vol = raw_signals.get("volatility_signal")
    regime = raw_signals.get("regime_signal")
    try:
        vol_f = float(vol) if vol is not None else 0.0
        regime_f = float(regime) if regime is not None else 0.0
    except (TypeError, ValueError):
        return 0.5
    if vol_f < 0:
        return 0.25
    if regime_f == 0.0:
        return 0.5
    return 1.0


def get_weighted_signal_delta(
    raw_signals: Union[Dict[str, float], Any],
    weights: Union[Dict[str, float], None] = None,
) -> float:
    """
    Block 3C: weighted sum of raw signals for entry score delta.
    delta = sum(weights[k] * raw_signals[k]) for each k in weights.
    Missing keys in raw_signals treated as 0.0. Returns float.
    """
    if not isinstance(raw_signals, dict):
        return 0.0
    w = weights if isinstance(weights, dict) else DEFAULT_SIGNAL_WEIGHTS
    delta = 0.0
    for k, weight in w.items():
        try:
            v = raw_signals.get(k)
            val = float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            val = 0.0
        delta += weight * val
    return float(delta)


# ---------- Block 3D: regime-specific weights, sector alignment, composite gate ----------


def compute_regime_adjusted_weights(regime_label: str) -> Dict[str, float]:
    """
    Block 3D: regime-specific weight multipliers applied to base weights.
    BULL: increase trend, momentum, breakout; decrease reversal, mean_reversion.
    BEAR: increase trend, momentum, reversal; decrease mean_reversion.
    RANGE: increase reversal, mean_reversion; decrease trend, breakout.
    Returns dict of final weights (base * regime multiplier). All values floats.
    """
    base = dict(DEFAULT_SIGNAL_WEIGHTS_3D)
    r = (regime_label or "").strip().upper()
    if r == "BULL":
        base["trend_signal"] *= 1.3
        base["momentum_signal"] *= 1.2
        base["breakout_signal"] *= 1.2
        base["reversal_signal"] *= 0.7
        base["mean_reversion_signal"] *= 0.7
    elif r == "BEAR":
        base["trend_signal"] *= 1.2
        base["momentum_signal"] *= 1.2
        base["reversal_signal"] *= 1.3
        base["mean_reversion_signal"] *= 0.8
        base["breakout_signal"] *= 0.9
    else:
        base["trend_signal"] *= 0.7
        base["momentum_signal"] *= 0.8
        base["reversal_signal"] *= 1.3
        base["mean_reversion_signal"] *= 1.3
        base["breakout_signal"] *= 0.7
    return {k: float(v) for k, v in base.items()}


def compute_sector_alignment_multiplier(raw_signals: Union[Dict[str, float], Any]) -> float:
    """
    Block 3D: sector-trend alignment. If sector_signal and trend_signal disagree → damp (0.5);
    if they agree → boost (1.2). Missing keys treated as 0.0. Returns float.
    """
    if not isinstance(raw_signals, dict):
        return 1.0
    try:
        sector = float(raw_signals.get("sector_signal") or 0.0)
        trend = float(raw_signals.get("trend_signal") or 0.0)
    except (TypeError, ValueError):
        return 1.0
    if sector == 0.0 and trend == 0.0:
        return 1.0
    if (sector > 0 and trend > 0) or (sector < 0 and trend < 0):
        return float(SECTOR_ALIGNMENT_BOOST)
    return float(SECTOR_ALIGNMENT_DAMP)


def compute_volatility_gate(raw_signals: Union[Dict[str, float], Any]) -> float:
    """
    Block 3D: volatility gate. vol_signal > threshold_high → 0.5; vol_signal < threshold_low → 0.25;
    else → 1.0. vol_signal in [-1, 1]; low = chop/chaos, high = very healthy. Returns float.
    """
    if not isinstance(raw_signals, dict):
        return 0.5
    try:
        vol = float(raw_signals.get("volatility_signal") or 0.0)
    except (TypeError, ValueError):
        return 0.5
    if vol < VOL_GATE_THRESHOLD_LOW:
        return 0.25
    if vol > VOL_GATE_THRESHOLD_HIGH:
        return 0.5
    return 1.0


def _compute_regime_gate(raw_signals: Union[Dict[str, float], Any], regime_label: str) -> float:
    """
    Block 3D: regime gate. If signal direction contradicts regime (e.g. BULL but trend < 0) → 0.5; else 1.0.
    """
    if not isinstance(raw_signals, dict):
        return 1.0
    r = (regime_label or "").strip().upper()
    try:
        trend = float(raw_signals.get("trend_signal") or 0.0)
        momentum = float(raw_signals.get("momentum_signal") or 0.0)
    except (TypeError, ValueError):
        return 1.0
    if r == "BULL":
        if trend < 0 or momentum < 0:
            return 0.5
    elif r == "BEAR":
        if trend > 0 or momentum > 0:
            return 0.5
    return 1.0


def compute_composite_gate(
    raw_signals: Union[Dict[str, float], Any],
    regime_label: str,
    sector_momentum: float,
) -> float:
    """
    Block 3D: composite gate = vol_gate * regime_gate * sector_alignment_multiplier.
    Bounded >= COMPOSITE_GATE_MIN (0.1). All inputs optional; missing keys → safe defaults.
    Returns float.
    """
    if not isinstance(raw_signals, dict):
        raw_signals = {}
    vol_gate = compute_volatility_gate(raw_signals)
    regime_gate = _compute_regime_gate(raw_signals, regime_label or "")
    sector_mult = compute_sector_alignment_multiplier(raw_signals)
    composite = float(vol_gate) * float(regime_gate) * float(sector_mult)
    return float(max(COMPOSITE_GATE_MIN, min(1.0, composite)))


def get_weighted_signal_delta_3D(
    raw_signals: Union[Dict[str, float], Any],
    weights: Union[Dict[str, float], None],
    gate: float,
) -> float:
    """
    Block 3D: weighted delta with gate applied; result clamped to [-WEIGHTED_DELTA_MAX_ABS, +WEIGHTED_DELTA_MAX_ABS].
    weights default to DEFAULT_SIGNAL_WEIGHTS_3D. Missing keys in raw_signals → 0.0. Returns float.
    """
    if not isinstance(raw_signals, dict):
        return 0.0
    w = weights if isinstance(weights, dict) else DEFAULT_SIGNAL_WEIGHTS_3D
    delta = 0.0
    for k, weight in w.items():
        try:
            v = raw_signals.get(k)
            val = float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            val = 0.0
        delta += weight * val
    g = float(gate) if gate is not None else 0.5
    result = g * delta
    return float(_clamp(result, -WEIGHTED_DELTA_MAX_ABS, WEIGHTED_DELTA_MAX_ABS))
