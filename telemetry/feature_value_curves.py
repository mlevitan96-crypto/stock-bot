#!/usr/bin/env python3
"""
Feature value curves (v2 shadow, read-only)
=========================================

Produces binned/quantiled curves mapping feature strength to realized PnL.

Contract:
- Read-only, side-effect free.
- Never raises on malformed input.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


FEATURE_INPUT_KEYS = [
    "flow_strength",
    "darkpool_bias",
    "sentiment",
    "earnings_proximity",
    "sector_alignment",
    "regime_alignment",
]


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _safe_str(v: Any) -> str:
    return str(v or "")


def _side(rec: Dict[str, Any]) -> str:
    s = str(rec.get("side", "") or "").lower()
    if s in ("long", "short"):
        return s
    d = str(rec.get("direction", "") or "").lower()
    return "short" if d in ("bearish", "short", "sell") else "long"


def _extract_feature_value(attrib: Dict[str, Any], feature: str) -> Optional[float]:
    """
    Prefer entry_uw.v2_uw_inputs[feature] if numeric.
    If not numeric and feature is sentiment, map BULLISH/BEARISH/NEUTRAL to +1/-1/0.
    """
    entry_uw = attrib.get("entry_uw") if isinstance(attrib.get("entry_uw"), dict) else {}
    inputs = entry_uw.get("v2_uw_inputs") if isinstance(entry_uw.get("v2_uw_inputs"), dict) else {}
    v = inputs.get(feature)
    f = _safe_float(v)
    if f is not None:
        return f
    if feature == "sentiment":
        s = _safe_str(v).upper()
        if s == "BULLISH":
            return 1.0
        if s == "BEARISH":
            return -1.0
        if s == "NEUTRAL":
            return 0.0
    return None


def _quantile_bins(xs: List[float], *, bins: int) -> List[Tuple[float, float]]:
    if not xs or bins <= 0:
        return []
    xs2 = sorted(xs)
    n = len(xs2)
    out: List[Tuple[float, float]] = []
    for i in range(bins):
        a = int(round((i / bins) * (n - 1)))
        b = int(round(((i + 1) / bins) * (n - 1)))
        a = max(0, min(n - 1, a))
        b = max(0, min(n - 1, b))
        lo = xs2[min(a, b)]
        hi = xs2[max(a, b)]
        out.append((lo, hi))
    # de-dup contiguous identical bins
    out2: List[Tuple[float, float]] = []
    for lo, hi in out:
        if out2 and out2[-1] == (lo, hi):
            continue
        out2.append((lo, hi))
    return out2


def _bin_stats(points: List[Tuple[float, float]], bins: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
    # points: (x, pnl)
    out: List[Dict[str, Any]] = []
    for lo, hi in bins:
        ys = [pnl for (x, pnl) in points if (x >= lo and x <= hi)]
        if not ys:
            out.append({"x_lo": lo, "x_hi": hi, "count": 0, "avg_pnl_usd": None, "total_pnl_usd": 0.0})
            continue
        out.append(
            {
                "x_lo": lo,
                "x_hi": hi,
                "count": len(ys),
                "avg_pnl_usd": sum(ys) / float(len(ys)),
                "total_pnl_usd": sum(ys),
            }
        )
    return out


def build_feature_value_curves(
    *,
    day: str,
    realized_trades: List[Dict[str, Any]],
    bins: int = 8,
) -> Dict[str, Any]:
    try:
        realized = [t for t in (realized_trades or []) if isinstance(t, dict)]
        # Use exit_attribution when available (it contains entry_uw/exit_uw)
        points_by_feature: Dict[str, List[Tuple[float, float]]] = {k: [] for k in FEATURE_INPUT_KEYS}
        points_by_feature_side: Dict[str, Dict[str, List[Tuple[float, float]]]] = {k: {"long": [], "short": []} for k in FEATURE_INPUT_KEYS}

        for t in realized:
            pnl = _safe_float(t.get("pnl_usd"))
            if pnl is None:
                continue
            attrib = t.get("exit_attribution") if isinstance(t.get("exit_attribution"), dict) else {}
            side = _side(t)
            for feat in FEATURE_INPUT_KEYS:
                x = _extract_feature_value(attrib, feat)
                if x is None:
                    continue
                points_by_feature[feat].append((float(x), float(pnl)))
                points_by_feature_side[feat][side].append((float(x), float(pnl)))

        curves: Dict[str, Any] = {}
        for feat, pts in points_by_feature.items():
            xs = [x for (x, _p) in pts]
            b = _quantile_bins(xs, bins=bins) if xs else []
            curves[feat] = {
                "bins": bins,
                "overall": _bin_stats(pts, b) if b else [],
                "long": _bin_stats(points_by_feature_side[feat]["long"], b) if b else [],
                "short": _bin_stats(points_by_feature_side[feat]["short"], b) if b else [],
                "point_count": len(pts),
            }

        return {
            "_meta": {"date": str(day), "kind": "feature_value_curves", "version": "2026-01-22_v1", "bins": int(bins)},
            "features": curves,
        }
    except Exception as e:
        return {"_meta": {"date": str(day), "kind": "feature_value_curves", "version": "2026-01-22_v1"}, "error": str(e)}

