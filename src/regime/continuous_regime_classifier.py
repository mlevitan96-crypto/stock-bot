"""
Lightweight continuous regime classifier (TREND / CHOP / MACRO_DOWNTREND).

**Design intent (Quant + Strategy):** infer *state* from overnight macro shock plus a real-time
**trend-to-noise ratio (TNR)** on 1m SPY closes from the live stream bar cache. A **Schmitt
trigger** on TNR reduces flip-flops (separate from time-based dwell hysteresis).

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
from typing import Any, List, Mapping, Optional, Sequence, Tuple


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


def calculate_trend_to_noise_ratio(prices: Sequence[float], window: int) -> float:
    """
    Trend-to-noise on closing prices (1m bars): **efficiency ratio**.

    ``TNR = |C_last - C_first| / (sum_i |ΔC_i| + ε)`` over the last ``window`` closes.
    Range roughly ``[0, 1]`` when ``window`` matches the slice length (choppy → near 0, smooth drift → near 1).

    Raises ``ValueError`` if ``window`` < 2 or fewer than two finite prices are available.
    """
    w = int(window)
    if w < 2:
        raise ValueError("window must be >= 2")
    seq = [float(p) for p in prices if isinstance(p, (int, float)) and float(p) == float(p)]
    if len(seq) < w:
        seq = seq[-w:] if len(seq) >= 2 else seq
    if len(seq) < 2:
        raise ValueError("prices must contain at least two finite values")
    use = seq[-w:]
    path = 0.0
    for i in range(1, len(use)):
        path += abs(use[i] - use[i - 1])
    net = abs(use[-1] - use[0])
    eps = float(os.environ.get("REGIME_TNR_EPS", "1e-12"))
    return float(net / (path + max(eps, 1e-15)))


def _tnr_thresholds() -> Tuple[float, float]:
    """(enter_chop, exit_chop): TNR below enter_chop → CHOP when coming from TREND; above exit_chop → TREND from CHOP."""
    try:
        low = float(os.environ.get("REGIME_TNR_ENTER_CHOP", "0.25").strip())
    except ValueError:
        low = 0.25
    try:
        high = float(os.environ.get("REGIME_TNR_EXIT_CHOP", "0.40").strip())
    except ValueError:
        high = 0.40
    if high <= low:
        high = low + 0.01
    return low, high


class SchmittTnrAxis:
    """Two-state Schmitt on TNR for TREND ↔ CHOP (MACRO handled upstream)."""

    __slots__ = ("_state",)

    def __init__(self) -> None:
        self._state = "TREND"

    def step(self, tnr: Optional[float]) -> str:
        if tnr is None or not (tnr == tnr):
            return str(self._state)
        low, high = _tnr_thresholds()
        st = str(self._state).strip().upper()
        if st not in ("TREND", "CHOP"):
            st = "TREND"
        if st == "TREND":
            if float(tnr) < low:
                st = "CHOP"
        else:
            if float(tnr) > high:
                st = "TREND"
        self._state = st
        return st


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
_SCH = SchmittTnrAxis()
_LAST_TNR: Optional[float] = None


def _regime_tnr_window() -> int:
    try:
        w = int(os.environ.get("REGIME_TNR_WINDOW", "32").strip())
    except ValueError:
        w = 32
    return max(2, min(400, w))


def _regime_spy_bar_max_age_sec() -> float:
    try:
        return float(os.environ.get("REGIME_SPY_BAR_MAX_AGE_SEC", "180").strip())
    except ValueError:
        return 180.0


def get_spy_1m_closes_from_stream_cache(limit: int) -> Optional[List[float]]:
    """
    Last ``limit`` SPY 1m closes (oldest first) from the live Alpaca stream ring buffer, if fresh.
    """
    try:
        from src.alpaca.stream_manager import get_stream_manager
    except Exception:
        return None
    mgr = get_stream_manager()
    if mgr is None or getattr(mgr, "price_cache", None) is None:
        return None
    lim = max(2, int(limit))
    try:
        df = mgr.price_cache.get_fresh_bars_df(
            "SPY",
            lim,
            max_age_sec=_regime_spy_bar_max_age_sec(),
        )
    except Exception:
        return None
    if df is None or getattr(df, "empty", True):
        return None
    try:
        closes = [float(x) for x in df["close"].tolist()]
    except Exception:
        return None
    if len(closes) < 2:
        return None
    return closes


def _compute_tnr_optional(ctx: Mapping[str, Any]) -> Optional[float]:
    global _LAST_TNR
    override = ctx.get("spy_1m_closes") or ctx.get("spy_1m_close_prices")
    if isinstance(override, (list, tuple)) and len(override) >= 2:
        try:
            tnr = calculate_trend_to_noise_ratio(override, min(len(override), _regime_tnr_window()))
            _LAST_TNR = float(tnr)
            return _LAST_TNR
        except Exception:
            pass
    closes = get_spy_1m_closes_from_stream_cache(_regime_tnr_window())
    if not closes:
        _LAST_TNR = None
        return None
    try:
        w = min(len(closes), _regime_tnr_window())
        tnr = calculate_trend_to_noise_ratio(closes, w)
        _LAST_TNR = float(tnr)
        return _LAST_TNR
    except Exception:
        _LAST_TNR = None
        return None


def _raw_regime_label(ctx: Mapping[str, Any]) -> str:
    """
    Pre-dwell label:
    - MACRO_DOWNTREND: SPY overnight proxy below threshold.
    - Else: Schmitt on TNR from live 1m SPY cache (fallback: vol ``high`` → CHOP, else TREND) when TNR unavailable.
    """
    spy = _spy_ret(ctx)
    try:
        macro_th = float(os.environ.get("REGIME_MACRO_SPY_RET_THRESHOLD", "-0.003").strip())
    except ValueError:
        macro_th = -0.003
    if spy <= macro_th:
        return "MACRO_DOWNTREND"
    tnr = _compute_tnr_optional(ctx)
    if tnr is not None:
        return str(_SCH.step(tnr))
    # No fresh SPY minute path: retain Schmitt state without a new crossing; if cold, use vol proxy.
    sch = str(_SCH.step(None))
    if sch == "TREND" and _vol_bucket(ctx) == "high":
        return "CHOP"
    return sch


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
    if not _truthy("REGIME_ENGINE_ENABLED", "0"):
        return "TREND", "TREND", spy, vol
    raw = _raw_regime_label(ctx)
    pub = str(_HY.step(raw))
    return pub, raw, spy, vol


def last_computed_tnr() -> Optional[float]:
    """Best-effort last TNR from the most recent classification path (thread-local engine)."""
    return _LAST_TNR
