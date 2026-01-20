#!/usr/bin/env python3
"""
Market Context V2 (Structural Upgrade)
=====================================

Purpose:
- Provide a robust, cached "market context" snapshot that can be consumed by:
  - regime detection
  - posture decisions
  - composite scoring (v2)
  - shadow A/B comparisons

Key constraints (MANDATE):
- Additive only (does not change existing decisions by itself)
- All failures are non-fatal, logged to logs/system_events.jsonl
- Stale/missing data is detected and explicitly logged

Notes:
- Futures/VIX are implemented via *tradeable proxies* available on Alpaca:
  - Futures proxy: SPY/QQQ overnight return + premarket trend
  - Volatility proxy: VXX (front) and VXZ (back/mid) term proxy, plus their ratio
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple

# Permanent system events + global failure wrapper (non-blocking import).
try:
    from utils.system_events import global_failure_wrapper, log_system_event
except Exception:  # pragma: no cover
    def global_failure_wrapper(_subsystem):  # type: ignore
        def _d(fn):
            return fn
        return _d

    def log_system_event(*args, **kwargs):  # type: ignore
        return None

try:
    from config.registry import StateFiles, atomic_write_json, read_json
except Exception:  # pragma: no cover
    StateFiles = None  # type: ignore
    atomic_write_json = None  # type: ignore
    read_json = None  # type: ignore


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def _pct_change(a: float, b: float) -> float:
    # Return (b - a) / a, safe.
    a = _safe_float(a, 0.0)
    b = _safe_float(b, 0.0)
    if a <= 0:
        return 0.0
    return (b - a) / a


def _try_dt(x: Any) -> Optional[datetime]:
    if x is None:
        return None
    if isinstance(x, datetime):
        return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    if isinstance(x, str):
        s = x.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _clock_window(api) -> Tuple[Optional[datetime], Optional[datetime], Optional[bool]]:
    """
    Best-effort read of Alpaca clock.
    Returns (next_open_utc, next_close_utc, is_open).
    """
    try:
        clock = api.get_clock()
    except Exception:
        return None, None, None

    # alpaca_trade_api clock fields are iso strings
    try:
        is_open = bool(getattr(clock, "is_open", False))
    except Exception:
        is_open = None
    try:
        next_open = _try_dt(getattr(clock, "next_open", None))
        next_close = _try_dt(getattr(clock, "next_close", None))
    except Exception:
        next_open, next_close = None, None
    return next_open, next_close, is_open


def _get_last_bar_close(api, symbol: str, *, limit: int = 90) -> Tuple[Optional[float], Optional[datetime]]:
    """
    Fetch the most recent 1Min bar close, best-effort.
    Returns (close, timestamp_utc) or (None, None).
    """
    try:
        bars = api.get_bars(symbol, "1Min", limit=int(limit))
        df = getattr(bars, "df", None)
        if df is None:
            return None, None
        if df.empty:
            return None, None
        row = df.iloc[-1]
        close = _safe_float(row.get("close"))
        idx = df.index[-1]
        # pandas timestamp
        try:
            ts = idx.to_pydatetime()
        except Exception:
            try:
                ts = datetime.fromtimestamp(float(idx), tz=timezone.utc)
            except Exception:
                ts = None
        if ts and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return close, ts
    except Exception:
        return None, None


def _get_daily_close(api, symbol: str, *, days: int = 5) -> Tuple[Optional[float], Optional[datetime]]:
    """
    Fetch the most recent 1Day bar close, best-effort.
    Returns (close, timestamp_utc) or (None, None).
    """
    try:
        bars = api.get_bars(symbol, "1Day", limit=int(max(2, days)))
        df = getattr(bars, "df", None)
        if df is None or df.empty:
            return None, None
        row = df.iloc[-1]
        close = _safe_float(row.get("close"))
        idx = df.index[-1]
        try:
            ts = idx.to_pydatetime()
        except Exception:
            ts = None
        if ts and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return close, ts
    except Exception:
        return None, None


@dataclass(frozen=True)
class MarketContextV2:
    timestamp: str
    # Proxy “futures direction”
    spy_prev_close: float
    spy_last_1m: float
    spy_overnight_ret: float
    qqq_prev_close: float
    qqq_last_1m: float
    qqq_overnight_ret: float

    # Volatility proxy (VIX term structure approximation)
    vxx_close_1d: float
    vxz_close_1d: float
    vxx_vxz_ratio: float

    # Health / staleness
    spy_last_1m_ts: Optional[str]
    qqq_last_1m_ts: Optional[str]
    stale_1m: bool
    stale_reason: str

    # Derived regime features (inputs, not final regime labels)
    market_trend: str          # up | down | flat
    volatility_regime: str     # low | mid | high
    risk_on_off: str           # risk_on | risk_off | neutral


def _derive_market_trend(spy_ret: float, qqq_ret: float) -> str:
    r = 0.5 * (spy_ret + qqq_ret)
    if r > 0.0025:
        return "up"
    if r < -0.0025:
        return "down"
    return "flat"


def _derive_vol_regime(vxx: float, ratio: float) -> str:
    # Coarse, tradeable-proxy-based regime.
    # vxx level guard
    if vxx >= 35.0 or ratio >= 1.15:
        return "high"
    if vxx <= 18.0 and ratio <= 1.02:
        return "low"
    return "mid"


def _derive_risk_on_off(trend: str, vol_regime: str) -> str:
    if vol_regime == "high" and trend == "down":
        return "risk_off"
    if vol_regime == "low" and trend == "up":
        return "risk_on"
    return "neutral"


def _is_stale(last_ts: Optional[datetime], *, max_age_sec: int) -> bool:
    if not last_ts:
        return True
    age = (_now_utc() - last_ts).total_seconds()
    return age > float(max_age_sec)


@global_failure_wrapper("data")
def update_market_context_v2(api) -> Dict[str, Any]:
    """
    Update and persist market context snapshot.

    Returns a dict (safe for JSON) representing MarketContextV2.
    Never raises; failures are logged via global_failure_wrapper and system_events.
    """
    now = _now_utc()
    next_open, _next_close, is_open = _clock_window(api)

    # Staleness thresholds:
    # - during regular session, 1Min bars should be very fresh
    # - outside session, accept longer (premarket/overnight)
    max_age_sec = 10 * 60
    if is_open is True:
        max_age_sec = 5 * 60

    # Proxy symbols
    spy_prev_close, _ = _get_daily_close(api, "SPY", days=5)
    qqq_prev_close, _ = _get_daily_close(api, "QQQ", days=5)
    spy_last_1m, spy_last_ts = _get_last_bar_close(api, "SPY", limit=120)
    qqq_last_1m, qqq_last_ts = _get_last_bar_close(api, "QQQ", limit=120)

    # Volatility proxies (tradeable, Alpaca-available)
    vxx_close_1d, _ = _get_daily_close(api, "VXX", days=10)
    vxz_close_1d, _ = _get_daily_close(api, "VXZ", days=10)

    spy_prev_close_f = _safe_float(spy_prev_close)
    qqq_prev_close_f = _safe_float(qqq_prev_close)
    spy_last_1m_f = _safe_float(spy_last_1m)
    qqq_last_1m_f = _safe_float(qqq_last_1m)

    spy_overnight_ret = _pct_change(spy_prev_close_f, spy_last_1m_f)
    qqq_overnight_ret = _pct_change(qqq_prev_close_f, qqq_last_1m_f)

    vxx_f = _safe_float(vxx_close_1d)
    vxz_f = _safe_float(vxz_close_1d)
    ratio = (vxx_f / vxz_f) if vxz_f > 0 else 0.0

    stale_spy = _is_stale(spy_last_ts, max_age_sec=max_age_sec)
    stale_qqq = _is_stale(qqq_last_ts, max_age_sec=max_age_sec)
    stale_1m = bool(stale_spy or stale_qqq)

    stale_reason = ""
    if stale_1m:
        stale_reason = "missing_or_old_1m_bars"
        # Premarket contract: within 4h of open, we require some premarket awareness inputs.
        # If missing, log CRITICAL (observability + operator awareness).
        try:
            if next_open:
                hours_to_open = (next_open - now).total_seconds() / 3600.0
                if 0.0 <= hours_to_open <= 4.0:
                    log_system_event(
                        subsystem="data",
                        event_type="premarket_context_missing_or_stale",
                        severity="CRITICAL",
                        details={
                            "hours_to_open": round(hours_to_open, 2),
                            "spy_last_1m_ts": spy_last_ts.isoformat() if spy_last_ts else None,
                            "qqq_last_1m_ts": qqq_last_ts.isoformat() if qqq_last_ts else None,
                            "max_age_sec": int(max_age_sec),
                        },
                    )
        except Exception:
            pass

        # Always log a WARN for stale bar inputs (non-fatal; fail-safe).
        try:
            log_system_event(
                subsystem="data",
                event_type="market_context_stale",
                severity="WARN",
                details={
                    "spy_last_1m_ts": spy_last_ts.isoformat() if spy_last_ts else None,
                    "qqq_last_1m_ts": qqq_last_ts.isoformat() if qqq_last_ts else None,
                    "is_open": is_open,
                    "max_age_sec": int(max_age_sec),
                },
            )
        except Exception:
            pass

    trend = _derive_market_trend(spy_overnight_ret, qqq_overnight_ret)
    vol_regime = _derive_vol_regime(vxx_f, ratio)
    risk_on_off = _derive_risk_on_off(trend, vol_regime)

    ctx = MarketContextV2(
        timestamp=now.isoformat(),
        spy_prev_close=spy_prev_close_f,
        spy_last_1m=spy_last_1m_f,
        spy_overnight_ret=spy_overnight_ret,
        qqq_prev_close=qqq_prev_close_f,
        qqq_last_1m=qqq_last_1m_f,
        qqq_overnight_ret=qqq_overnight_ret,
        vxx_close_1d=vxx_f,
        vxz_close_1d=vxz_f,
        vxx_vxz_ratio=_safe_float(ratio),
        spy_last_1m_ts=spy_last_ts.isoformat() if spy_last_ts else None,
        qqq_last_1m_ts=qqq_last_ts.isoformat() if qqq_last_ts else None,
        stale_1m=stale_1m,
        stale_reason=stale_reason,
        market_trend=trend,
        volatility_regime=vol_regime,
        risk_on_off=risk_on_off,
    )

    payload = asdict(ctx)

    # Persist
    try:
        if StateFiles is not None and hasattr(StateFiles, "MARKET_CONTEXT_V2") and atomic_write_json is not None:
            atomic_write_json(StateFiles.MARKET_CONTEXT_V2, payload)  # type: ignore[attr-defined]
    except Exception as e:
        try:
            log_system_event(
                subsystem="data",
                event_type="market_context_persist_failed",
                severity="ERROR",
                details={"error": str(e)},
            )
        except Exception:
            pass

    # Emit a lightweight INFO event (observability; keep details bounded).
    try:
        log_system_event(
            subsystem="data",
            event_type="market_context_updated",
            severity="INFO",
            details={
                "market_trend": trend,
                "volatility_regime": vol_regime,
                "risk_on_off": risk_on_off,
                "spy_overnight_ret": round(spy_overnight_ret, 6),
                "qqq_overnight_ret": round(qqq_overnight_ret, 6),
                "vxx_vxz_ratio": round(_safe_float(ratio), 4),
                "stale_1m": stale_1m,
            },
        )
    except Exception:
        pass

    return payload


def read_market_context_v2(default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Read last persisted market context snapshot.
    Best-effort; never raises.
    """
    if default is None:
        default = {}
    try:
        if StateFiles is None or not hasattr(StateFiles, "MARKET_CONTEXT_V2") or read_json is None:
            return dict(default)
        path = StateFiles.MARKET_CONTEXT_V2  # type: ignore[attr-defined]
        data = read_json(path, default=default)
        return data if isinstance(data, dict) else dict(default)
    except Exception:
        return dict(default)

