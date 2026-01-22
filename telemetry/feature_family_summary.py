"""
Feature family summary (telemetry-only)
======================================

Aggregates parity + realized trade outcomes by feature family.

Contract:
- Read-only.
- Always emits non-empty family blocks (even if counts are zero).
"""

from __future__ import annotations

from typing import Any, Dict, List

from telemetry.feature_families import FEATURE_FAMILIES, FAMILY_UNKNOWN, active_v2_families_from_adjustments


def _mean(xs: List[float]) -> float:
    return float(sum(xs) / float(len(xs))) if xs else 0.0


def _var(xs: List[float]) -> float:
    if not xs:
        return 0.0
    m = _mean(xs)
    return float(sum((x - m) ** 2 for x in xs) / float(len(xs)))


def build_feature_family_summary(
    *,
    day: str,
    entry_parity_rows: List[Dict[str, Any]],
    realized_trades: List[Dict[str, Any]],
) -> Dict[str, Any]:
    # Parity deltas per family (and per side)
    parity_by_family: Dict[str, Dict[str, List[float]]] = {f: {"overall": [], "long": [], "short": []} for f in FEATURE_FAMILIES}
    if FAMILY_UNKNOWN not in parity_by_family:
        parity_by_family[FAMILY_UNKNOWN] = {"overall": [], "long": [], "short": []}

    for r in entry_parity_rows or []:
        if not isinstance(r, dict):
            continue
        fam = str(r.get("feature_family") or FAMILY_UNKNOWN)
        if fam not in parity_by_family:
            fam = FAMILY_UNKNOWN
        delta = float(r.get("score_delta") or 0.0)
        parity_by_family[fam]["overall"].append(delta)
        side = str(r.get("v1_side") or r.get("v2_side") or "").lower()
        if side in ("long", "short"):
            parity_by_family[fam][side].append(delta)

    # Realized trade PnL per family (v2), using entry_uw adjustments when available.
    pnl_by_family: Dict[str, List[float]] = {f: [] for f in FEATURE_FAMILIES}
    if FAMILY_UNKNOWN not in pnl_by_family:
        pnl_by_family[FAMILY_UNKNOWN] = []

    for t in realized_trades or []:
        if not isinstance(t, dict):
            continue
        pnl = float(t.get("pnl_usd") or 0.0)
        attrib = t.get("exit_attribution") if isinstance(t.get("exit_attribution"), dict) else {}
        entry_uw = attrib.get("entry_uw") if isinstance(attrib.get("entry_uw"), dict) else {}
        adjs = entry_uw.get("v2_uw_adjustments") if isinstance(entry_uw.get("v2_uw_adjustments"), dict) else {}
        fams = active_v2_families_from_adjustments(adjs) if adjs else set()
        if not fams:
            pnl_by_family[FAMILY_UNKNOWN].append(pnl)
        else:
            for fam in fams:
                if fam not in pnl_by_family:
                    pnl_by_family[FAMILY_UNKNOWN].append(pnl)
                else:
                    pnl_by_family[fam].append(pnl)

    families_out: Dict[str, Any] = {}
    for fam in FEATURE_FAMILIES:
        deltas_all = parity_by_family.get(fam, {}).get("overall", []) if fam in parity_by_family else []
        deltas_long = parity_by_family.get(fam, {}).get("long", []) if fam in parity_by_family else []
        deltas_short = parity_by_family.get(fam, {}).get("short", []) if fam in parity_by_family else []
        pnl = pnl_by_family.get(fam, [])

        mean_delta = _mean(deltas_all)
        var_delta = _var(deltas_all)
        skew = _mean(deltas_long) - _mean(deltas_short)
        stability = 1.0 / (1.0 + var_delta) if var_delta >= 0 else 0.0

        families_out[fam] = {
            "counts": {
                "parity_rows": int(len(deltas_all)),
                "parity_rows_long": int(len(deltas_long)),
                "parity_rows_short": int(len(deltas_short)),
                "realized_trades": int(len(pnl)),
            },
            "mean_value": float(mean_delta),
            "variance": float(var_delta),
            "long_short_skew": float(skew),
            "ev_contribution": float(_mean(pnl)),
            "stability_score": float(stability),
        }

    return {
        "_meta": {"date": str(day), "kind": "feature_family_summary", "version": "2026-01-22_v1"},
        "families": families_out,
        "notes": {
            "mean_value": "mean score_delta (v2 - v1) for entry parity rows in family",
            "ev_contribution": "avg realized pnl_usd for trades where family is active at entry (v2, best-effort)",
        },
    }

