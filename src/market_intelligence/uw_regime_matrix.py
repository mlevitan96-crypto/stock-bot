"""
Daily regime dictionary (shadow-only): GEX profile, dark-pool reference levels, sweep activity.

**Not used for live order gating.** Consume only from shadow telemetry paths.
"""
from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional

# Proximity: price within this fractional band of a DP level counts as "support" (shadow flag only).
_DEFAULT_DP_PROXIMITY_FRAC = 0.003  # 0.3%


def _safe_upper_ticker(ticker: str) -> str:
    return str(ticker or "").strip().upper()[:32]


def _is_momentum_strategy(intended_strategy: str) -> bool:
    s = str(intended_strategy or "").lower()
    return any(k in s for k in ("momentum", "trend", "breakout", "impulse"))


class UWRegimeMatrix:
    """
    In-memory regime snapshot. Production path would hydrate from UW/GEX feeds;
    tests and shadow lane use ``_refresh_daily_regime_mock()`` until wired.
    """

    def __init__(self) -> None:
        self.gex_profile: Dict[str, str] = {}
        self.dark_pool_levels: Dict[str, List[float]] = {}
        self.recent_sweeps: Dict[str, bool] = {}
        self._source = "uninitialized"
        self._refresh_daily_regime_mock()

    def _refresh_daily_regime_mock(self) -> None:
        """Deterministic dummy regime rows for tests and shadow dry-runs."""
        self.gex_profile = {
            "AAPL": "negative",
            "MSFT": "positive",
            "SPY": "neutral",
            "QQQ": "positive",
        }
        self.dark_pool_levels = {
            "AAPL": [175.0, 174.5],
            "MSFT": [380.0, 381.25],
            "SPY": [500.0],
        }
        self.recent_sweeps = {
            "AAPL": True,
            "MSFT": False,
            "SPY": False,
            "QQQ": True,
        }
        self._source = "mock_daily_refresh"

    def evaluate_trade_conviction(
        self,
        ticker: str,
        intended_strategy: str,
        current_price: float,
    ) -> Dict[str, Any]:
        """
        Shadow query contract. Never raises: returns a dict with ``regime_conviction`` in
        {``veto``, ``high_conviction_boost``, ``neutral``} and auxiliary flags.

        Rules (first match wins):
        - Positive GEX + momentum strategy → ``veto``
        - Negative GEX + recent sweeps → ``high_conviction_boost``
        - Else if dark-pool proximity → ``dark_pool_support`` flag; ``regime_conviction`` stays ``neutral`` unless above matched
        """
        try:
            return self._evaluate_trade_conviction_inner(ticker, intended_strategy, current_price)
        except Exception as exc:  # pragma: no cover — belt-and-suspenders vs shadow bleed
            return {
                "regime_conviction": "neutral",
                "dark_pool_support": False,
                "gex_read": "unknown",
                "sweeps_recent": False,
                "dark_pool_min_distance_frac": None,
                "intended_strategy_norm": str(intended_strategy or "")[:200],
                "ticker": _safe_upper_ticker(ticker),
                "current_price": float(current_price) if math.isfinite(float(current_price)) else None,
                "regime_matrix_source": self._source,
                "shadow_uw_regime_error": str(exc)[:200],
            }

    def _evaluate_trade_conviction_inner(
        self,
        ticker: str,
        intended_strategy: str,
        current_price: float,
    ) -> Dict[str, Any]:
        sym = _safe_upper_ticker(ticker)
        strat = str(intended_strategy or "neutral_default")
        try:
            px = float(current_price)
        except (TypeError, ValueError):
            px = float("nan")
        if not math.isfinite(px):
            px = 0.0

        gex = str(self.gex_profile.get(sym) or "neutral").strip().lower()
        if gex not in ("positive", "negative", "neutral"):
            gex = "neutral"

        sweeps = bool(self.recent_sweeps.get(sym, False))
        momentum = _is_momentum_strategy(strat)

        levels = self.dark_pool_levels.get(sym) or []
        min_frac: Optional[float] = None
        prox_frac = float(os.getenv("UW_REGIME_DP_PROXIMITY_FRAC", str(_DEFAULT_DP_PROXIMITY_FRAC)) or _DEFAULT_DP_PROXIMITY_FRAC)
        if not math.isfinite(prox_frac) or prox_frac <= 0:
            prox_frac = _DEFAULT_DP_PROXIMITY_FRAC

        if levels and px > 0.0 and math.isfinite(px):
            den = max(abs(px), 1e-12)
            for lvl in levels:
                try:
                    lv = float(lvl)
                except (TypeError, ValueError):
                    continue
                if not math.isfinite(lv) or lv <= 0:
                    continue
                frac_dist = abs(px - lv) / den
                if math.isfinite(frac_dist):
                    min_frac = frac_dist if min_frac is None else min(min_frac, frac_dist)

        dp_support = bool(min_frac is not None and min_frac <= prox_frac)

        conviction = "neutral"
        if gex == "positive" and momentum:
            conviction = "veto"
        elif gex == "negative" and sweeps:
            conviction = "high_conviction_boost"

        return {
            "regime_conviction": conviction,
            "dark_pool_support": dp_support,
            "gex_read": gex,
            "sweeps_recent": sweeps,
            "momentum_strategy": momentum,
            "dark_pool_min_distance_frac": None if min_frac is None else round(float(min_frac), 8),
            "dark_pool_proximity_threshold_frac": round(float(prox_frac), 8),
            "intended_strategy_norm": strat[:200],
            "ticker": sym or "UNKNOWN",
            "current_price": round(float(px), 6) if px > 0.0 and math.isfinite(px) else None,
            "regime_matrix_source": self._source,
        }


_MATRIX: Optional[UWRegimeMatrix] = None


def get_uw_regime_matrix() -> UWRegimeMatrix:
    global _MATRIX
    if _MATRIX is None:
        _MATRIX = UWRegimeMatrix()
    return _MATRIX


def reset_uw_regime_matrix_for_tests() -> None:
    global _MATRIX
    _MATRIX = None
