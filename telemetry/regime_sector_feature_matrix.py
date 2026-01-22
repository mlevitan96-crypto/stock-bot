#!/usr/bin/env python3
"""
Regime/Sector feature matrix (v2 shadow, read-only)
==================================================

Builds a best-effort matrix of (regime, sector) → per-feature realized PnL summaries.

Contract:
- Read-only, side-effect free.
- Never raises on malformed input.
"""

from __future__ import annotations

from collections import defaultdict
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


def _extract_inputs(attrib: Dict[str, Any]) -> Dict[str, Any]:
    entry_uw = attrib.get("entry_uw") if isinstance(attrib.get("entry_uw"), dict) else {}
    inputs = entry_uw.get("v2_uw_inputs") if isinstance(entry_uw.get("v2_uw_inputs"), dict) else {}
    return inputs if isinstance(inputs, dict) else {}


def build_regime_sector_feature_matrix(*, day: str, realized_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        # matrix[(regime, sector)][feature] -> stats accumulators
        cell = defaultdict(lambda: defaultdict(lambda: {"count": 0, "total_pnl_usd": 0.0, "avg_input_sum": 0.0, "avg_input_count": 0}))
        cell_total = defaultdict(lambda: {"count": 0, "total_pnl_usd": 0.0})

        for t in realized_trades or []:
            if not isinstance(t, dict):
                continue
            pnl = _safe_float(t.get("pnl_usd"))
            if pnl is None:
                continue
            regime = _safe_str(t.get("entry_regime") or "")
            sector = _safe_str(t.get("entry_sector") or "UNKNOWN") or "UNKNOWN"
            key = (regime, sector)
            attrib = t.get("exit_attribution") if isinstance(t.get("exit_attribution"), dict) else {}
            inputs = _extract_inputs(attrib)

            cell_total[key]["count"] += 1
            cell_total[key]["total_pnl_usd"] += float(pnl)

            for feat in FEATURE_KEYS:
                v = inputs.get(feat)
                # sentiment may be string; keep numeric only for avg_input
                fv = _safe_float(v)
                cell[key][feat]["count"] += 1
                cell[key][feat]["total_pnl_usd"] += float(pnl)
                if fv is not None:
                    cell[key][feat]["avg_input_sum"] += float(fv)
                    cell[key][feat]["avg_input_count"] += 1

        out: Dict[str, Any] = {}
        for (regime, sector), feats in cell.items():
            rk = regime or ""
            sk = sector or "UNKNOWN"
            out.setdefault(rk, {})
            out[rk].setdefault(sk, {"_cell": {}, "features": {}})
            out[rk][sk]["_cell"] = {
                "count": cell_total[(regime, sector)]["count"],
                "total_pnl_usd": cell_total[(regime, sector)]["total_pnl_usd"],
                "avg_pnl_usd": (cell_total[(regime, sector)]["total_pnl_usd"] / float(cell_total[(regime, sector)]["count"])) if cell_total[(regime, sector)]["count"] else None,
            }
            for feat, st in feats.items():
                cnt = int(st.get("count") or 0)
                tot = float(st.get("total_pnl_usd") or 0.0)
                out[rk][sk]["features"][feat] = {
                    "count": cnt,
                    "total_pnl_usd": tot,
                    "avg_pnl_usd": (tot / float(cnt)) if cnt else None,
                    "avg_input": (float(st.get("avg_input_sum") or 0.0) / float(st.get("avg_input_count") or 1)) if (st.get("avg_input_count") or 0) else None,
                }

        return {
            "_meta": {"date": str(day), "kind": "regime_sector_feature_matrix", "version": "2026-01-22_v1"},
            "matrix": out,
        }
    except Exception as e:
        return {"_meta": {"date": str(day), "kind": "regime_sector_feature_matrix", "version": "2026-01-22_v1"}, "error": str(e)}

