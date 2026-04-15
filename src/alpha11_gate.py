"""
Alpha 11 flow-strength floor (Quant cohort: strict 163 audit).

Blocks discretionary entries when persisted UW ``flow_strength`` (or ``conviction``)
is below the Quant floor. Missing / non-finite telemetry skips the gate (allow) with
an INFO log so we do not brick entries on partial UW payloads.

Configure:
  ALPHA11_FLOW_GATE_ENABLED    default 1  (set 0 to disable)
  ALPHA11_MIN_FLOW_STRENGTH    default 0.985 (Quant strict-cohort winner mean floor)
"""

from __future__ import annotations

import math
import os
from typing import Any, Dict, Mapping, Optional, Tuple


def _truthy_env(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _min_flow_strength() -> float:
    """Quant hard floor; override only via ALPHA11_MIN_FLOW_STRENGTH."""
    raw = os.environ.get("ALPHA11_MIN_FLOW_STRENGTH", "0.985").strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.985
    return v


def _flow_strength_from_uw(uw: Any) -> Optional[float]:
    if not isinstance(uw, dict):
        return None
    for k in ("flow_strength", "conviction"):
        v = uw.get(k)
        if v is None:
            continue
        try:
            f = float(v)
            if math.isfinite(f):
                return f
        except (TypeError, ValueError):
            continue
    return None


def _extract_flow_strength(
    composite_result: Optional[Mapping[str, Any]],
    composite_meta: Optional[Mapping[str, Any]],
) -> Optional[float]:
    for src in (composite_result, composite_meta):
        if not isinstance(src, dict):
            continue
        uw = src.get("v2_uw_inputs")
        fs = _flow_strength_from_uw(uw)
        if fs is not None:
            return fs
    return None


def check_alpha11_flow_strength_gate(
    *,
    symbol: str,
    composite_result: Optional[Mapping[str, Any]],
    composite_meta: Optional[Mapping[str, Any]],
) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Returns (allowed, block_reason_or_none, flow_strength_or_none).

    Disabled → allow. Missing flow → allow with reason ``alpha11_flow_skipped``.
    Below floor → block ``alpha11_flow_strength_below_gate``.
    """
    if not _truthy_env("ALPHA11_FLOW_GATE_ENABLED", "1"):
        return True, None, None

    fs = _extract_flow_strength(composite_result, composite_meta)
    if fs is None:
        return True, "alpha11_flow_skipped_missing_flow_strength", None

    floor = _min_flow_strength()
    if fs < floor:
        return False, "alpha11_flow_strength_below_gate", fs
    return True, None, fs
