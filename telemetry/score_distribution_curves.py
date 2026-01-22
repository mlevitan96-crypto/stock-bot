"""
Score distribution curves (telemetry-only)
=========================================

Produces histograms (counts by bin) for:
- v1 entry scores
- v2 entry scores
- score deltas (v2 - v1)

Split by feature family and long/short where available.

Contract:
- Read-only (pure function).
- Best-effort: empty inputs still produce non-empty histogram arrays (all zeros).
"""

from __future__ import annotations

from typing import Any, Dict, List

from telemetry.feature_families import FEATURE_FAMILIES, FAMILY_UNKNOWN


def _hist(values: List[float], *, start: float, end: float, step: float) -> Dict[str, Any]:
    # edges includes both endpoints; counts has len(edges)-1
    edges: List[float] = []
    x = float(start)
    while x <= float(end) + 1e-12:
        edges.append(round(x, 6))
        x += float(step)
    counts = [0 for _ in range(max(0, len(edges) - 1))]
    for v in values:
        try:
            fv = float(v)
        except Exception:
            continue
        if fv < edges[0]:
            # clamp into first bin
            idx = 0
        elif fv >= edges[-1]:
            idx = len(edges) - 2 if len(edges) >= 2 else 0
        else:
            idx = int((fv - edges[0]) / float(step))
            idx = max(0, min(len(counts) - 1, idx))
        if 0 <= idx < len(counts):
            counts[idx] += 1
    return {"edges": edges, "counts": counts, "n": int(len(values))}


def _side(r: Dict[str, Any]) -> str:
    s = str((r.get("v1_side") or r.get("v2_side") or "")).lower()
    if s in ("long", "short"):
        return s
    return "unknown"


def build_score_distribution_curves(*, day: str, entry_parity_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Group rows by family and side.
    fams = {f: {"overall": [], "long": [], "short": []} for f in FEATURE_FAMILIES}
    if FAMILY_UNKNOWN not in fams:
        fams[FAMILY_UNKNOWN] = {"overall": [], "long": [], "short": []}

    for r in entry_parity_rows or []:
        if not isinstance(r, dict):
            continue
        fam = str(r.get("feature_family") or FAMILY_UNKNOWN)
        if fam not in fams:
            fam = FAMILY_UNKNOWN
        side = _side(r)
        fams[fam]["overall"].append(r)
        if side in ("long", "short"):
            fams[fam][side].append(r)

    out: Dict[str, Any] = {"_meta": {"date": str(day), "kind": "score_distribution_curves", "version": "2026-01-22_v1"}}
    families_out: Dict[str, Any] = {}
    for fam, groups in fams.items():
        fam_block: Dict[str, Any] = {}
        for grp_name, rows in groups.items():
            v1_scores = [float((rr.get("v1_score_at_entry") or 0.0)) for rr in rows]
            v2_scores = [float((rr.get("v2_score_at_entry") or 0.0)) for rr in rows]
            deltas = [float((rr.get("score_delta") or 0.0)) for rr in rows]
            fam_block[grp_name] = {
                "v1_score_hist": _hist(v1_scores, start=0.0, end=8.0, step=0.25),
                "v2_score_hist": _hist(v2_scores, start=0.0, end=8.0, step=0.25),
                "score_delta_hist": _hist(deltas, start=-4.0, end=4.0, step=0.25),
            }
        families_out[fam] = fam_block

    out["families"] = families_out
    out["notes"] = {"source": "entry_parity_details (from v1 attribution + v2 shadow_entry_opened) grouped by feature_family"}
    return out

