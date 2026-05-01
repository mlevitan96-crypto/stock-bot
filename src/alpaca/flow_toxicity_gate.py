"""
VPIN-style toxicity proxy from L1 OFI telemetry (``ofi_l1_roll_*``).

True VPIN buckets volume imbalance; here we use **rolling signed OFI sums** already emitted
in entry snapshots / ML rows as a cheap order-flow intensity signal: short-window magnitude vs
a longer baseline (spike ratio). High ratio ⇒ treat as **toxic / informed-flow pressure** for
entry gating (Chen / Ghost lens).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_RISK = _REPO / "config" / "alpaca_risk_profile.json"


def load_vpin_ofi_gate_config(path: Optional[Path] = None) -> Dict[str, Any]:
    p = path or _DEFAULT_RISK
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    cfg = raw.get("vpin_ofi_gate")
    return cfg if isinstance(cfg, dict) else {}


def ofi_l1_spike_ratio(row: Mapping[str, Any]) -> Optional[float]:
    """
    ``|OFI_60s| / max(floor, |OFI_300s|)`` when both finite; else None.
    """
    try:
        s60 = float(row.get("ofi_l1_roll_60s_sum", float("nan")))
        s300 = float(row.get("ofi_l1_roll_300s_sum", float("nan")))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(s60) or not math.isfinite(s300):
        return None
    return float(abs(s60) / max(1e-12, abs(s300)))


def entry_blocked_by_vpin_ofi(
    row: Mapping[str, Any],
    *,
    cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Optional[float]]:
    """
    Returns (blocked, reason_code, spike_ratio_or_none).

    When OFI fields are missing or non-finite: ``fail_open`` (default) does not block;
    ``fail_closed`` blocks with ``vpin_ofi_missing``.
    """
    c = cfg if cfg is not None else load_vpin_ofi_gate_config()
    if not c.get("enabled", True):
        return False, "vpin_ofi_disabled", None
    fail_open = str(c.get("failure_mode", "fail_open")).strip().lower() in (
        "fail_open",
        "open",
        "1",
        "true",
        "yes",
    )
    ratio_max = float(c.get("toxic_spike_ratio_max", 5.0))
    denom_floor = float(c.get("abs_ofi_300_floor", 500.0))

    has_60 = "ofi_l1_roll_60s_sum" in row
    has_300 = "ofi_l1_roll_300s_sum" in row
    if not has_60 or not has_300:
        if fail_open:
            return False, "vpin_ofi_missing_fields_fail_open", None
        return True, "vpin_ofi_missing_fields_fail_closed", None

    try:
        s60 = float(row.get("ofi_l1_roll_60s_sum", float("nan")))
        s300 = float(row.get("ofi_l1_roll_300s_sum", float("nan")))
    except (TypeError, ValueError):
        if fail_open:
            return False, "vpin_ofi_non_numeric_fail_open", None
        return True, "vpin_ofi_non_numeric_fail_closed", None

    if not math.isfinite(s60) or not math.isfinite(s300):
        if fail_open:
            return False, "vpin_ofi_non_finite_fail_open", None
        return True, "vpin_ofi_non_finite_fail_closed", None

    den = max(denom_floor, abs(s300), 1e-12)
    spike = abs(s60) / den
    if spike > ratio_max:
        return True, "vpin_ofi_toxicity_veto", float(spike)
    return False, "vpin_ofi_pass", float(spike)


def env_vpin_gate_overrides_enabled() -> bool:
    return str(os.environ.get("VPIN_OFI_GATE_ENABLED", "1")).strip().lower() in ("1", "true", "yes", "on")
