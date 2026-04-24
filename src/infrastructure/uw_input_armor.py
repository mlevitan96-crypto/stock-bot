"""
Unusual Whales → composite scorer boundary: coerce poisoned / missing scalar inputs.

Per MEMORY_BANK §7.1: invalid or blank API fields must not propagate as non-numeric types
or NaN strings into the composite. We normalize to finite floats (0.0) and bounded
sentinel strings before ``uw_composite_v2`` scoring.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

# Keys that must be numeric for stable composite math (Section 7.1 alignment).
_SCALAR_FLOAT_KEYS: Tuple[str, ...] = (
    "conviction",
    "flow_conv",
    "flow_conviction",
    "iv_term_skew",
    "smile_slope",
    "toxicity",
    "event_alignment",
    "freshness",
    "trade_count",
    "sector_alignment",
    "regime_alignment",
    "beta_vs_spy",
    "realized_vol_5d",
    "realized_vol_20d",
)


def _finite_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        x = float(v)
        return x if math.isfinite(x) else None
    s = str(v).strip()
    if not s or s.lower() in ("null", "none", "nan", "inf", "-inf"):
        return None
    try:
        x = float(s)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _coerce_scalar(k: str, v: Any) -> Tuple[Any, bool]:
    """Return (new_value, changed)."""
    if k not in _SCALAR_FLOAT_KEYS:
        return v, False
    if isinstance(v, dict) or isinstance(v, list):
        return 0.0, True
    fin = _finite_float(v)
    if fin is None:
        return 0.0, True
    return fin, fin != v


def _armor_dark_pool(dp: Any) -> Tuple[dict, bool]:
    if not isinstance(dp, dict):
        return {}, dp is not None
    out = dict(dp)
    changed = False
    for dk in ("total_notional_1h", "notional_1h", "total_notional", "total_premium"):
        if dk not in out:
            continue
        fin = _finite_float(out.get(dk))
        if fin is None:
            if out.get(dk) not in (None, "", [], {}):
                changed = True
            out[dk] = 0.0
        else:
            if out.get(dk) != fin:
                changed = True
            out[dk] = fin
    sent = out.get("sentiment")
    if sent is not None and str(sent).strip() == "":
        out["sentiment"] = "NEUTRAL"
        changed = True
    return out, changed


def armor_uw_enriched_row_for_composite(row: Optional[Dict[str, Any]], *, symbol: str = "") -> Dict[str, Any]:
    """
    Return a shallow copy of ``row`` with poisoned scalars replaced by safe defaults.
    Does not mutate the input dict.
    """
    if not isinstance(row, dict):
        return {}
    out: Dict[str, Any] = dict(row)
    any_change = False
    for k in _SCALAR_FLOAT_KEYS:
        if k not in out:
            continue
        nv, ch = _coerce_scalar(k, out[k])
        if ch:
            out[k] = nv
            any_change = True
    dp = out.get("dark_pool")
    dp2, dch = _armor_dark_pool(dp)
    if dch or dp2 != dp:
        out["dark_pool"] = dp2
        any_change = True
    sent = out.get("sentiment")
    if sent is not None:
        s = str(sent).strip()
        if not s or s.lower() in ("null", "none"):
            out["sentiment"] = "NEUTRAL"
            any_change = True
    if any_change:
        try:
            from utils.system_events import log_system_event

            log_system_event(
                subsystem="data_armor",
                event_type="uw_composite_input_coerced",
                severity="INFO",
                symbol=str(symbol or "").upper()[:16] or None,
                details={"note": "poisoned_or_blank_uw_fields_normalized"},
            )
        except Exception:
            pass
    return out
