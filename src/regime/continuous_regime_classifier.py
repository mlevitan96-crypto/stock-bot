"""
Lightweight continuous regime classifier (TREND / CHOP / MACRO_DOWNTREND).

**Design intent (Quant + Strategy):** replace static clock buckets with *state* inferred from
live context (overnight macro shock + volatility regime). ML/Hurst/beta extensions plug in here.

**Red team — hysteresis:** raw labels pass through ``RegimeHysteresis`` so a noisy score cannot
flip execution mode every few minutes. Configure ``REGIME_MIN_DWELL_SEC`` (default 180s).

**CPA — chop / passive liquidity:** passive bid/ask improvement requires **post-only / maker**
routes and fee/rebate awareness; this module only **labels** regime — order placement stays in
execution layer behind explicit flags (``REGIME_CHOP_PASSIVE_ENTRY_ENABLED`` — default off).

All public outputs use native ``str`` / ``float`` for JSON safety.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Mapping, Optional, Tuple


def _truthy(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _spy_ret(ctx: Mapping[str, Any]) -> float:
    for k in ("spy_overnight_ret", "spy_overnight_return", "spy_ret"):
        v = ctx.get(k)
        if v is None:
            continue
        try:
            f = float(v)
            if f == f:
                return f
        except (TypeError, ValueError):
            continue
    return 0.0


def _vol_bucket(ctx: Mapping[str, Any]) -> str:
    v = str(ctx.get("volatility_regime") or ctx.get("vol_regime") or "mid").strip().lower()
    return v if v else "mid"


def _raw_regime_label(ctx: Mapping[str, Any]) -> str:
    """
    Cheap v0 classifier (no bar cache required):
    - MACRO_DOWNTREND: large negative SPY overnight proxy (configurable threshold).
    - CHOP: elevated vol regime (``high``) without macro crash — mean-reversion / range proxy.
    - TREND: default path for breakouts / standard Alpha 11.
    """
    spy = _spy_ret(ctx)
    try:
        macro_th = float(os.environ.get("REGIME_MACRO_SPY_RET_THRESHOLD", "-0.003").strip())
    except ValueError:
        macro_th = -0.003
    if spy <= macro_th:
        return "MACRO_DOWNTREND"
    if _vol_bucket(ctx) == "high":
        return "CHOP"
    return "TREND"


class RegimeHysteresis:
    """Minimum dwell in a published regime before switching (spread / churn guard)."""

    __slots__ = ("_locked", "_since")

    def __init__(self) -> None:
        self._locked = "TREND"
        self._since = 0.0

    def step(self, raw: str, now: Optional[float] = None) -> str:
        now_t = float(time.time() if now is None else now)
        try:
            dwell = float(os.environ.get("REGIME_MIN_DWELL_SEC", "180").strip())
        except ValueError:
            dwell = 180.0
        dwell = max(0.0, dwell)
        raw_u = str(raw or "TREND").strip().upper()
        if raw_u not in ("TREND", "CHOP", "MACRO_DOWNTREND"):
            raw_u = "TREND"
        if raw_u == self._locked:
            self._since = now_t
            return self._locked
        if dwell <= 0.0 or (now_t - self._since) >= dwell:
            self._locked = raw_u
            self._since = now_t
        return self._locked


_HY = RegimeHysteresis()


def classify_from_market_context(ctx: Mapping[str, Any]) -> str:
    """
    Returns one of ``TREND``, ``CHOP``, ``MACRO_DOWNTREND`` (native str, hysteresis-smoothed).
    When ``REGIME_ENGINE_ENABLED`` is false, always ``TREND`` (no behavior change).
    """
    if not _truthy("REGIME_ENGINE_ENABLED", "0"):
        return "TREND"
    raw = _raw_regime_label(ctx)
    return str(_HY.step(raw))


def regime_explain(ctx: Mapping[str, Any]) -> Tuple[str, str, float, str]:
    """(published_regime, raw_regime, spy_ret, vol_regime) for logging."""
    spy = _spy_ret(ctx)
    vol = _vol_bucket(ctx)
    raw = _raw_regime_label(ctx)
    pub = classify_from_market_context(ctx)
    return pub, raw, spy, vol
