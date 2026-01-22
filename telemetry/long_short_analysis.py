#!/usr/bin/env python3
"""
Long/Short asymmetry analysis (v2 shadow, read-only)
===================================================

Computes basic long vs short expectancy metrics from realized (closed) shadow trades.

Contract:
- Read-only, side-effect free.
- Never raises on malformed input.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _side(rec: Dict[str, Any]) -> str:
    s = str(rec.get("side", "") or "").lower()
    if s in ("short", "long"):
        return s
    # fallback to direction if present
    d = str(rec.get("direction", "") or "").lower()
    return "short" if d in ("bearish", "short", "sell") else "long"


def _compute_group(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    pnls = [float(p) for p in (_safe_float(t.get("pnl_usd")) for t in trades) if p is not None]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    n = len(pnls)
    win_rate = (len(wins) / float(n)) if n else 0.0
    avg_pnl = (sum(pnls) / float(n)) if n else 0.0
    avg_win = (sum(wins) / float(len(wins))) if wins else 0.0
    avg_loss = (sum(losses) / float(len(losses))) if losses else 0.0
    expectancy = (win_rate * avg_win) + ((1.0 - win_rate) * avg_loss) if n else 0.0
    return {
        "count": n,
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate": win_rate,
        "avg_pnl_usd": avg_pnl,
        "avg_win_usd": avg_win,
        "avg_loss_usd": avg_loss,
        "expectancy_usd": expectancy,
        "total_pnl_usd": sum(pnls) if pnls else 0.0,
    }


def build_long_short_analysis(*, day: str, realized_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        realized = [t for t in (realized_trades or []) if isinstance(t, dict) and _safe_float(t.get("pnl_usd")) is not None]
        longs = [t for t in realized if _side(t) == "long"]
        shorts = [t for t in realized if _side(t) == "short"]
        return {
            "_meta": {"date": str(day), "kind": "long_short_analysis", "version": "2026-01-22_v1"},
            "overall": _compute_group(realized),
            "long": _compute_group(longs),
            "short": _compute_group(shorts),
        }
    except Exception as e:
        return {"_meta": {"date": str(day), "kind": "long_short_analysis", "version": "2026-01-22_v1"}, "error": str(e)}

