"""
Offense entry gate: relative strength vs SPY (5m) when possible; else strict price > session VWAP.

Uses Alpaca REST ``get_bars`` only (no import from ``main``). Fail-closed on buy when neither check passes.
"""
from __future__ import annotations

import os
from typing import Any, Optional, Tuple


def _closes_from_bars(bars: Any, n: int = 3) -> Optional[list]:
    if bars is None:
        return None
    try:
        df = getattr(bars, "df", None)
        if df is not None and len(df) > 0 and "close" in df.columns:
            seq = [float(x) for x in df["close"].tolist()[-n:]]
            return seq if len(seq) >= 2 else None
    except Exception:
        pass
    try:
        bl = list(bars)
        if len(bl) < 2:
            return None
        out = []
        for b in bl[-n:]:
            c = getattr(b, "c", None) or getattr(b, "close", None)
            if c is not None:
                out.append(float(c))
        return out if len(out) >= 2 else None
    except Exception:
        return None


def _session_vwap_from_1m(bars: Any) -> Optional[float]:
    """Typical-price VWAP from 1-minute bars (current session in ``limit`` window)."""
    if bars is None:
        return None
    try:
        df = getattr(bars, "df", None)
        if df is None or len(df) == 0:
            return None
        h = df["high"].astype(float)
        l = df["low"].astype(float)
        c = df["close"].astype(float)
        v = df["volume"].astype(float) if "volume" in df.columns else None
        if v is None:
            return None
        tp = (h + l + c) / 3.0
        vol = v.sum()
        if vol <= 0:
            return None
        return float((tp * v).sum() / vol)
    except Exception:
        return None


def check_offense_entry_gate(api: Any, symbol: str, ref_price: float, side: str) -> Tuple[bool, str]:
    """
    Returns (allowed, reason). Short / non-buy always allowed here.
    Buy: require RS vs SPY on 5m when both series exist; else require ref_price > session VWAP from 1m bars.
    """
    if str(side).lower() != "buy":
        return True, "offense_gate_skipped_non_buy"
    if str(os.environ.get("OFFENSE_ENTRY_GATE_ENABLED", "1")).strip().lower() not in ("1", "true", "yes", "on"):
        return True, "offense_gate_disabled"

    sym = str(symbol).upper()
    bench = str(os.environ.get("OFFENSE_RS_BENCHMARK", "SPY")).upper()
    try:
        rp = float(ref_price)
        if not (rp == rp) or rp <= 0:
            return False, "offense_gate_bad_ref_price"
    except (TypeError, ValueError):
        return False, "offense_gate_bad_ref_price"

    # 1) Relative strength: last bar vs first in window (5m)
    try:
        b_sym = api.get_bars(sym, "5Min", limit=4)
        b_bench = api.get_bars(bench, "5Min", limit=4)
        c_sym = _closes_from_bars(b_sym, n=4)
        c_bench = _closes_from_bars(b_bench, n=4)
        if c_sym and c_bench and len(c_sym) >= 2 and len(c_bench) >= 2:
            r_sym = (c_sym[-1] - c_sym[0]) / c_sym[0] if c_sym[0] else 0.0
            r_bench = (c_bench[-1] - c_bench[0]) / c_bench[0] if c_bench[0] else 0.0
            if r_sym > r_bench:
                return True, "offense_gate_relative_strength_ok"
    except Exception:
        pass

    # 2) Strict VWAP fallback
    try:
        b1 = api.get_bars(sym, "1Min", limit=int(os.environ.get("OFFENSE_VWAP_BAR_LIMIT", "120")))
        vwap = _session_vwap_from_1m(b1)
        if vwap is not None and rp > float(vwap):
            return True, "offense_gate_above_vwap"
    except Exception:
        pass

    return False, "offense_gate_blocked_rs_and_vwap"
