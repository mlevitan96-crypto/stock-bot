"""
Replacement telemetry (expanded) (telemetry-only)
================================================

Analyzes v2 shadow replacement exits with per-feature / per-family rates.

Contract:
- Read-only.
- Best-effort: missing attribution/adjustments fall back to "unknown".
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

from telemetry.feature_families import FAMILY_UNKNOWN, v2_family_for_key


def _absf(v: Any) -> float:
    try:
        return abs(float(v))
    except Exception:
        return 0.0


def _get_entry_adjustments(trade: Dict[str, Any]) -> Dict[str, Any]:
    attrib = trade.get("exit_attribution") if isinstance(trade.get("exit_attribution"), dict) else {}
    entry_uw = attrib.get("entry_uw") if isinstance(attrib.get("entry_uw"), dict) else {}
    adjs = entry_uw.get("v2_uw_adjustments") if isinstance(entry_uw.get("v2_uw_adjustments"), dict) else {}
    return adjs


def _replacement_reason(trade: Dict[str, Any]) -> str:
    # Prefer exit_attribution replacement_reasoning if present; otherwise shadow_exit reasoning.
    attrib = trade.get("exit_attribution") if isinstance(trade.get("exit_attribution"), dict) else {}
    rr = attrib.get("replacement_reasoning")
    if rr is None:
        rr = trade.get("replacement_reasoning")
    if isinstance(rr, dict):
        for k in ("cause", "reason", "close_reason", "exit_reason"):
            v = rr.get(k)
            if v:
                return str(v)
        # If dict but no known keys, provide stable tag
        return "reasoning_present_no_cause"
    if isinstance(rr, str) and rr.strip():
        return rr.strip()
    return "unknown"


def build_replacement_telemetry_expanded(*, day: str, realized_trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    denom_feat: Dict[str, int] = defaultdict(int)
    numer_feat: Dict[str, int] = defaultdict(int)
    denom_fam: Dict[str, int] = defaultdict(int)
    numer_fam: Dict[str, int] = defaultdict(int)

    reason_hist = Counter()
    total_trades = 0
    total_replacements = 0

    for t in realized_trades or []:
        if not isinstance(t, dict):
            continue
        total_trades += 1
        replaced = bool(t.get("replacement_candidate"))
        if replaced:
            total_replacements += 1
            reason_hist[_replacement_reason(t)] += 1

        adjs = _get_entry_adjustments(t)
        active_feats: List[str] = []
        if isinstance(adjs, dict):
            for k, v in adjs.items():
                if str(k) == "total":
                    continue
                if _absf(v) <= 1e-9:
                    continue
                active_feats.append(str(k))
        if not active_feats:
            denom_fam[FAMILY_UNKNOWN] += 1
            if replaced:
                numer_fam[FAMILY_UNKNOWN] += 1
        else:
            for fk in active_feats:
                denom_feat[fk] += 1
                fam = v2_family_for_key(fk)
                denom_fam[fam] += 1
                if replaced:
                    numer_feat[fk] += 1
                    numer_fam[fam] += 1

    # Ensure stable non-empty histogram
    if not reason_hist:
        reason_hist["unknown"] = 0

    per_feature: Dict[str, Any] = {}
    for fk in sorted(denom_feat.keys() | numer_feat.keys()):
        d = int(denom_feat.get(fk, 0))
        n = int(numer_feat.get(fk, 0))
        per_feature[fk] = {
            "denom": d,
            "numer": n,
            "replacement_rate": float(n / d) if d else 0.0,
        }

    per_family: Dict[str, Any] = {}
    for fam in sorted(denom_fam.keys() | numer_fam.keys()):
        d = int(denom_fam.get(fam, 0))
        n = int(numer_fam.get(fam, 0))
        per_family[fam] = {
            "denom": d,
            "numer": n,
            "replacement_rate": float(n / d) if d else 0.0,
        }

    overall_rate = float(total_replacements / total_trades) if total_trades else 0.0

    # Simple anomaly detector (telemetry-only heuristic)
    anomaly = False
    if total_replacements >= 3 and overall_rate > 0.25:
        anomaly = True
    for fk, row in per_feature.items():
        if int(row.get("denom", 0)) >= 5 and float(row.get("replacement_rate", 0.0)) > 0.5:
            anomaly = True
            break

    return {
        "_meta": {"date": str(day), "kind": "replacement_telemetry_expanded", "version": "2026-01-22_v1"},
        "counts": {
            "realized_trades": int(total_trades),
            "replacement_trades": int(total_replacements),
            "replacement_rate": float(overall_rate),
        },
        "per_feature_replacement_rate": per_feature,
        "per_family_replacement_rate": per_family,
        "replacement_cause_histogram": dict(reason_hist),
        "replacement_anomaly_detected": bool(anomaly),
        "notes": {
            "active_feature_definition": "abs(v2_uw_adjustments[feature])>0 (entry_uw, best-effort)",
            "anomaly_rule": "overall replacement_rate>0.25 with >=3 events OR any feature replacement_rate>0.5 with denom>=5",
        },
    }

