"""
Attribution schema contract validation.
Ensures: total_score == sum(contributions), required snapshots exist, exit_reason_code present.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

EPS = 1e-6


def _sum_contributions(components: List[Dict[str, Any]]) -> float:
    """Recursively sum contribution_to_score from components and sub_components."""
    total = 0.0
    for c in components or []:
        if isinstance(c, dict):
            total += float(c.get("contribution_to_score") or 0.0)
            sub = c.get("sub_components") or []
            if sub:
                total += _sum_contributions(sub)
    return total


def validate_snapshot_score(snapshot: Dict[str, Any], tolerance: float = EPS) -> Tuple[bool, str]:
    """
    Validate total_score == sum(component contributions).
    Returns (ok, error_message).
    """
    total = float(snapshot.get("total_score") or 0.0)
    components = snapshot.get("components") or []
    summed = _sum_contributions(components)
    if abs(total - summed) > tolerance:
        return False, f"total_score={total} != sum(contributions)={summed}"
    return True, ""


def validate_trade_attribution(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate TradeAttributionRecord: entry and exit snapshots present, exit_reason_code set.
    Returns (ok, list of errors).
    """
    errors: List[str] = []
    if not record.get("trade_id"):
        errors.append("missing trade_id")
    if not record.get("symbol"):
        errors.append("missing symbol")
    entry = record.get("entry_snapshot")
    exit_snap = record.get("exit_snapshot")
    if not entry and not exit_snap:
        errors.append("missing both entry_snapshot and exit_snapshot")
    if exit_snap and not record.get("exit_reason_code"):
        errors.append("exit_snapshot present but exit_reason_code missing")
    if entry:
        ok, msg = validate_snapshot_score(entry)
        if not ok:
            errors.append(f"entry_snapshot: {msg}")
    if exit_snap:
        ok, msg = validate_snapshot_score(exit_snap)
        if not ok:
            errors.append(f"exit_snapshot: {msg}")
    return len(errors) == 0, errors
