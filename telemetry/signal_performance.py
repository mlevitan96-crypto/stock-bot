#!/usr/bin/env python3
"""
Signal Performance Telemetry (computed)
=====================================

Computes per-signal (feature-family) performance from realized trades.

Contract:
- Additive only; does not modify trading/scoring/exits.
- Uses existing regime labels when available; otherwise leaves breakdowns empty but present.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v: Any) -> float:
    try:
        if v is None:
            return 0.0
        return float(v)
    except Exception:
        return 0.0


def _safe_int(v: Any) -> int:
    try:
        if v is None:
            return 0
        return int(v)
    except Exception:
        return 0


def _perf_block(pnls: List[float]) -> Dict[str, Any]:
    n = int(len(pnls))
    if n <= 0:
        return {"win_rate": 0.0, "avg_pnl_usd": 0.0, "expectancy_usd": 0.0, "trade_count": 0}
    pnl_sum = float(sum(float(x) for x in pnls))
    wins = int(sum(1 for x in pnls if float(x) > 0.0))
    avg = float(pnl_sum / n) if n else 0.0
    return {
        "win_rate": float(wins / n) if n else 0.0,
        "avg_pnl_usd": float(avg),
        "expectancy_usd": float(avg),
        "trade_count": int(n),
    }


def _families_from_trade(trade: Dict[str, Any]) -> List[str]:
    """
    Best-effort: infer signal families from v2 UW adjustments snapshot at entry/exit.
    If missing, returns ["unknown"].
    """
    adjustments: Dict[str, Any] = {}
    try:
        snap = trade.get("entry_intel_snapshot") if isinstance(trade.get("entry_intel_snapshot"), dict) else None
        if snap is None:
            snap = trade.get("intel_snapshot") if isinstance(trade.get("intel_snapshot"), dict) else None
        if isinstance(snap, dict):
            adjustments = snap.get("v2_uw_adjustments") if isinstance(snap.get("v2_uw_adjustments"), dict) else {}
    except Exception:
        adjustments = {}

    fams: List[str] = []
    try:
        from telemetry.feature_families import active_v2_families_from_adjustments  # type: ignore

        fams = active_v2_families_from_adjustments(adjustments) or []
    except Exception:
        fams = []
    if not fams:
        return ["unknown"]
    return [str(x) for x in fams if str(x)]


def build_signal_performance(*, realized_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Structure:
    {
      "as_of_ts": "<ISO8601>",
      "signals": [
        {
          "name": "<signal_or_feature_family_name>",
          "win_rate": <number>,
          "avg_pnl_usd": <number>,
          "expectancy_usd": <number>,
          "trade_count": <int>,
          "long_short_breakdown": {...},
          "regime_breakdown": [...],
          "contribution_to_total_pnl": <number>
        }
      ]
    }
    """
    trades = [t for t in (realized_trades or []) if isinstance(t, dict)]
    total_pnl = float(sum(_safe_float(t.get("pnl_usd")) for t in trades))

    # Aggregate per family. A trade can contribute to multiple families (multi-label).
    fam_pnls: Dict[str, List[float]] = {}
    fam_long: Dict[str, List[float]] = {}
    fam_short: Dict[str, List[float]] = {}
    fam_reg: Dict[str, Dict[str, List[float]]] = {}
    fam_contrib_split_pnl: Dict[str, float] = {}

    for t in trades:
        pnl = float(_safe_float(t.get("pnl_usd")))
        side = str(t.get("side") or "").lower()
        reg = str(t.get("entry_regime") or t.get("exit_regime") or "").strip()

        fams = _families_from_trade(t)
        denom = float(len(fams)) if fams else 1.0
        split = float(pnl / denom) if denom > 0 else float(pnl)

        for fam in fams:
            fam_pnls.setdefault(fam, []).append(pnl)
            if side == "short":
                fam_short.setdefault(fam, []).append(pnl)
            else:
                fam_long.setdefault(fam, []).append(pnl)
            if reg:
                fam_reg.setdefault(fam, {}).setdefault(reg, []).append(pnl)
            fam_contrib_split_pnl[fam] = float(fam_contrib_split_pnl.get(fam, 0.0) + split)

    signals_out: List[Dict[str, Any]] = []
    for fam in sorted(fam_pnls.keys()):
        pnls = fam_pnls.get(fam, []) or []
        blk = _perf_block(pnls)
        long_blk = _perf_block(fam_long.get(fam, []) or [])
        short_blk = _perf_block(fam_short.get(fam, []) or [])

        regimes = fam_reg.get(fam, {}) if isinstance(fam_reg.get(fam), dict) else {}
        regime_breakdown: List[Dict[str, Any]] = []
        for reg_name, rp in sorted(regimes.items(), key=lambda kv: kv[0]):
            rpnls = rp if isinstance(rp, list) else []
            rb = _perf_block([float(_safe_float(x)) for x in rpnls])
            regime_breakdown.append(
                {
                    "regime": str(reg_name),
                    "expectancy_usd": float(rb.get("expectancy_usd") or 0.0),
                    "trade_count": int(rb.get("trade_count") or 0),
                }
            )

        contrib = float(fam_contrib_split_pnl.get(fam, 0.0))
        contrib_to_total = float(contrib / total_pnl) if total_pnl != 0.0 else 0.0

        signals_out.append(
            {
                "name": str(fam),
                "win_rate": float(blk["win_rate"]),
                "avg_pnl_usd": float(blk["avg_pnl_usd"]),
                "expectancy_usd": float(blk["expectancy_usd"]),
                "trade_count": int(blk["trade_count"]),
                "long_short_breakdown": {
                    "long": {
                        "win_rate": float(long_blk["win_rate"]),
                        "expectancy_usd": float(long_blk["expectancy_usd"]),
                        "trade_count": int(long_blk["trade_count"]),
                    },
                    "short": {
                        "win_rate": float(short_blk["win_rate"]),
                        "expectancy_usd": float(short_blk["expectancy_usd"]),
                        "trade_count": int(short_blk["trade_count"]),
                    },
                },
                "regime_breakdown": regime_breakdown,
                "contribution_to_total_pnl": float(contrib_to_total),
            }
        )

    return {"as_of_ts": _now_iso(), "signals": signals_out}

