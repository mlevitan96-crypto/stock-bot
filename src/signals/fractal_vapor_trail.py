"""
Shadow signal: recursive Hurst-style persistence on price returns + short-horizon dH/dt.

Emitted as ``shadow_fractal_vapor`` (dict) on trade_intent / shadow logs. Does **not** gate entries.
"""
from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

_LAST: Dict[str, Tuple[float, float]] = {}  # symbol -> (hurst, monotonic_ts)


def _log_returns(prices: Sequence[Any]) -> np.ndarray:
    xs = np.asarray([float(x) for x in prices if x is not None], dtype=float)
    xs = xs[np.isfinite(xs) & (xs > 0)]
    if xs.size < 8:
        return np.array([], dtype=float)
    lr = np.diff(np.log(xs))
    return lr[np.isfinite(lr)]


def _hurst_rs_simple(returns: np.ndarray) -> Optional[float]:
    """Small-sample R/S style persistence proxy in (0,1), ~0.5 = random walk."""
    x = np.asarray(returns, dtype=float).ravel()
    n = int(x.size)
    if n < 16:
        return None
    mu = float(np.mean(x))
    y = np.cumsum(x - mu)
    r = float(np.max(y) - np.min(y))
    s = float(np.std(x, ddof=1)) or 1e-12
    rs = r / s
    # Map RS to Hurst-like scale (heuristic, stable for gating telemetry only).
    h = math.log(rs + 1.0) / math.log(n + 1.0)
    return float(max(0.01, min(0.99, h)))


def compute_fractal_vapor_trail(
    price_series: Optional[Sequence[Any]],
    *,
    symbol: str = "",
) -> Dict[str, Any]:
    """
    Returns a dict suitable for ``shadow_fractal_vapor`` JSON field.

    Keys: hurst, hurst_derivative, n_prices, n_returns, symbol, ts_monotonic
    """
    sym = str(symbol or "").upper().strip()
    lr = _log_returns(price_series or [])
    H = _hurst_rs_simple(lr)
    now = time.monotonic()
    dH = None
    if sym and H is not None:
        prev = _LAST.get(sym)
        if prev is not None:
            Hp, tp = prev
            dt = max(1e-6, now - tp)
            dH = (H - Hp) / dt
        _LAST[sym] = (float(H), now)
    out: Dict[str, Any] = {
        "symbol": sym or None,
        "hurst": H,
        "hurst_derivative": dH,
        "n_prices": len(list(price_series or [])),
        "n_returns": int(lr.size),
        "ts_monotonic": now,
    }
    return out
