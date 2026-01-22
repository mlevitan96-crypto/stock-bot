#!/usr/bin/env python3
"""
Feature equalizer builder (v2 shadow, read-only)
==============================================

Builds equalizer-ready per-feature attribution → realized outcome summaries.

This does NOT modify any weights; it only produces telemetry that can be used to
design per-feature value curves / equalizer knobs offline.

Contract:
- Read-only, side-effect free.
- Never raises on malformed input.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional


FEATURE_KEYS = [
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


def _entry_inputs(attrib: Dict[str, Any]) -> Dict[str, Any]:
    entry_uw = attrib.get("entry_uw") if isinstance(attrib.get("entry_uw"), dict) else {}
    inputs = entry_uw.get("v2_uw_inputs") if isinstance(entry_uw.get("v2_uw_inputs"), dict) else {}
    return inputs if isinstance(inputs, dict) else {}


def _entry_adjustments(attrib: Dict[str, Any]) -> Dict[str, Any]:
    entry_uw = attrib.get("entry_uw") if isinstance(attrib.get("entry_uw"), dict) else {}
    adj = entry_uw.get("v2_uw_adjustments") if isinstance(entry_uw.get("v2_uw_adjustments"), dict) else {}
    return adj if isinstance(adj, dict) else {}


def _exit_adjustments(attrib: Dict[str, Any]) -> Dict[str, Any]:
    exit_uw = attrib.get("exit_uw") if isinstance(attrib.get("exit_uw"), dict) else {}
    adj = exit_uw.get("v2_uw_adjustments") if isinstance(exit_uw.get("v2_uw_adjustments"), dict) else {}
    return adj if isinstance(adj, dict) else {}


def _active_features(attrib: Dict[str, Any]) -> List[str]:
    """
    Feature is considered active if entry adjustment abs(value) > 0.
    (Best-effort; avoids tying to future weight implementations.)
    """
    adj = _entry_adjustments(attrib)
    out: List[str] = []
    for k in FEATURE_KEYS:
        v = _safe_float(adj.get(k))
        if v is not None and abs(v) > 1e-9:
            out.append(k)
    return out


def build_feature_equalizer(*, day: str, realized_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        realized = [t for t in (realized_trades or []) if isinstance(t, dict) and _safe_float(t.get("pnl_usd")) is not None]

        per_feature = defaultdict(lambda: {"count": 0, "win": 0, "loss": 0, "total_pnl_usd": 0.0, "by_side": {"long": {"count": 0, "total_pnl_usd": 0.0, "win": 0, "loss": 0}, "short": {"count": 0, "total_pnl_usd": 0.0, "win": 0, "loss": 0}}})
        per_feature_exit = defaultdict(lambda: {"count": 0, "avg_v2_exit_score_sum": 0.0, "avg_v2_exit_score_n": 0, "avg_score_det_sum": 0.0, "avg_score_det_n": 0, "avg_rs_det_sum": 0.0, "avg_rs_det_n": 0, "avg_vol_exp_sum": 0.0, "avg_vol_exp_n": 0})
        feature_clusters = Counter()

        for t in realized:
            pnl = float(_safe_float(t.get("pnl_usd")) or 0.0)
            side = _side(t)
            attrib = t.get("exit_attribution") if isinstance(t.get("exit_attribution"), dict) else {}
            active = _active_features(attrib)
            if active:
                feature_clusters["+".join(sorted(active))] += 1

            # Exit impact inputs
            v2_exit_score = _safe_float((attrib.get("v2_exit_score") if isinstance(attrib, dict) else None) or t.get("v2_exit_score"))
            score_det = _safe_float((attrib.get("score_deterioration") if isinstance(attrib, dict) else None))
            rs_det = _safe_float((attrib.get("relative_strength_deterioration") if isinstance(attrib, dict) else None))
            comps = attrib.get("v2_exit_components") if isinstance(attrib.get("v2_exit_components"), dict) else {}
            vol_exp = _safe_float(comps.get("vol_expansion"))

            for feat in active:
                pf = per_feature[feat]
                pf["count"] += 1
                pf["total_pnl_usd"] += pnl
                if pnl > 0:
                    pf["win"] += 1
                elif pnl < 0:
                    pf["loss"] += 1

                ps = pf["by_side"][side]
                ps["count"] += 1
                ps["total_pnl_usd"] += pnl
                if pnl > 0:
                    ps["win"] += 1
                elif pnl < 0:
                    ps["loss"] += 1

                pe = per_feature_exit[feat]
                pe["count"] += 1
                if v2_exit_score is not None:
                    pe["avg_v2_exit_score_sum"] += float(v2_exit_score)
                    pe["avg_v2_exit_score_n"] += 1
                if score_det is not None:
                    pe["avg_score_det_sum"] += float(score_det)
                    pe["avg_score_det_n"] += 1
                if rs_det is not None:
                    pe["avg_rs_det_sum"] += float(rs_det)
                    pe["avg_rs_det_n"] += 1
                if vol_exp is not None:
                    pe["avg_vol_exp_sum"] += float(vol_exp)
                    pe["avg_vol_exp_n"] += 1

        # finalize per-feature stats
        out_features: Dict[str, Any] = {}
        for feat, st in per_feature.items():
            cnt = int(st["count"])
            tot = float(st["total_pnl_usd"])
            out_features[feat] = {
                "count": cnt,
                "win": int(st["win"]),
                "loss": int(st["loss"]),
                "win_rate": (int(st["win"]) / float(cnt)) if cnt else None,
                "total_pnl_usd": tot,
                "avg_pnl_usd": (tot / float(cnt)) if cnt else None,
                "by_side": {
                    s: {
                        "count": int(st["by_side"][s]["count"]),
                        "total_pnl_usd": float(st["by_side"][s]["total_pnl_usd"]),
                        "avg_pnl_usd": (float(st["by_side"][s]["total_pnl_usd"]) / float(st["by_side"][s]["count"])) if st["by_side"][s]["count"] else None,
                        "win_rate": (int(st["by_side"][s]["win"]) / float(st["by_side"][s]["count"])) if st["by_side"][s]["count"] else None,
                    }
                    for s in ("long", "short")
                },
            }

        out_exit: Dict[str, Any] = {}
        for feat, st in per_feature_exit.items():
            out_exit[feat] = {
                "count": int(st["count"]),
                "avg_v2_exit_score": (float(st["avg_v2_exit_score_sum"]) / float(st["avg_v2_exit_score_n"])) if st["avg_v2_exit_score_n"] else None,
                "avg_score_deterioration": (float(st["avg_score_det_sum"]) / float(st["avg_score_det_n"])) if st["avg_score_det_n"] else None,
                "avg_relative_strength_deterioration": (float(st["avg_rs_det_sum"]) / float(st["avg_rs_det_n"])) if st["avg_rs_det_n"] else None,
                "avg_vol_expansion": (float(st["avg_vol_exp_sum"]) / float(st["avg_vol_exp_n"])) if st["avg_vol_exp_n"] else None,
            }

        # Replacement telemetry (best-effort)
        repl = [t for t in realized if t.get("replacement_candidate")]
        repl_pnls = [float(_safe_float(t.get("pnl_usd")) or 0.0) for t in repl]
        non_repl = [t for t in realized if not t.get("replacement_candidate")]
        non_repl_pnls = [float(_safe_float(t.get("pnl_usd")) or 0.0) for t in non_repl]

        return {
            "_meta": {"date": str(day), "kind": "feature_equalizer", "version": "2026-01-22_v1"},
            "features": out_features,
            "feature_exit_impact": out_exit,
            "feature_cluster_counts": dict(feature_clusters),
            "replacement_telemetry": {
                "replacement_exit_count": len(repl),
                "replacement_total_pnl_usd": sum(repl_pnls) if repl_pnls else 0.0,
                "non_replacement_exit_count": len(non_repl),
                "non_replacement_total_pnl_usd": sum(non_repl_pnls) if non_repl_pnls else 0.0,
            },
        }
    except Exception as e:
        return {"_meta": {"date": str(day), "kind": "feature_equalizer", "version": "2026-01-22_v1"}, "error": str(e)}

