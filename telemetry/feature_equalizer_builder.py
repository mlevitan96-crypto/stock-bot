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


def _exit_inputs(attrib: Dict[str, Any]) -> Dict[str, Any]:
    exit_uw = attrib.get("exit_uw") if isinstance(attrib.get("exit_uw"), dict) else {}
    inputs = exit_uw.get("v2_uw_inputs") if isinstance(exit_uw.get("v2_uw_inputs"), dict) else {}
    return inputs if isinstance(inputs, dict) else {}


def _basic_stats(xs: List[float]) -> Dict[str, Any]:
    if not xs:
        return {}
    ys = sorted(float(x) for x in xs)
    n = len(ys)
    mean = sum(ys) / float(n) if n else 0.0
    med = ys[n // 2] if (n % 2 == 1) else (ys[n // 2 - 1] + ys[n // 2]) / 2.0

    def pct(p: float) -> float:
        if n == 1:
            return ys[0]
        i = int(round((p / 100.0) * (n - 1)))
        i = max(0, min(n - 1, i))
        return ys[i]

    return {"n": n, "min": ys[0], "p25": pct(25), "p50": pct(50), "p75": pct(75), "max": ys[-1], "mean": mean, "median": med}


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
        # Additional diagnostics requested by promotion readiness:
        # - score evolution curves
        # - volatility expansion curves
        # - regime/sector alignment drift
        # - feature contribution decay curves
        score_evolution_points: List[Dict[str, Any]] = []
        vol_expansion_points: List[Dict[str, Any]] = []
        drift_regime_alignment: List[float] = []
        drift_sector_alignment: List[float] = []
        per_feature_decay: Dict[str, List[float]] = defaultdict(list)
        exit_reason_by_sector: Dict[str, Counter] = defaultdict(Counter)
        exit_reason_by_regime: Dict[str, Counter] = defaultdict(Counter)
        exit_reason_by_feature_cluster: Dict[str, Counter] = defaultdict(Counter)

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

            # Score evolution curve point
            tmin = _safe_float(t.get("time_in_trade_minutes"))
            tmin_n = float(tmin) if tmin is not None else 0.0
            ev = _safe_float(t.get("entry_v2_score"))
            xv = _safe_float(t.get("exit_v2_score"))
            if ev is not None and xv is not None:
                score_evolution_points.append(
                    {
                        "time_in_trade_minutes": tmin_n,
                        "entry_v2_score": float(ev),
                        "exit_v2_score": float(xv),
                        "delta_v2_score": float(ev) - float(xv),
                        "pnl_usd": pnl,
                        "side": side,
                    }
                )
            if vol_exp is not None:
                vol_expansion_points.append({"time_in_trade_minutes": tmin_n, "vol_expansion": float(vol_exp), "pnl_usd": pnl, "side": side})

            # Alignment drift (entry vs exit)
            ent_inputs = _entry_inputs(attrib)
            ex_inputs = _exit_inputs(attrib)
            ra0 = _safe_float(ent_inputs.get("regime_alignment"))
            ra1 = _safe_float(ex_inputs.get("regime_alignment"))
            sa0 = _safe_float(ent_inputs.get("sector_alignment"))
            sa1 = _safe_float(ex_inputs.get("sector_alignment"))
            if ra0 is not None and ra1 is not None:
                drift_regime_alignment.append(float(ra1 - ra0))
            if sa0 is not None and sa1 is not None:
                drift_sector_alignment.append(float(sa1 - sa0))

            # Feature adjustment decay (exit_adj - entry_adj)
            ent_adj = _entry_adjustments(attrib)
            ex_adj = _exit_adjustments(attrib)
            for feat in FEATURE_KEYS:
                a0 = _safe_float(ent_adj.get(feat))
                a1 = _safe_float(ex_adj.get(feat))
                if a0 is not None and a1 is not None:
                    per_feature_decay[feat].append(float(a1 - a0))

            # Exit reason distributions by sector/regime/feature cluster
            reason = _safe_str(t.get("exit_reason") or "")
            sector = _safe_str(t.get("entry_sector") or "UNKNOWN") or "UNKNOWN"
            regime = _safe_str(t.get("entry_regime") or "")
            cluster = "+".join(sorted(active)) if active else "(none)"
            exit_reason_by_sector[sector][reason] += 1
            exit_reason_by_regime[regime][reason] += 1
            exit_reason_by_feature_cluster[cluster][reason] += 1

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
                "win_rate": (int(st["win"]) / float(cnt)) if cnt else 0.0,
                "total_pnl_usd": tot,
                "avg_pnl_usd": (tot / float(cnt)) if cnt else 0.0,
                "by_side": {
                    s: {
                        "count": int(st["by_side"][s]["count"]),
                        "total_pnl_usd": float(st["by_side"][s]["total_pnl_usd"]),
                        "avg_pnl_usd": (float(st["by_side"][s]["total_pnl_usd"]) / float(st["by_side"][s]["count"])) if st["by_side"][s]["count"] else 0.0,
                        "win_rate": (int(st["by_side"][s]["win"]) / float(st["by_side"][s]["count"])) if st["by_side"][s]["count"] else 0.0,
                    }
                    for s in ("long", "short")
                },
            }

        out_exit: Dict[str, Any] = {}
        for feat, st in per_feature_exit.items():
            out_exit[feat] = {
                "count": int(st["count"]),
                "avg_v2_exit_score": (float(st["avg_v2_exit_score_sum"]) / float(st["avg_v2_exit_score_n"])) if st["avg_v2_exit_score_n"] else 0.0,
                "avg_score_deterioration": (float(st["avg_score_det_sum"]) / float(st["avg_score_det_n"])) if st["avg_score_det_n"] else 0.0,
                "avg_relative_strength_deterioration": (float(st["avg_rs_det_sum"]) / float(st["avg_rs_det_n"])) if st["avg_rs_det_n"] else 0.0,
                "avg_vol_expansion": (float(st["avg_vol_exp_sum"]) / float(st["avg_vol_exp_n"])) if st["avg_vol_exp_n"] else 0.0,
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
            "exit_reason_distributions": {
                "by_sector": {k: dict(v) for k, v in exit_reason_by_sector.items()},
                "by_regime": {k: dict(v) for k, v in exit_reason_by_regime.items()},
                "by_feature_cluster": {k: dict(v) for k, v in exit_reason_by_feature_cluster.items()},
            },
            "score_evolution": {
                "points": score_evolution_points[:500],
                "delta_stats": _basic_stats([float(p.get("delta_v2_score")) for p in score_evolution_points if p.get("delta_v2_score") is not None]),
            },
            "volatility_expansion": {
                "points": vol_expansion_points[:500],
                "vol_expansion_stats": _basic_stats([float(p.get("vol_expansion")) for p in vol_expansion_points if p.get("vol_expansion") is not None]),
            },
            "alignment_drift": {
                "regime_alignment_drift_stats": _basic_stats(drift_regime_alignment),
                "sector_alignment_drift_stats": _basic_stats(drift_sector_alignment),
            },
            "feature_contribution_decay": {k: {"delta_stats": _basic_stats(v)} for k, v in per_feature_decay.items()},
            "replacement_telemetry": {
                "replacement_exit_count": len(repl),
                "replacement_total_pnl_usd": sum(repl_pnls) if repl_pnls else 0.0,
                "non_replacement_exit_count": len(non_repl),
                "non_replacement_total_pnl_usd": sum(non_repl_pnls) if non_repl_pnls else 0.0,
            },
        }
    except Exception as e:
        return {"_meta": {"date": str(day), "kind": "feature_equalizer", "version": "2026-01-22_v1"}, "error": str(e)}

